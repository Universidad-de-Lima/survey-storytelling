"""
SURVEY ETL NLP — Módulo de procesamiento de lenguaje natural y tópicos semánticos.

Procesa y agrupa comentarios de encuestas libres (Pasivos y Detractores)
asociando términos semánticamente relacionados a tópicos configurados.
"""

import re
import pandas as pd
from typing import List, Dict, Optional
from .config import TOPICOS, STOPWORDS


def normalizar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto en español para facilitar el matching de palabras.
    Remueve tildes, caracteres especiales y convierte a minúsculas.
    """
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = texto.lower().strip()
    
    # Normalizar tildes comunes
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n"
    }
    for orig, rep in reemplazos.items():
        texto = texto.replace(orig, rep)
        
    # Eliminar caracteres especiales excepto letras, números y espacios
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def clasificar_en_topico(comentario_norm: str) -> Optional[str]:
    """
    Determina qué tópico semántico coincide mejor con el comentario normalizado.
    Retorna el nombre del tópico o None si no alcanza el umbral mínimo (0.5).
    """
    mejor_topico: Optional[str] = None
    mejor_score: float = 0.0
    
    # Separar palabras excluyendo stopwords configuradas para reducir ruido
    palabras_comentario = {w for w in comentario_norm.split() if w not in STOPWORDS}

    for topico_nombre, config in TOPICOS.items():
        palabras_clave_norm = [normalizar_texto(p) for p in config["palabras"]]
        coincidencias: float = 0.0
        for pk in palabras_clave_norm:
            # Coincidencia exacta o como subcadena en palabras largas
            if pk in palabras_comentario:
                coincidencias += 1.0
            elif any(pk in palabra for palabra in palabras_comentario if len(pk) > 4):
                coincidencias += 0.5
                
        if coincidencias > mejor_score:
            mejor_score = coincidencias
            mejor_topico = topico_nombre

    return mejor_topico if mejor_score >= 0.5 else None


def agrupar_comentarios_por_topico(df_comentarios: pd.DataFrame) -> List[Dict[str, any]]:
    """
    Toma un DataFrame con columnas [comentario, nps_score, carrera, facultad, ciclo]
    y agrupa los comentarios en tópicos semánticos estructurados.
    Solo procesa comentarios de Pasivos (NPS 7-8) y Detractores (NPS 0-6).
    """
    # REGLA CRÍTICA: Solo Pasivos y Detractores (NPS < 9)
    df_filtrado = df_comentarios[df_comentarios["nps_score"] < 9].copy()

    if df_filtrado.empty:
        return []

    df_filtrado["comentario_norm"] = df_filtrado["comentario"].apply(normalizar_texto)
    df_filtrado = df_filtrado[df_filtrado["comentario_norm"].str.len() > 10]

    # Clasificar cada comentario en un tópico
    df_filtrado["topico"] = df_filtrado["comentario_norm"].apply(clasificar_en_topico)

    topicos_resultado: List[Dict[str, any]] = []

    for topico_nombre, config in TOPICOS.items():
        subset = df_filtrado[df_filtrado["topico"] == topico_nombre]
        if len(subset) < 2:  # Umbral mínimo de relevancia
            continue

        # Extraer frases más largas y descriptivas
        frases_candidatas = subset["comentario"].dropna().tolist()
        frases_candidatas = [f.strip() for f in frases_candidatas if len(f.strip()) > 20]
        frases_candidatas.sort(key=len, reverse=True)
        frases_representativas = frases_candidatas[:3]

        # Conteos por tipo NPS
        detractores = int((subset["nps_score"] <= 6).sum())
        pasivos = int(subset["nps_score"].between(7, 8).sum())

        # Agrupaciones por dimensiones geográficas/académicas del negocio
        por_carrera = subset.groupby("carrera").size().to_dict()
        por_facultad = subset.groupby("facultad").size().to_dict()
        por_ciclo = subset.groupby("ciclo").size().to_dict()

        topicos_resultado.append({
            "topico": topico_nombre,
            "tipo": config["tipo"],
            "icono": config["icono"],
            "total_comentarios": int(len(subset)),
            "detractores": detractores,
            "pasivos": pasivos,
            "frases_representativas": frases_representativas,
            "por_carrera": {k: int(v) for k, v in sorted(por_carrera.items(), key=lambda x: x[1], reverse=True)},
            "por_facultad": {k: int(v) for k, v in sorted(por_facultad.items(), key=lambda x: x[1], reverse=True)},
            "por_ciclo": {k: int(v) for k, v in sorted(por_ciclo.items(), key=lambda x: x[1], reverse=True)}
        })

    # Ordenar de mayor a menor cantidad de comentarios
    topicos_resultado.sort(key=lambda x: x["total_comentarios"], reverse=True)
    return topicos_resultado
