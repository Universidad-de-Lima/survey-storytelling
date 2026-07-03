"""
SURVEY ETL NLP — Módulo de procesamiento de lenguaje natural y tópicos semánticos por IA local.

Clasifica comentarios de encuestas libres (pasivos, detractores y promotores)
usando embeddings multilingües locales y cálculo de similitud de coseno
frente a anclas vectoriales de sentimiento y tópicos, con costo cero y sin APIs de pago.
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    class SentenceTransformer:
        def __init__(self, *args, **kwargs): pass
        def encode(self, texts, **kwargs): return np.zeros((len(texts), 384))


# Diccionario de modismos y abreviaciones comunes
ABREVIACIONES = {
    r"\bprofe\b": "docente",
    r"\bprofes\b": "docentes",
    r"\b(la|en la|de la|a la)\s+u\b": r"\1 universidad",
    r"\bwifi\b": "Wi-Fi",
    r"\bwi-fi\b": "Wi-Fi",
    r"\bfacu\b": "facultad",
    r"\bblackboard\b": "Blackboard",
    r"\bzoom\b": "Zoom",
}

def normalizar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto en español para facilitar el matching y embeddings.
    Conserva tildes, diacríticos y la letra ñ para no dañar la precisión del modelo multilingüe.
    """
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = texto.lower().strip()
    # Remover puntuación y caracteres especiales no alfanuméricos en español, conservando letras con tilde y ñ
    texto = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def corregir_slang(texto: str) -> str:
    """
    Reemplaza modismos, jergas y abreviaturas comunes para mejorar la legibilidad en la UI.
    """
    if not isinstance(texto, str):
        return ""
    # Capitalizar inicial
    t = texto.strip()
    if not t:
        return ""
    t = t[0].upper() + t[1:]
    
    # Reemplazar abreviaciones usando expresiones regulares insensibles a mayúsculas
    for pattern, replacement in ABREVIACIONES.items():
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)
    
    # Asegurar puntuación final
    if not t.endswith((".", "!", "?")):
        t += "."
    return t

def enmascarar_pii(texto: str) -> str:
    """
    Detecta y enmascara información de identificación personal (PII) en el texto
    tales como correos electrónicos, números telefónicos y códigos estudiantiles.
    """
    if not isinstance(texto, str) or not texto.strip():
        return ""
    
    # 1. Enmascarar correos electrónicos
    patron_correo = r"[\w\.-]+@[\w\.-]+\.\w+"
    t = re.sub(patron_correo, "[CORREO ENMASCARADO]", texto)
    
    # 2. Enmascarar números telefónicos (Perú, 9 dígitos con o sin prefijo +51 y espacios/guiones)
    patron_telefono = r"\b(?:\+?51\s*)?9\d{2}[-\s]?\d{3}[-\s]?\d{3}\b"
    t = re.sub(patron_telefono, "[TELÉFONO ENMASCARADO]", t)
    
    # 3. Enmascarar códigos de estudiante de 8 dígitos (típicamente inician con 20 o 19)
    patron_codigo = r"\b(?:20|19)\d{6}\b"
    t = re.sub(patron_codigo, "[CÓDIGO ENMASCARADO]", t)
    
    return t

def sanitizar_comentario(texto: str) -> Tuple[bool, Optional[str]]:
    """
    Evalúa la calidad del comentario.
    Retorna (es_valido, motivo_invalidez)
    """
    if not isinstance(texto, str) or not texto.strip():
        return False, "mensaje_vacio"
    
    txt_clean = texto.strip()
    if len(txt_clean) <= 3:
        return False, "mensaje_demasiado_corto"
    
    # Detectar spam de letras repetidas exageradas (ej: "aaaaaaaa", "xxxxxxx")
    if re.search(r"(.)\1{4,}", txt_clean.lower()):
        return False, "spam_o_ruido"
    
    # Expresiones de descarte comunes que no aportan valor semántico
    noise_patterns = [
        r"^ninguno$", r"^ninguna$", r"^nada$", r"^todo ok$", r"^todo bien$", r"^ninguno\.$",
        r"^no$", r"^si$", r"^ningun comentario$", r"^ningun comentario\.$", r"^ninguno por el momento$"
    ]
    for pattern in noise_patterns:
        if re.match(pattern, txt_clean.lower().strip()):
            return False, "sin_opinion_valida"
            
    return True, None

def segmentar_comentario(texto: str) -> List[str]:
    """
    Divide un comentario en fragmentos semánticamente autónomos utilizando
    signos de puntuación (. ; :), saltos de línea y conectores adversativos.
    Excluye comas (,).
    """
    if not isinstance(texto, str) or not texto.strip():
        return []

    # 1. Dividir por signos de puntuación (. ; :) y saltos de línea (\n \r) e interrogación/exclamación (? !)
    sentencias = re.split(r"[\n\r.:;!?]+", texto)
    sentencias = [s.strip() for s in sentencias if s.strip()]

    # 2. Dividir por conectores adversativos con límites de palabra (\b)
    # conectores: pero, sin embargo, aunque, no obstante, en cambio
    patron_conectores = r"\b(?:pero|sin\s+embargo|aunque|no\s+obstante|en\s+cambio)\b"
    fragmentos = []
    for s in sentencias:
        sub_frags = re.split(patron_conectores, s, flags=re.IGNORECASE)
        for sf in sub_frags:
            clean_sf = sf.strip()
            if clean_sf:
                fragmentos.append(clean_sf)

    # 3. Filtrar y sanitizar cada fragmento
    fragmentos_validos = []
    for f in fragmentos:
        es_valido, _ = sanitizar_comentario(f)
        if es_valido:
            fragmentos_validos.append(f)

    return fragmentos_validos

# Caché global para el modelo SentenceTransformer (Singleton Pattern)
_MODEL_INSTANCE = None

def obtener_modelo() -> SentenceTransformer:
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        # paraphrase-multilingual-MiniLM-L12-v2 es ligero (~118MB) y rápido en CPU
        _MODEL_INSTANCE = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _MODEL_INSTANCE
