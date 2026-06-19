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
    
    # Correcciones ortográficas y gramaticales frecuentes de alumnos
    t = re.sub(r'\blas\s+ascensores\b', 'los ascensores', t)
    t = re.sub(r'\bla\s+ascensor\b', 'el ascensor', t)
    t = re.sub(r'\bhaiga\b', 'haya', t)
    t = re.sub(r'\bcafeteria\b', 'cafetería', t)
    
    # Reducir espacios
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def proteger_entidades(texto: str) -> str:
    t = texto
    # Proteger pabellones aislados inconfundibles convirtiéndolos en un token
    t = re.sub(r'\b(A1|A2|D1|D2|D3|E1|E2|H|I1|I2|L1|L2|L3|M|MS|N|O1|O2)\b', lambda m: f"PABELLON_{m.group(1).upper()}", t, flags=re.IGNORECASE)
    # Proteger pabellón 'O' solo si tiene contexto de infraestructura
    t = re.sub(r'\b(pabell[oó]n|edificio|torre|ascensores\s+de|ascensor\s+de|aulas\s+de|ba[ñn]os\s+de|del|el|los)\s+o\b', r'\1 PABELLON_O', t, flags=re.IGNORECASE)
    
    for patron in ENTIDADES:
        def replace_func(match):
            return match.group(0).replace(" ", "_")
        t = re.sub(patron, replace_func, t, flags=re.IGNORECASE)
    return t

def desproteger_entidades(texto: str) -> str:
    t = texto
    # Manejo específico para O (porque son O1 y O2)
    t = re.sub(r'\bPABELLON_O\b', 'los edificios O', t)
    # Manejo para el resto de pabellones
    t = re.sub(r'\bPABELLON_([A-Z0-9]+)\b', r'el edificio \1', t)
    t = t.replace("_", " ")
    return t

def _limpiar_unidad(texto: str) -> str:
    """Elimina residuos de puntuación o tokens vacíos al inicio o final de una Meaning Unit"""
    t = texto.strip()
    # Limpiar conjunciones y puntuaciones al inicio
    t = re.sub(r'^(?:[yoe]\s+)+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^[\s,;.\-:]+', '', t)
    # Limpiar conjunciones y puntuaciones al final
    t = re.sub(r'(?:\s+[yoe])+$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\s,;.\-:]+$', '', t)
    t = t.strip()
    # Descartar unidades que son puro ruido
    ruido = ["etc", "etc.", "entre otros", "cosas asi", "cosas así", "y demas", "y demás", "varios", "ninguna", "ninguno", "nada"]
    if t.lower() in ruido:
        return ""
    return t

def _extraccion_heuristica_fallback(texto: str) -> List[str]:
    """Fallback cuando SpaCy no está disponible"""
    bloques = re.split(r"[\n\r.;:]+|\b(?:pero|sin\s+embargo|aunque)\b", texto, flags=re.IGNORECASE)
    unidades = []
    for b in bloques:
        # Fallback ultra-básico: romper por comas si es largo
        if len(b.split()) > 8:
            sub = re.split(r",", b)
            unidades.extend(sub)
        else:
            unidades.append(b)
    return [u.strip() for u in unidades if u.strip()]

def extraer_unidades_opinion(texto: str) -> List[str]:
    """
    Abstracción principal para extraer Meaning Units (Unidades de Opinión).
    No segmenta oraciones por gramática, sino que intenta aislar ideas evaluables.
    """
    nlp = get_nlp()
    if not nlp:
        unidades = _extraccion_heuristica_fallback(texto)
    else:
        # 1. Separación fuerte por puntuación divisoria o conectores.
        # Estos siempre separan ideas independientes.
        bloques = re.split(r"[\n\r.;:]+|\b(?:pero|sin\s+embargo|aunque|mientras\s+que|por\s+otro\s+lado|o\s+que|y\s+que)\b", texto, flags=re.IGNORECASE)
        unidades = []
        
        for bloque in bloques:
            bloque = bloque.strip()
            if not bloque: continue
            
            doc = nlp(bloque)
            
            conjs = [t for t in doc if t.dep_ == "conj"]
            cortar_en = []
            
            for c in conjs:
                h = c.head
                # A. Clausulas Verbales (ej: Deberían "mejorar" X y "ampliar" Y)
                if h.pos_ in ["VERB", "AUX"] and c.pos_ in ["VERB", "AUX"]:
                    for child in h.children:
                        if child.dep_ == "cc" and child.i < c.i: cortar_en.append(child.i)
                    for child in c.children:
                        if child.dep_ == "cc" and child.i < c.i: cortar_en.append(child.i)
                    for i in range(h.i, c.i):
                        if doc[i].text == ",": cortar_en.append(i)
                
                # B. Clausulas Nominales y Enumeraciones (ej: "Falta de aire", "falta de enchufes")
                elif h.pos_ in ["NOUN", "PROPN", "ADJ"] and c.pos_ in ["NOUN", "PROPN", "ADJ"]:
                    depende_de_verbo = any(anc.pos_ in ["VERB", "AUX"] for anc in h.ancestors)
                    es_lista_simple = len(list(h.subtree)) <= 3 and len(list(c.subtree)) <= 3
                    
                    if not depende_de_verbo or not es_lista_simple:
                        for child in h.children:
                            if child.dep_ == "cc" and child.i < c.i: cortar_en.append(child.i)
                        for child in c.children:
                            if child.dep_ == "cc" and child.i < c.i: cortar_en.append(child.i)
                        for i in range(h.i, c.i):
                            if doc[i].text == ",": cortar_en.append(i)

            # C. Separación adicional por comas en enumeraciones largas sin conj explícito
            for tok in doc:
                if tok.text == "," and tok.i not in cortar_en:
                    # Si a la izquierda y derecha hay un sustantivo/adjetivo sustantivado
                    # que no depende estrictamente el uno del otro (ej. nmod).
                    if tok.head.pos_ in ["NOUN", "PROPN"] and tok.head.dep_ in ["ROOT", "appos", "conj"]:
                         # Solo cortar si la frase es sustancial
                         if len(list(tok.head.subtree)) > 2:
                             cortar_en.append(tok.i)
                         
            cortar_en = sorted(list(set(cortar_en)))
            
            if cortar_en:
                inicio = 0
                for idx in cortar_en:
                    frag = doc[inicio:idx].text.strip()
                    if frag: unidades.append(frag)
                    inicio = idx + 1
                frag = doc[inicio:].text.strip()
                if frag: unidades.append(frag)
            else:
                unidades.append(bloque)

    # 2. Post-procesamiento y validación
    resultados = []
    for u in unidades:
        l = _limpiar_unidad(u)
        # Validar que tenga al menos 3 caracteres alfanuméricos
        if l and len(re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]', '', l)) >= 3:
            # Capitalizar primera letra
            l = l[0].upper() + l[1:] if len(l) > 1 else l.upper()
            if l not in resultados: # Desduplicar
                resultados.append(l)
                
    return resultados

def fragmentar_comentario_nps(comentario_original: str, sanitizar_func=None) -> List[str]:
    """
    Punto de entrada compatible con el pipeline actual.
    Transforma el texto completo en Fragmentos NPS (Meaning Units).
    """
    if not isinstance(comentario_original, str) or not comentario_original.strip():
        return []
        
    texto = normalizar_texto(comentario_original)
    texto = proteger_entidades(texto)
    
    if sanitizar_func:
        valido, mensaje = sanitizar_func(texto)
        if not valido:
            return []
            
    unidades = extraer_unidades_opinion(texto)
    
    # Desenmascarar entidades
    resultados_finales = []
    for u in unidades:
        final_str = desproteger_entidades(u)
        resultados_finales.append(final_str)
        
    return resultados_finales
