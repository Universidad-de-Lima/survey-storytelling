import spacy
import re
import numpy as np
from typing import Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from .nlp import obtener_modelo
import json
import os
from .config import CATEGORIA_DIMENSION_PREGRADO, CATEGORIA_DIMENSION_POSGRADO

# Cargar stop aspectos
_STOP_ASPECTOS = set()
_config_path = os.path.join(os.path.dirname(__file__), "..", "config", "stop_aspectos.json")
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _STOP_ASPECTOS = set(json.load(f))
except Exception:
    _STOP_ASPECTOS = {"falta", "cosa", "cosas", "problema", "problemas", "mejora", "mejoras"}

# Cargar spacy
try:
    nlp_spacy = spacy.load("es_core_news_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("es_core_news_sm")
    nlp_spacy = spacy.load("es_core_news_sm")

# 1. Unificar dimensiones oficiales desde config
CATEGORIA_PADRE_MAP = {}
CATEGORIA_PADRE_MAP.update(CATEGORIA_DIMENSION_PREGRADO)
CATEGORIA_PADRE_MAP.update(CATEGORIA_DIMENSION_POSGRADO)
CATEGORIA_PADRE_MAP["Pendiente de Clasificación"] = "Pendiente de Clasificación"

# 2. Diccionario interno de alias muy comunes para atajo rápido (Fase 1)
ALIAS_DICT_MANUAL = {
    "Aulas de clase": ["aula", "aulas", "salon", "salones", "carpeta", "carpetas", "silla", "sillas", "comodidad", "mobiliario", "pizarra", "pizarras"],
    "Ambientes y salas para estudio": ["espacio de estudio", "espacios de estudio", "cubiculo", "cubiculos", "biblioteca", "mesas", "mesas libres"],
    "Calidad de la enseñanza en la carrera": ["profesor", "profesores", "docente", "docentes", "profe", "profes", "enseñanza", "pedagogia", "trato", "explicacion", "metodologia"],
    "Evaluación del aprendizaje": ["examen", "examenes", "evaluacion", "evaluaciones", "practica", "practicas", "nota", "notas", "calificacion", "exigencia"],
    "Plan curricular y perfil de egreso": ["malla", "curricula", "curso", "cursos", "electivo", "electivos", "plan de estudios", "temas", "silabo"],
    "Habilidades para trabajar en equipo": ["trabajo grupal", "trabajos grupales", "grupo", "grupos", "equipo", "compañeros", "compañero"],
    "Portal web de la Universidad (Mi Ulima)": ["miulima", "portal", "sistema"],
    "Aula virtual": ["blackboard", "correo", "zoom", "intranet"],
    "Conexión Wi-Fi en el campus": ["wifi", "wi-fi", "internet", "red", "señal", "conexion", "conectividad"],
    "Procedimientos administrativos": ["matricula", "inscripcion", "cupo", "cupos", "turno", "turnos", "sistema de matricula", "tramites"],
    "Equipamiento tecnológico en laboratorios": ["laboratorio", "laboratorios", "pc", "pcs", "computadora", "computadoras", "mac", "macs", "impresora", "impresoras"]
}

# Solo registramos alias exactos para las dimensiones que sí existen en la config actual
EXACT_MATCH_ITEMS = []
for bucket, aliases in ALIAS_DICT_MANUAL.items():
    if bucket in CATEGORIA_PADRE_MAP:
        for alias in aliases:
            EXACT_MATCH_ITEMS.append((alias.lower(), bucket))

EXACT_MATCH_ITEMS.sort(key=lambda x: len(x[0]), reverse=True)
EXACT_MATCH = dict(EXACT_MATCH_ITEMS)

# 3. Anclas Semánticas para Fallback Vectorial
# Se generan dinámicamente: el anchor es el nombre de la dimensión + sus alias manuales
SEMANTIC_ANCHORS = {}
for dimension in CATEGORIA_PADRE_MAP.keys():
    if dimension == "Pendiente de Clasificación":
        continue
    anchor_words = [dimension.lower()]
    if dimension in ALIAS_DICT_MANUAL:
        anchor_words.extend(ALIAS_DICT_MANUAL[dimension])
    
    SEMANTIC_ANCHORS[dimension] = " ".join(anchor_words)

_ANCHORS_EMBEDDINGS = None
_ANCHORS_KEYS = None

def _inicializar_embeddings():
    global _ANCHORS_EMBEDDINGS, _ANCHORS_KEYS
    if _ANCHORS_EMBEDDINGS is None:
        model = obtener_modelo()
        _ANCHORS_KEYS = list(SEMANTIC_ANCHORS.keys())
        _ANCHORS_EMBEDDINGS = model.encode(list(SEMANTIC_ANCHORS.values()))

def extraer_aspecto_detectado(opinion_unit: str) -> Tuple[str, list]:
    """Extrae el aspecto literal usando SpaCy Noun Chunks o raiz. Retorna (aspecto, sub_aspectos)."""
    if not opinion_unit or not opinion_unit.strip():
        return "", []
    
    doc = nlp_spacy(opinion_unit)
    candidatos = []
    sub_aspectos = []
    
    # Recopilar todos los sustantivos válidos para sub_aspectos
    for token in doc:
        if token.pos_ in ('NOUN', 'PROPN'):
            t_low = token.text.lower()
            t_lem = token.lemma_.lower()
            if t_low not in _STOP_ASPECTOS and t_lem not in _STOP_ASPECTOS:
                sub_aspectos.append(t_low)
                
    # Regla 1: Buscar Noun Chunks
    chunks = list(doc.noun_chunks)
    if chunks:
        # Priorizar el chunk que contiene la raiz (ROOT), el sujeto (nsubj), u objeto directo (obj)
        for chunk in chunks:
            if chunk.root.dep_ in ('nsubj', 'obj', 'ROOT', 'nsubj:pass'):
                root_lemma = chunk.root.lemma_.lower()
                root_text = chunk.root.text.lower()
                
                if root_lemma in _STOP_ASPECTOS or root_text in _STOP_ASPECTOS:
                    # Buscar hijos modificadores (nmod, obl, pobj, compound)
                    mods = [child for child in chunk.root.children if child.dep_ in ('nmod', 'obl', 'pobj', 'compound')]
                    if mods:
                        mod_words = [t.text.lower() for t in mods[0].subtree if t.pos_ not in ('DET', 'PRON', 'ADP')]
                        if mod_words:
                            candidatos.append(" ".join(mod_words))
                            continue
                    continue
                
                # Limpiar determinantes ('el', 'la', 'los', 'las', 'un', 'una')
                words = [token.text for token in chunk if token.pos_ not in ('DET', 'PRON')]
                if words:
                    candidatos.append(" ".join(words).lower())
                    
        if not candidatos:
            # Si ninguno cumple, tomar el primer chunk que no sea stop word
            for chunk in chunks:
                root_lemma = chunk.root.lemma_.lower()
                root_text = chunk.root.text.lower()
                if root_lemma not in _STOP_ASPECTOS and root_text not in _STOP_ASPECTOS:
                    words = [token.text for token in chunk if token.pos_ not in ('DET', 'PRON')]
                    if words:
                        candidatos.append(" ".join(words).lower())
                        break
                        
    if candidatos:
        return candidatos[0], sub_aspectos

    # Regla 2: Fallback manual (buscar el primer sustantivo)
    nouns = [token for token in doc if token.pos_ == 'NOUN']
    for token in nouns:
        t_low = token.text.lower()
        t_lem = token.lemma_.lower()
        if t_low not in _STOP_ASPECTOS and t_lem not in _STOP_ASPECTOS:
            # Buscar modificadores adjetivales o compuestos para bloques completos (ej: aire acondicionado)
            mods = [child.text.lower() for child in token.children if child.dep_ in ('amod', 'compound')]
            if mods:
                return f"{t_low} {' '.join(mods)}", sub_aspectos
            return t_low, sub_aspectos

    # Regla 3: Si no hay sustantivo, devolver verbo/adjetivo raiz
    for token in doc:
        if token.dep_ == 'ROOT' and token.pos_ in ('VERB', 'ADJ'):
            return token.lemma_.lower(), sub_aspectos
            
    # Si todo falla, devolver la oracion completa normalizada
    return opinion_unit.lower(), sub_aspectos

def normalizar_aspecto(aspecto_detectado: str) -> Tuple[str, str, str]:
    """Retorna (Aspecto Normalizado, Categoria Padre, Metodo_Usado)"""
    if not aspecto_detectado:
        return "Pendiente de Clasificación", "Pendiente de Clasificación", "ninguno"
        
    aspecto_clean = re.sub(r'[^a-záéíóúñ\s-]', '', aspecto_detectado.lower()).strip()
    
    # 1. Exact Match (Diccionario Alias)
    for alias, bucket in EXACT_MATCH.items():
        if re.search(rf"\b{re.escape(alias)}\b", aspecto_clean):
            return bucket, CATEGORIA_PADRE_MAP[bucket], "alias"

    # Si es exactamente igual (por si el regex falla por algun caso)
    if aspecto_clean in EXACT_MATCH:
        bucket = EXACT_MATCH[aspecto_clean]
        return bucket, CATEGORIA_PADRE_MAP[bucket], "alias"

    # 2. Semantic Matching Vectorial
    _inicializar_embeddings()
    model = obtener_modelo()
    emb = model.encode([aspecto_clean])
    sim = cosine_similarity(emb, _ANCHORS_EMBEDDINGS)[0]
    
    max_idx = np.argmax(sim)
    max_score = sim[max_idx]
    
    # Umbral estricto para evitar falsos positivos
    if max_score > 0.65:
        bucket = _ANCHORS_KEYS[max_idx]
        return bucket, CATEGORIA_PADRE_MAP[bucket], "embedding"
        
    # 3. Fallback
    return "Pendiente de Clasificación", "Pendiente de Clasificación", "fallback"

def procesar_opinion_unit(texto: str) -> Dict[str, str]:
    """Flujo completo para una opinion unit."""
    aspecto_detectado, sub_aspectos = extraer_aspecto_detectado(texto)
    aspecto_normalizado, categoria_padre, metodo = normalizar_aspecto(aspecto_detectado)
    
    return {
        "aspecto_detectado": aspecto_detectado,
        "aspecto_normalizado": aspecto_normalizado,
        "categoria_padre": categoria_padre,
        "sub_aspectos": sub_aspectos,
        "metodo": metodo
    }
