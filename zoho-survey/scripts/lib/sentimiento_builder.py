"""
SURVEY ETL SENTIMIENTO BUILDER — Construcción del contrato sentimiento.json.

Ensambla los datos de fragmentación NPS y análisis cualitativo en la
estructura final sentimiento.json v3.0 que consume el frontend.
"""

import logging
from collections import Counter, defaultdict
from typing import Optional


def construir_sentimiento_json(
    datos_fragmentos: Optional[list],
    dataset_cualitativo: Optional[list],
    df,
    tiene_col_comentario: bool,
    nps_col: str,
    facultad_col: str = "Facultad",
    carrera_col: str = "Carrera",
    ciclo_col: str = "Ciclo",
) -> dict:
    """Construye el objeto sentimiento.json v3.0.

    Recibe los datos intermedios del pipeline cualitativo y los transforma
    en la estructura final que consume el frontend, incluyendo:
    - comentarios_detallados: lista plana de fragmentos con metadatos
    - distribuciones: por sentimiento, intensidad, carrera y ciclo
    - topicos_globales: agregación por aspecto normalizado

    Si no hay datos cualitativos, retorna un objeto vacío.
    """
    from lib.nlp import sanitizar_comentario

    if not tiene_col_comentario or not datos_fragmentos:
        return {}

    comentarios_detallados = []
    for frag in datos_fragmentos:
        if not frag.get("unidades"):
            continue
        for unidad in frag["unidades"]:
            comentario_raw = frag.get("comentario_original", "")
            comentario_mostrar = unidad.get("texto", "")
            nps_score = frag.get("nps_score", 0)
            nps_label = (
                "Promotor" if nps_score >= 9
                else "Pasivo" if nps_score >= 7
                else "Detractor"
            )
            entrada = {
                "id": unidad.get("orden", 0),
                "comentario_id_original": frag.get("comentario_id", ""),
                "comentario_original": sanitizar_comentario(comentario_raw),
                "fragmento_mostrar": sanitizar_comentario(comentario_mostrar),
                "carrera": frag.get("carrera", ""),
                "facultad": frag.get("facultad", ""),
                "ciclo": frag.get("ciclo", ""),
                "nps_score": nps_score,
                "nps_label": nps_label,
                "sentimiento": unidad.get("sentimiento", "neutro"),
                "intensidad": unidad.get("intensidad", 3),
                "aspecto_normalizado": unidad.get("aspecto_normalizado", ""),
                "categoria_padre": unidad.get("categoria_padre", ""),
                "es_valido": unidad.get("es_valido", True),
                "motivo_invalidez": unidad.get("motivo_invalidez", ""),
            }
            comentarios_detallados.append(entrada)

    if not comentarios_detallados:
        return {}

    # Tópicos globales: agregar por aspecto_normalizado
    topicos_globales = defaultdict(lambda: {
        "positivo": 0, "negativo": 0, "neutro": 0,
        "total": 0, "intensidad_promedio": 0.0
    })
    for c in comentarios_detallados:
        if not c["es_valido"]:
            continue
        topico = c["aspecto_normalizado"] or "sin_aspecto"
        tg = topicos_globales[topico]
        tg[c["sentimiento"]] += 1
        tg["total"] += 1

    for topico, data in topicos_globales.items():
        intensidades = [
            c["intensidad"] for c in comentarios_detallados
            if c["es_valido"] and (c["aspecto_normalizado"] or "sin_aspecto") == topico
        ]
        data["intensidad_promedio"] = (
            round(sum(intensidades) / len(intensidades), 2) if intensidades else 0.0
        )

    # Distribución de sentimiento
    sent_count = Counter(c["sentimiento"] for c in comentarios_detallados if c["es_valido"])
    total_validos = sum(sent_count.values()) or 1
    dist_sent = {
        "positivo": round((sent_count.get("positivo", 0) / total_validos) * 100, 1),
        "negativo": round((sent_count.get("negativo", 0) / total_validos) * 100, 1),
        "neutro": round((sent_count.get("neutro", 0) / total_validos) * 100, 1),
    }

    # Distribución de intensidad
    int_count = Counter(c["intensidad"] for c in comentarios_detallados if c["es_valido"])
    total_int = sum(int_count.values()) or 1
    dist_int = {
        str(k): round((int_count.get(k, 0) / total_int) * 100, 1)
        for k in range(1, 6)
    }

    # Distribuciones por carrera y ciclo
    dist_carrera = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0, "total": 0})
    dist_ciclo = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0, "total": 0})
    for c in comentarios_detallados:
        if not c["es_valido"]:
            continue
        dist_carrera[c["carrera"]][c["sentimiento"]] += 1
        dist_carrera[c["carrera"]]["total"] += 1
        if c["ciclo"] and c["ciclo"] != "NA":
            dist_ciclo[c["ciclo"]][c["sentimiento"]] += 1
            dist_ciclo[c["ciclo"]]["total"] += 1

    return {
        "version": "3.0",
        "total_comentarios": len(comentarios_detallados),
        "total_validos": total_validos,
        "total_invalidos": sum(1 for c in comentarios_detallados if not c["es_valido"]),
        "comentarios_detallados": comentarios_detallados,
        "topicos_globales": dict(topicos_globales),
        "distribucion_sentimiento": dist_sent,
        "distribucion_intensidad": dist_int,
        "distribucion_carrera": dict(dist_carrera),
        "distribucion_ciclo": dict(dist_ciclo),
    }
