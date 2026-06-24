"""
SURVEY ETL NLP — Módulo de procesamiento de lenguaje natural y tópicos semánticos por IA local.

Clasifica comentarios de encuestas libres (pasivos, detractores y promotores)
usando embeddings multilingües locales y cálculo de similitud de coseno
frente a anclas vectoriales de sentimiento y tópicos, con costo cero y sin APIs de pago.
"""

import re
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    class SentenceTransformer:
        def __init__(self, *args, **kwargs): pass
        def encode(self, texts, **kwargs): return np.zeros((len(texts), 384))
from sklearn.metrics.pairwise import cosine_similarity
from .config import STOPWORDS

# ── 1. Anclas Semánticas para Sentimiento ──
ANCHORS_SENTIMENT = {
    "positivo": "excelente bueno contento satisfecho recomendado gran calidad muy buena enseñanza todo muy bien felicitaciones me gusta",
    "negativo": "malo pésimo insatisfecho disconforme queja mala atención desactualizado lento demora mal servicio pésima metodología no me gusta"
}

# ── 2. Anclas Semánticas para Tópicos ──
ANCHORS_TOPICS = {
    "Calidad docente": "profesores docentes enseñanza clases metodologías didáctica explicaciones dictado de cursos docentes de carrera",
    "Malla curricular y cursos": "malla curricular materias cursos plan de estudios asignaturas temas de relleno electivos plan curricular",
    "Infraestructura y espacios": "infraestructura campus aulas laboratorios biblioteca edificios salones de clase pabellones áreas comunes",
    "Servicios administrativos": "trámites secretaría atención administrativa horarios procesos de matrícula récord académico demora burocracia",
    "Tecnología y plataformas": "wifi internet blackboard zoom portal mi ulima herramientas virtuales conexión a internet sistemas",
    "Oportunidades laborales": "empleabilidad bolsa de trabajo prácticas preprofesionales egresados convenios empleo egreso profesional",
    "Bienestar y servicios al estudiante": "servicio médico psicología talleres actividades extracurriculares deporte arte música becas ayuda financiera",
    "Valoración positiva general": "excelente calidad prestigio recomendado gran universidad buen servicio orgullo institucional me gusta"
}

# ── 3. Categorías Padre (Estructura de Negocio) ──
CATEGORIAS_PADRES = {
    "Calidad docente": "Académico",
    "Malla curricular y cursos": "Académico",
    "Infraestructura y espacios": "Infraestructura",
    "Servicios administrativos": "Administrativo y Bienestar",
    "Tecnología y plataformas": "Infraestructura",
    "Oportunidades laborales": "Administrativo y Bienestar",
    "Bienestar y servicios al estudiante": "Administrativo y Bienestar",
    "Valoración positiva general": "Valoración General",
    "Otros": "Otros"
}

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

def agrupar_comentarios_por_topico(df_comentarios: pd.DataFrame) -> Tuple[List[Dict[str, any]], List[Dict[str, any]]]:
    """
    [DEPRECATED — v3.0] Esta función NO se invoca desde build_json.py desde la migración
    al motor cualitativo moderno (lib/aspect_extraction.py + lib/sentiment_engine.py).
    Se conserva como referencia histórica del pipeline anterior basado en TOPICOS/STOPWORDS.
    No usar en código nuevo; usar procesar_opinion_unit + analizar_sentimiento_intensidad.

    Toma un DataFrame con columnas [comentario, nps_score, carrera, facultad, ciclo]
    y realiza la clasificación semántica local (sentimiento y tópicos).
    Retorna (topicos_resultado, comentarios_detallados).
    """
    # 1. Obtener el modelo SentenceTransformer desde el caché global
    model = obtener_modelo()

    # Precalcular embeddings de las anclas de sentimiento
    sent_labels = list(ANCHORS_SENTIMENT.keys())
    sent_embeddings = model.encode(list(ANCHORS_SENTIMENT.values()))

    # Precalcular embeddings de las anclas de tópicos
    topic_labels = list(ANCHORS_TOPICS.keys())
    topic_embeddings = model.encode(list(ANCHORS_TOPICS.values()))

    comentarios_detallados: List[Dict[str, any]] = []
    topicos_con_embeddings: Dict[str, List[np.ndarray]] = {t: [] for t in topic_labels}
    topicos_con_comentarios: Dict[str, List[Dict[str, any]]] = {t: [] for t in topic_labels}
    topicos_con_comentarios["Otros"] = []
    topicos_con_embeddings["Otros"] = []

    registros_validos: List[Dict[str, any]] = []
    textos_a_codificar: List[str] = []

    # Pasada 1: Clasificación de calidad, enmascaramiento de PII, fragmentación semántica y filtro de válidos
    for idx, row in df_comentarios.iterrows():
        orig_text = str(row["comentario"])
        # Enmascarar información personal (PII) de inmediato antes de cualquier procesamiento
        orig_text = enmascarar_pii(orig_text)
        
        es_valido, motivo = sanitizar_comentario(orig_text)
        
        # Mapear datos
        nps = int(row["nps_score"])
        carrera = str(row["carrera"])
        facultad = str(row["facultad"])
        ciclo = str(row["ciclo"])
        
        # Asignar id único si no existe
        res_id = str(row.get("ID", f"R_{idx}"))

        if not es_valido:
            # Comentario inválido: guardar en detalle para la UI
            comentarios_detallados.append({
                "id": res_id,
                "carrera": carrera,
                "facultad": facultad,
                "ciclo": ciclo,
                "nps_score": nps,
                "sentimiento": "neutro",
                "intensidad": 0.0,
                "categoria": "Otros",
                "categoria_padre": "Otros",
                "fragmento_original": orig_text,
                "fragmento_mostrar": orig_text,
                "es_valido": False,
                "motivo_invalidez": motivo,
                "comentario_original": orig_text,
                "comentario_id_original": res_id,
                "fragmento_secuencia": 0,
                "es_fragmento": False
            })
        else:
            # Segmentación semántica (Fase 2B)
            fragmentos = segmentar_comentario(orig_text)
            if not fragmentos:
                # Si la segmentación no produce fragmentos válidos, se mapea como comentario inválido
                comentarios_detallados.append({
                    "id": res_id,
                    "carrera": carrera,
                    "facultad": facultad,
                    "ciclo": ciclo,
                    "nps_score": nps,
                    "sentimiento": "neutro",
                    "intensidad": 0.0,
                    "categoria": "Otros",
                    "categoria_padre": "Otros",
                    "fragmento_original": orig_text,
                    "fragmento_mostrar": orig_text,
                    "es_valido": False,
                    "motivo_invalidez": "sin_opinion_valida",
                    "comentario_original": orig_text,
                    "comentario_id_original": res_id,
                    "fragmento_secuencia": 0,
                    "es_fragmento": False
                })
            else:
                es_frag = len(fragmentos) > 1
                for f_idx, frag in enumerate(fragmentos):
                    # Cada fragmento pasa de nuevo por las validaciones y normalizaciones
                    es_val_frag, _ = sanitizar_comentario(frag)
                    if not es_val_frag:
                        continue
                    
                    clean_text = corregir_slang(frag)
                    norm_txt = normalizar_texto(frag)
                    
                    textos_a_codificar.append(norm_txt)
                    registros_validos.append({
                        "id": f"{res_id}_p{f_idx + 1}" if es_frag else res_id,
                        "carrera": carrera,
                        "facultad": facultad,
                        "ciclo": ciclo,
                        "nps_score": nps,
                        "fragmento_original": frag,
                        "fragmento_mostrar": clean_text,
                        "comentario_original": orig_text,
                        "comentario_id_original": res_id,
                        "fragmento_secuencia": f_idx + 1 if es_frag else 0,
                        "es_fragmento": es_frag
                    })

    # Inferencia por lotes sobre todos los comentarios válidos
    if textos_a_codificar:
        embeddings_validos = model.encode(textos_a_codificar, batch_size=32)
        
        # Pasada 2: Procesar similitudes sobre embeddings precalculados en lote
        for val_idx, reg in enumerate(registros_validos):
            # Obtener el vector del comentario y asegurar forma 2D para similitud
            emb = embeddings_validos[val_idx].reshape(1, -1)
            
            # 1. Similitud de Sentimiento
            sim_sent = cosine_similarity(emb, sent_embeddings)[0]
            sim_pos, sim_neg = sim_sent[0], sim_sent[1]
            
            # Regla de calibración matemática (anclas vectoriales) - v3.0.3 (Sensible)
            diff = sim_pos - sim_neg
            if abs(diff) < 0.12 or (sim_pos < 0.25 and sim_neg < 0.25):
                sentiment = "neutro"
                intensity = 0.5
            else:
                if diff > 0:
                    sentiment = "positivo"
                    intensity = float(sim_pos)
                else:
                    sentiment = "negativo"
                    intensity = float(sim_neg)

            # 2. Similitud de Tópico
            sim_topic = cosine_similarity(emb, topic_embeddings)[0]
            idx_topic = np.argmax(sim_topic)
            score_topic = sim_topic[idx_topic]

            if score_topic < 0.38:
                topic_assigned = "Otros"
            else:
                topic_assigned = topic_labels[idx_topic]

            parent_cat = CATEGORIAS_PADRES[topic_assigned]

            comment_obj = {
                "id": reg["id"],
                "carrera": reg["carrera"],
                "facultad": reg["facultad"],
                "ciclo": reg["ciclo"],
                "nps_score": reg["nps_score"],
                "sentimiento": sentiment,
                "intensidad": round(intensity, 3),
                "categoria": topic_assigned,
                "categoria_padre": parent_cat,
                "fragmento_original": reg["fragmento_original"],
                "fragmento_mostrar": reg["fragmento_mostrar"],
                "es_valido": True,
                "comentario_original": reg["comentario_original"],
                "comentario_id_original": reg["comentario_id_original"],
                "fragmento_secuencia": reg["fragmento_secuencia"],
                "es_fragmento": reg["es_fragmento"]
            }
            comentarios_detallados.append(comment_obj)

            # Agrupar para cálculo de centroides y agregados
            topicos_con_embeddings[topic_assigned].append(emb[0])
            topicos_con_comentarios[topic_assigned].append(comment_obj)

    # Ordenar comentarios_detallados para preservar la secuencia original del dataframe
    id_posiciones = {str(row.get("ID", f"R_{idx}")): idx for idx, row in df_comentarios.iterrows()}
    comentarios_detallados.sort(
        key=lambda x: (
            id_posiciones.get(x["comentario_id_original"], 99999),
            x.get("fragmento_secuencia", 0)
        )
    )

    # 3. Compilar tópicos agregados y seleccionar frases representativas
    topicos_resultado: List[Dict[str, any]] = []

    # Configuración de iconos para tópicos dinámicos
    iconos = {
        "Calidad docente": "📚",
        "Malla curricular y cursos": "📋",
        "Infraestructura y espacios": "🏛️",
        "Servicios administrativos": "⚙️",
        "Tecnología y plataformas": "💻",
        "Oportunidades laborales": "💼",
        "Bienestar y servicios al estudiante": "🌱",
        "Valoración positiva general": "✅",
        "Otros": "💬"
    }

    for t_name, comm_list in topicos_con_comentarios.items():
        if t_name == "Otros" and not comm_list:
            continue
        
        total_comm = len(comm_list)
        if total_comm == 0:
            continue

        # Seleccionar frases representativas mediante centroide (distancia coseno)
        embeddings_list = topicos_con_embeddings[t_name]
        centroide = np.mean(embeddings_list, axis=0)
        
        # Calcular similitud al centroide para cada comentario
        similaridades = cosine_similarity([centroide], embeddings_list)[0]
        
        # Emparejar comentarios con sus scores de similitud al centroide
        sorted_comments = sorted(
            zip(comm_list, similaridades),
            key=lambda x: x[1],
            reverse=True
        )

        # Seleccionar las 3 frases más representativas (máximo de 3)
        # Filtramos para no duplicar fragmentos idénticos
        frases_representativas = []
        seen_texts = set()
        for c_obj, sim_score in sorted_comments:
            fmt_txt = c_obj["fragmento_mostrar"]
            if fmt_txt not in seen_texts:
                frases_representativas.append(fmt_txt)
                seen_texts.add(fmt_txt)
            if len(frases_representativas) >= 3:
                break

        # Contadores por segmento NPS
        detractores = sum(1 for c in comm_list if c["nps_score"] <= 6)
        pasivos = sum(1 for c in comm_list if 7 <= c["nps_score"] <= 8)
        promotores = sum(1 for c in comm_list if c["nps_score"] >= 9)

        # Sentiment predominante
        sent_counts = pd.Series([c["sentimiento"] for c in comm_list]).value_counts()
        sent_pred = sent_counts.index[0] if not sent_counts.empty else "neutro"

        # Agregaciones geográficas
        por_carrera = pd.Series([c["carrera"] for c in comm_list]).value_counts().to_dict()
        por_facultad = pd.Series([c["facultad"] for c in comm_list]).value_counts().to_dict()
        por_ciclo = pd.Series([c["ciclo"] for c in comm_list]).value_counts().to_dict()

        topicos_resultado.append({
            "topico": t_name,
            "categoria_padre": CATEGORIAS_PADRES[t_name],
            "tipo": "positivo" if sent_pred == "positivo" else ("negativo" if sent_pred == "negativo" else "mejora"),
            "icono": iconos.get(t_name, "💬"),
            "total_comentarios": total_comm,
            "detractores": detractores,
            "pasivos": pasivos,
            "sentimiento_predominante": sent_pred,
            "intensidad_promedio": round(float(np.mean([c["intensidad"] for c in comm_list])), 2),
            "frases_representativas": frases_representativas,
            "por_carrera": {k: int(v) for k, v in sorted(por_carrera.items(), key=lambda x: x[1], reverse=True)},
            "por_facultad": {k: int(v) for k, v in sorted(por_facultad.items(), key=lambda x: x[1], reverse=True)},
            "por_ciclo": {k: int(v) for k, v in sorted(por_ciclo.items(), key=lambda x: x[1], reverse=True)}
        })

    topicos_resultado.sort(key=lambda x: x["total_comentarios"], reverse=True)
    return topicos_resultado, comentarios_detallados
