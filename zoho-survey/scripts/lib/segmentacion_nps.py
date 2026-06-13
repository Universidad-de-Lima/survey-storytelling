import re
from typing import List, Tuple
import logging

try:
    import spacy
except ImportError:
    spacy = None

# Intentar cargar el modelo, con lazy loading
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None and spacy is not None:
        try:
            _nlp = spacy.load("es_core_news_sm", disable=["ner", "lemmatizer", "textcat"])
        except Exception as e:
            logging.warning(f"No se pudo cargar es_core_news_sm: {e}")
            _nlp = False
    return _nlp

# Entidades a proteger
ENTIDADES = [
    r"administraci[oó]n\s+y\s+finanzas",
    r"ciencia\s+pol[ií]tica",
    r"ingenier[ií]a\s+industrial\s+y\s+de\s+sistemas",
    r"arquitectura\s+y\s+dise[nñ]o",
    r"ciencias\s+empresariales\s+y\s+econ[oó]micas",
    r"comunicaci[oó]n",
    r"derecho",
    r"psicolog[ií]a",
    r"mi\s+ulima",
    r"bienestar\s+y\s+empleabilidad",
    r"centro\s+de\s+idiomas"
]

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    t = texto.lower()
    # Correcciones informales comunes
    t = re.sub(r'\bq\b', 'que', t)
    t = re.sub(r'\bxq\b', 'porque', t)
    t = re.sub(r'\bpq\b', 'porque', t)
    t = re.sub(r'\btmb\b', 'también', t)
    t = re.sub(r'\bvcs\b', 'veces', t)
    
    # Reducir espacios
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def proteger_entidades(texto: str) -> str:
    t = texto
    for patron in ENTIDADES:
        def replace_func(match):
            return match.group(0).replace(" ", "_")
        t = re.sub(patron, replace_func, t, flags=re.IGNORECASE)
    return t

def desproteger_entidades(texto: str) -> str:
    return texto.replace("_", " ")

def fragmentacion_heuristica_inicial(texto: str) -> List[str]:
    # 1. Dividir por signos de puntuación finales explícitos
    sentencias = re.split(r"[\n\r.!?]+", texto)
    
    # 2. Dividir por conectores adversativos y de adición fuertes
    patron_conectores = r"\b(?:pero|sin\s+embargo|aunque|no\s+obstante|en\s+cambio|además|así\s+como)\b"
    fragmentos = []
    for s in sentencias:
        sub_frags = re.split(patron_conectores, s, flags=re.IGNORECASE)
        for sf in sub_frags:
            clean_sf = sf.strip()
            if clean_sf:
                fragmentos.append(clean_sf)
    return fragmentos

def procesar_fragmento_con_spacy(texto: str) -> List[str]:
    nlp = get_nlp()
    if not nlp or len(texto.split()) < 8:
        # Fallback de comas si no hay spacy o es muy corto
        return fallback_comas(texto)
    
    doc = nlp(texto)
    
    # Buscar si hay múltiples verbos principales
    verbos = [tok for tok in doc if tok.pos_ in ("VERB", "AUX")]
    if len(verbos) <= 1:
        # Fallback a comas si no hay múltiples verbos
        return fallback_comas(texto)
    
    # Intentar partir donde hay conjunciones "y", "ni", "o" que separan cláusulas
    puntos_corte = []
    for tok in doc:
        if tok.text.lower() in ["y", "e", "ni", "o", ","]:
            # Verificar si conecta dos verbos
            if tok.head.pos_ in ("VERB", "AUX") or tok.dep_ == "cc" or tok.dep_ == "conj":
                puntos_corte.append(tok.i)
    
    if not puntos_corte:
        return fallback_comas(texto)
    
    # Cortar el texto
    fragmentos = []
    inicio = 0
    for idx in puntos_corte:
        frag = doc[inicio:idx].text.strip()
        if frag and frag not in [",", "y", "e", "ni", "o"]:
            fragmentos.append(frag)
        inicio = idx + 1
    
    frag_final = doc[inicio:].text.strip()
    if frag_final and frag_final not in [",", "y", "e", "ni", "o"]:
        fragmentos.append(frag_final)
        
    return fragmentos

def fallback_comas(texto: str) -> List[str]:
    # Partir por comas
    parts = re.split(r",", texto)
    return [p.strip() for p in parts if p.strip() and p.strip() not in [","]]

def validar_fragmento(texto: str) -> bool:
    if not texto:
        return False
    # Más de 3 letras o números
    if len(re.sub(r'[^a-zA-Z0-9]', '', texto)) < 3:
        return False
    return True

def fragmentar_comentario_nps(comentario_original: str, sanitizar_func=None) -> List[str]:
    if not isinstance(comentario_original, str) or not comentario_original.strip():
        return []
        
    texto = normalizar_texto(comentario_original)
    texto = proteger_entidades(texto)
    
    if sanitizar_func:
        valido, mensaje = sanitizar_func(texto)
        if not valido:
            return []
    
    # Heurística inicial
    cortes_1 = fragmentacion_heuristica_inicial(texto)
    
    # SpaCy y Comas
    cortes_2 = []
    for c in cortes_1:
        if len(c.split()) >= 6:
            sub = procesar_fragmento_con_spacy(c)
            cortes_2.extend(sub)
        else:
            cortes_2.extend(fallback_comas(c))
            
    # Validación y Des-enmascarado
    resultados = []
    for c in cortes_2:
        final_str = desproteger_entidades(c)
        if validar_fragmento(final_str):
            # Normalizar mayúscula inicial
            final_str = final_str.capitalize()
            if final_str not in resultados: # Desduplicar
                resultados.append(final_str)
                
    return resultados
