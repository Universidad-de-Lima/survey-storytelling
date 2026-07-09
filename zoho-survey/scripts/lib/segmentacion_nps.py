import re
from typing import List, Tuple
import logging
from .nlp import normalizar_texto as _nlp_normalizar_texto
from .nlp import sanitizar_comentario

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
    return _nlp_normalizar_texto(texto)


def proteger_entidades(texto: str) -> str:
    t = texto
    # Limpiar introducciones parentéticas que rompen el chunking
    t = re.sub(r'(?i)(por\s+mi\s+experiencia|al\s+menos\s+en\s+mi\s+experiencia|en\s+general|la\s+verdad)\s*,', r'\1', t)
    
    # Proteger pabellones aislados inconfundibles convirtiéndolos en un token
    t = re.sub(r'\b(A1|A2|D1|D2|D3|E1|E2|H|I1|I2|L1|L2|L3|M|MS|N|O1|O2)\b', lambda m: f"PABELLON_{m.group(1).upper()}", t, flags=re.IGNORECASE)
    # Proteger pabellón 'O' solo si tiene contexto de infraestructura
    t = re.sub(r'\b(pabell[oó]n|edificios?|torres?|ascensores?|aulas?|ba[ñn]os?)(?:\s+de\s+|\s+del\s+|\s+el\s+|\s+los\s+|\s+las\s+|\s+la\s+|\s+)o\b', r'\1_de_PABELLON_O', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(del|el|los)\s+o\b', r'\1 PABELLON_O', t, flags=re.IGNORECASE)
    
    for patron in ENTIDADES:
        def replace_func(match):
            return match.group(0).replace(" ", "_")
        t = re.sub(patron, replace_func, t, flags=re.IGNORECASE)
    return t

def desproteger_entidades(texto: str) -> str:
    t = texto
    # Manejo específico para O (porque son O1 y O2)
    t = re.sub(r'\bPABELLON_O\b', 'los edificios O', t)
    t = re.sub(r'\_de\_PABELLON\_O\b', ' de los edificios O', t)
    # Manejo para el resto de pabellones
    t = re.sub(r'\bPABELLON_([A-Z0-9]+)\b', r'el edificio \1', t)
    t = t.replace("_", " ")
    return t

def _limpiar_unidad(texto: str) -> str:
    """Elimina residuos de puntuación o tokens vacíos al inicio o final de una Meaning Unit"""
    t = texto.strip()
    # Eliminar muletillas introductorias
    t = re.sub(r'^(?:me\s+parece\s+que|creo\s+que|yo\s+creo\s+que|pienso\s+que|considero\s+que|siento\s+que)\s+', '', t, flags=re.IGNORECASE)
    
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

def _distribuir_contexto_compartido(unidades: List[str], nlp) -> List[str]:
    """
    Realiza la distribución de contexto hacia la izquierda (Right-Node Raising)
    para cláusulas compartidas separadas por conjunciones o asindetón.
    """
    result = list(unidades)
    for i in range(len(result) - 1):
        u1 = result[i]
        u2 = result[i+1]
        
        # Heurística A: Cruce léxico de terminación (ej: "Falta de equipos" + "actualización de equipos de grabación")
        u1_words = u1.split()
        if u1_words:
            last_word = u1_words[-1]
            if last_word in u2.split():
                parts = u2.split(last_word)
                if len(parts) > 1 and parts[-1].strip().startswith("de "):
                    tail = parts[-1]
                    result[i] = u1 + tail
                    continue
        
        # Heurística B: Propagación de Adjetivos / Complementos Predicativos
        doc2 = nlp(u2)
        split_idx = -1
        for tok in doc2:
            if tok.pos_ == "ADJ" and tok.dep_ == "amod":
                split_idx = tok.i
                break
        
        if split_idx != -1:
            tail = doc2[split_idx:].text
            doc1 = nlp(u1)
            has_adj_or_verb = any(t.pos_ in ["ADJ", "VERB"] for t in doc1)
            if not has_adj_or_verb:
                result[i] = u1 + " " + tail

        # Heurística C: Left-Node Raising (Propagación del Contexto Verbal hacia la derecha)
        # Limpiar conjunciones iniciales para análisis correcto
        u2_clean = re.sub(r'^(?:y|o|e)\s+', '', u2, flags=re.IGNORECASE)
        doc2 = nlp(u2_clean)
        has_verb_u2 = any(t.pos_ in ["VERB", "AUX"] for t in doc2) or re.search(r'\b(recomendar\w*|enseñ\w*|gust\w*)\b', u2_clean, re.IGNORECASE)
        
        if not has_verb_u2:
            doc1 = nlp(u1)
            has_verb_u1 = any(t.pos_ in ["VERB", "AUX"] for t in doc1)
            
            if has_verb_u1:
                # Encontrar el primer sustantivo en u1
                noun_idx = -1
                for tok in doc1:
                    if tok.pos_ in ["NOUN", "PROPN"]:
                        noun_idx = tok.i
                        break
                
                if noun_idx > 0:
                    prefix = doc1[:noun_idx].text.strip()
                    # Verificar que el prefijo realmente contenga el verbo
                    prefix_doc = nlp(prefix)
                    if any(t.pos_ in ["VERB", "AUX"] for t in prefix_doc):
                        result[i+1] = f"{prefix} {u2}"

    return result

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
                    # Heurística de protección: no separar verbos muy unidos (ej: trabaja y estudia)
                    if abs(c.i - h.i) <= 2 or h.dep_ in ["acl", "advcl", "relcl", "acl:relcl"]:
                        continue
                    
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
                    # No cortar si la frase antes de la coma es muy corta (ej. introducciones o muletillas)
                    if tok.i < 3:
                        continue
                    # Si a la izquierda y derecha hay un sustantivo/adjetivo sustantivado o verbo principal
                    if tok.head.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"] and tok.head.dep_ in ["ROOT", "appos", "conj", "advcl", "parataxis"]:
                         # Solo cortar si la frase es sustancial
                         if len(list(tok.head.subtree)) >= 2:
                             cortar_en.append(tok.i)
                             
            # C2. Heurística de contraste (ej: "la universidad si la carrera no")
            for i in range(len(doc) - 2):
                if doc[i].text.lower() in ["si", "sí"] and doc[i+1].pos_ in ["DET", "NOUN", "PRON"]:
                    for j in range(i+1, min(len(doc), i+6)):
                        if doc[j].text.lower() == "no":
                            cortar_en.append(i + 1)
                            break
                            
            # C3. Evitar cortar antes de pronombres relativos (que, quien)
            cortar_en = [idx for idx in cortar_en if idx < len(doc) and doc[idx].text.lower() not in ["que", "quien", "quienes"]]
                             
            # D. Separación por aposición/asindetón sin comas (ej: "muchos cursos pocos créditos")
            for i in range(len(doc) - 1):
                if doc[i].pos_ in ["NOUN", "PROPN"] and doc[i+1].pos_ in ["DET", "PRON"]:
                    if doc[i+1].head.i != doc[i].i:
                        cortar_en.append(i + 1)
                         
            cortar_en = sorted(list(set(cortar_en)))
            
            if cortar_en:
                inicio = 0
                for idx in cortar_en:
                    frag = doc[inicio:idx].text.strip()
                    if frag: unidades.append(frag)
                    
                    if doc[idx].pos_ in ["CCONJ", "PUNCT", "SCONJ"]:
                        inicio = idx + 1
                    else:
                        inicio = idx
                        
                frag = doc[inicio:].text.strip()
                if frag: unidades.append(frag)
            else:
                unidades.append(bloque)

    # 2. Post-procesamiento semántico avanzado (Right-Node Raising)
    if nlp:
        unidades = _distribuir_contexto_compartido(unidades, nlp)

    # 3. Limpieza y validación final
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
