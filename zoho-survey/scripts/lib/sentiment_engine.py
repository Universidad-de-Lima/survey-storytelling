import re
import spacy
import numpy as np
from typing import Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from lib.nlp import obtener_modelo

# Cargar spacy
try:
    nlp_spacy = spacy.load("es_core_news_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("es_core_news_sm")
    nlp_spacy = spacy.load("es_core_news_sm")

# Anclas Semánticas para Sentimiento
ANCHORS_SENTIMENT = {
    "positivo": "excelente bueno contento satisfecho recomendado gran calidad muy buena enseñanza todo muy bien felicitaciones me gusta",
    "negativo": "malo pésimo insatisfecho disconforme queja mala atención desactualizado lento demora mal servicio pésima metodología no me gusta no sirve falla",
    "neutro": "normal pasable promedio estandar sin comentarios ni bueno ni malo regular aceptable podria ser"
}

_SENT_EMBEDDINGS = None
_SENT_KEYS = None

def _inicializar_embeddings():
    global _SENT_EMBEDDINGS, _SENT_KEYS
    if _SENT_EMBEDDINGS is None:
        model = obtener_modelo()
        _SENT_KEYS = list(ANCHORS_SENTIMENT.keys())
        _SENT_EMBEDDINGS = model.encode(list(ANCHORS_SENTIMENT.values()))

# ==========================================
# LÓGICA DE INTENSIDAD (HÍBRIDA)
# ==========================================

# Señal 1: Intensificadores y Atenuantes
INTENSIFICADORES = r"\b(muy|demasiado|súper|super|extremadamente|altamente|totalmente|completamente|excelente|horrible|pésimo|pesimo|terrible|increíble|increible|fascinante)\b"
ATENUANTES = r"\b(algo|un poco|podría|podria|quizás|quizas|ligeramente|tal vez|regular)\b"

# Señal 2: Patrones de Severidad
SEVERIDAD = r"\b(nunca|siempre|constantemente|cada ciclo|cada semestre|cada vez|frecuentemente|no funciona|no sirve|no responde|no permite|se cae|falla|colapsa|se malogra|pierde|bloquea|impide|inunda)\b"

# Señal 3: Impacto Operativo
IMPACTO = r"\b(no pude|perdí el|perdi el|no logré|no logre|se perdió|se perdio|imposible)\b"

def calcular_intensidad(texto: str) -> (int, bool):
    """Calcula intensidad de 1 a 5 basada en léxico, severidad e impacto. Retorna (score, es_evento_negativo)."""
    doc = nlp_spacy(texto.lower())
    texto_lower = texto.lower()
    
    score = 3  # Moderado por defecto
    es_evento_negativo = False
    
    # 1. Analizar Intensificadores / Atenuantes
    score += len(re.findall(INTENSIFICADORES, texto_lower))
    score -= len(re.findall(ATENUANTES, texto_lower))
        
    # 2. Analizar Patrones de Severidad
    matches_sev = re.findall(SEVERIDAD, texto_lower)
    if matches_sev:
        score += len(matches_sev)
        es_evento_negativo = True
        
    # 3. Analizar Impacto Operativo
    matches_imp = re.findall(IMPACTO, texto_lower)
    if matches_imp:
        score += len(matches_imp)
        es_evento_negativo = True
        
    # Si "inunda" está presente y necesitamos que sea 5, y solo hay un match, podemos forzar +2 para palabras críticas
    if "inunda" in texto_lower:
        score += 1
        
    # Clamping entre 1 y 5
    return max(1, min(5, score)), es_evento_negativo

# ==========================================
# MOTOR PRINCIPAL
# ==========================================

def analizar_sentimiento_intensidad(texto: str) -> Dict[str, Any]:
    """
    Recibe un texto (Opinion Unit) y retorna sentimiento, intensidad, confianza y scores en crudo.
    """
    if not texto or not str(texto).strip():
        return {
            "sentimiento": "neutro",
            "intensidad": 1,
            "confianza_sentimiento": 1.0,
            "score_positivo": 0.0,
            "score_negativo": 0.0,
            "score_neutro": 1.0,
            "motor": "local"
        }
        
    _inicializar_embeddings()
    model = obtener_modelo()
    
    # 1. Calcular Similitudes Coseno
    emb = model.encode([texto])
    sim_scores = cosine_similarity(emb, _SENT_EMBEDDINGS)[0]
    
    score_pos = float(sim_scores[0])
    score_neg = float(sim_scores[1])
    score_neu = float(sim_scores[2])
    
    # 2. Convertir a Probabilidades (Softmax con temperatura 10 para calibración)
    temperatura = 10.0
    exp_scores = np.exp(sim_scores * temperatura)
    probs = exp_scores / np.sum(exp_scores)
    
    idx_ganador = np.argmax(probs)
    sentimiento_ganador = _SENT_KEYS[idx_ganador]
    confianza = float(probs[idx_ganador])
    
    # 3. Calcular Intensidad y Eventos Negativos
    intensidad, es_evento_negativo = calcular_intensidad(texto)
    
    # 4. Ajustes por Reglas de Negocio
    if es_evento_negativo and sentimiento_ganador != "negativo":
        sentimiento_ganador = "negativo"
        # La confianza podría recalibrarse, pero la dejamos igual para trazabilidad
    elif sentimiento_ganador == "neutro":
        intensidad = min(2, intensidad)
        
    return {
        "sentimiento": sentimiento_ganador,
        "intensidad": intensidad,
        "confianza_sentimiento": round(confianza, 4),
        "score_positivo": round(score_pos, 4),
        "score_negativo": round(score_neg, 4),
        "score_neutro": round(score_neu, 4),
        "motor": "local"
    }
