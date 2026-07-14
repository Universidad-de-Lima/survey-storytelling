"""
IA CUALITATIVO — Orquestador del analisis cualitativo basado en DeepSeek.

Este modulo es la capa de integracion entre build_json.py y los 4 submodulos
especializados: ia_cache (cache persistente), ia_client (cliente DeepSeek),
ia_filtro_ruido (pre-filtrado), e ia_validacion (validacion de respuestas).

Reemplaza a los 3 modulos locales (segmentacion_nps.py, aspect_extraction.py,
sentiment_engine.py) por una unica llamada a DeepSeek que ejecuta las 5 tareas
en conjunto, con coherencia de contexto y reglas de sesgo NPS aplicadas.

Uso principal (integrado en build_json.py):
  from lib.ia_cualitativo import generar_salidas_cualitativas_ia
  datos_fragmentos, dataset, metadata = generar_salidas_cualitativas_ia(
      df_sent=df_sent, taxonomia=..., csat_columns_map=..., cache_path=...
  )

Variables de entorno:
  - DEEPSEEK_API_KEY (obligatorio para modo IA).
  - IA_CUALITATIVO_MODEL (opcional, default "deepseek-v4-flash").
  - IA_CUALITATIVO_MAX_RPM (opcional, default 60).
  - IA_CUALITATIVO_CACHE (opcional, "1" para habilitar, "0" para deshabilitar).
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .ia_cache import CacheManager
from .ia_client import DeepSeekClient, DEFAULT_WORKERS
from .ia_filtro_ruido import es_ruido_pre_filtro, generar_unidad_ruido
from .ia_validacion import validar_respuesta_ia
from .prompts_cualitativo import (
    build_system_prompt,
    build_user_prompt,
    RATING_TO_SCORE,
    PROMPT_VERSION,
)

try:
    import pandas as _pd
except ImportError:
    _pd = None

logger = logging.getLogger(__name__)


# ============================================================
# FUNCION PRINCIPAL: analizar un comentario
# ============================================================

def analizar_comentario(comentario: str,
                        nps_score: int,
                        csat_ratings: Dict[str, str],
                        taxonomia: Dict[str, str],
                        categorias_padre: List[str],
                        client: DeepSeekClient,
                        cache: Optional[CacheManager] = None,
                        id_encuesta: str = "") -> Dict[str, Any]:
    """Analiza un comentario completo y devuelve {unidades: [...]}.

    Usa cache si esta disponible. Si la API falla, devuelve
    una unidad placeholder no valida.
    """
    if cache is not None:
        cached = cache.get(comentario, nps_score, csat_ratings)
        if cached is not None:
            return cached

    system_prompt = build_system_prompt(taxonomia, categorias_padre)
    user_prompt = build_user_prompt(comentario, nps_score, csat_ratings, id_encuesta)

    try:
        raw_resp = client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=10000,
        )
    except RuntimeError as e:
        logger.error(f"DeepSeek fallo para {id_encuesta}: {e}")
        return _placeholder(comentario, f"DeepSeek fallo: {str(e)[:100]}",
                           "Error de API (fallback)")

    sanada, err = validar_respuesta_ia(raw_resp, taxonomia)
    if sanada is None:
        logger.warning(f"Respuesta IA invalida para {id_encuesta}: {err}")
        return _placeholder(comentario, f"Validacion fallo: {err}",
                           "Respuesta IA invalida")

    if cache is not None:
        cache.set(comentario, nps_score, csat_ratings, sanada)

    return sanada


def _placeholder(comentario: str, detalle: str, motivo: str) -> dict:
    """Genera placeholder de unidad no valida."""
    return {
        "unidades": [{
            "orden": 1,
            "texto": comentario[:100],
            "es_valido": False,
            "motivo_invalidez": motivo,
            "sentimiento": "neutro",
            "intensidad": 1,
            "justificacion_sentimiento": detalle,
            "dimension": "Pendiente de Clasificación",
            "categoria_padre": "Pendiente de Clasificación",
            "es_mencion_mejora": False,
            "es_salvavidas": False,
            "dimension_evaluada_rating": None,
            "dimension_evaluada_score": None,
            "sub_aspectos": [],
        }]
    }


# ============================================================
# FUNCION DE ALTO NIVEL: analizar todo el dataset
# ============================================================

def analizar_dataset_cualitativo(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    cache_path: Optional[Path] = None,
    progress_every: int = 25,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Analiza cualitativamente todo el dataset de comentarios NPS.

    Returns:
        (dataset_cualitativo, metadata) donde dataset_cualitativo es una
        lista de dicts (uno por unidad) y metadata contiene estadisticas.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY no configurada.")

    client = DeepSeekClient(api_key=api_key)
    cache = (CacheManager(cache_path, prompt_version=PROMPT_VERSION)
             if cache_path else None)
    if cache is not None:
        cache.reset_hit_count()
    categorias_padre = sorted(set(taxonomia.values()))

    # Cleaning defensivo
    if _pd is not None:
        try:
            df_sent = df_sent.copy()
            df_sent["nps_score"] = _pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"]).reset_index(drop=True)
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent = df_sent[df_sent["comentario"].str.strip() != ""]
            df_sent = df_sent[df_sent["comentario"].str.strip().str.lower() != "nan"]
        except Exception as clean_err:
            logger.warning(f"Cleaning defensivo fallo: {clean_err}")

    dataset_cualitativo: List[Dict[str, Any]] = []
    total_comentarios = 0
    total_unidades = 0
    errores = 0
    cache_hits = 0
    ruido_filtrado = 0

    total_rows = len(df_sent)
    workers = DEFAULT_WORKERS
    logger.info(
        f"Iniciando analisis IA de {total_rows} comentarios "
        f"(modelo: {client.model}, {workers} workers, timeout={client.timeout}s)."
    )

    # Pre-coleccionar tasks
    tasks: List[Tuple] = []
    for idx, row in df_sent.iterrows():
        comentario_val = row["comentario"]
        if _pd is not None and _pd.isna(comentario_val):
            continue
        if comentario_val is None:
            continue
        comentario = str(comentario_val).strip()
        if not comentario or comentario.lower() == "nan":
            continue

        nps_val = row["nps_score"]
        if _pd is not None and _pd.isna(nps_val):
            continue
        try:
            nps = int(nps_val)
        except (ValueError, TypeError):
            continue

        res_id = str(row.get("ID", f"R_{idx}"))
        facultad = str(row.get("facultad", ""))
        carrera = str(row.get("carrera", ""))
        ciclo = str(row.get("ciclo", ""))
        satisfaccion_global = str(row.get("satisfaccion_global", "No respondido"))

        csat_ratings: Dict[str, str] = {}
        for dim, col in csat_columns_map.items():
            if col in row.index:
                val = row[col]
                if val and str(val).strip() and str(val).strip() in RATING_TO_SCORE:
                    csat_ratings[dim] = str(val).strip()

        tasks.append((comentario, nps, csat_ratings, res_id,
                      facultad, carrera, ciclo, satisfaccion_global))

    logger.info(f"{len(tasks)} tasks preparados de {total_rows} filas.")
    _start_batch = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        fut_map = {}
        for (comentario, nps, csat_ratings, res_id,
             facultad, carrera, ciclo, satisfaccion_global) in tasks:
            es_ruido, motivo = es_ruido_pre_filtro(comentario)
            if es_ruido:
                ruido_filtrado += 1
                unidad = generar_unidad_ruido(motivo)
                dataset_cualitativo.append(_build_item(
                    res_id, "01", facultad, carrera, ciclo, nps,
                    satisfaccion_global, comentario[:100], "", "",
                    "", [], "neutro", 1, 1.0, comentario,
                    False, motivo, "deepseek"
                ))
                continue

            future = executor.submit(
                _analizar_un_comentario, comentario, nps, csat_ratings,
                taxonomia, categorias_padre, client, cache, res_id,
                facultad, carrera, ciclo, satisfaccion_global
            )
            fut_map[future] = (res_id, facultad, carrera, ciclo,
                               satisfaccion_global, nps, comentario)

        for i, future in enumerate(as_completed(fut_map)):
            res_id, facultad, carrera, ciclo, satisfaccion_global, nps, \
                comentario = fut_map[future]
            try:
                resultado = future.result()
                unidades = resultado.get("unidades", [])
                total_comentarios += 1
                total_unidades += len(unidades)
                for unidad in unidades:
                    es_valido = unidad.get("es_valido", True)
                    sent = unidad.get("sentimiento", "neutro").lower()
                    dataset_cualitativo.append(_build_item(
                        res_id, f"{unidad['orden']:02d}",
                        facultad, carrera, ciclo, nps,
                        satisfaccion_global, unidad.get("texto", ""),
                        unidad.get("dimension", ""),
                        unidad.get("dimension", ""),
                        unidad.get("categoria_padre", ""),
                        unidad.get("sub_aspectos", []),
                        sent, unidad.get("intensidad", 3),
                        1.0, comentario, es_valido,
                        unidad.get("motivo_invalidez", ""), "deepseek"
                    ))
            except Exception as e:
                errores += 1
                logger.error(f"Error procesando {res_id}: {e}")

            if (i + 1) % progress_every == 0:
                elapsed = time.perf_counter() - _start_batch
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Progreso: {i+1}/{len(fut_map)} comentarios "
                    f"({rate:.1f} cmt/s), {total_unidades} unidades, "
                    f"{errores} errores, {ruido_filtrado} ruido."
                )

    _elapsed = time.perf_counter() - _start_batch
    if cache:
        cache.flush()

    # REND-02: Ordenar dataset para garantizar idempotencia.
    # as_completed produce resultados en orden de finalizacion (no determinista).
    # Ordenar por id_encuesta + id_fragmento asegura que mismo CSV -> mismo JSON.
    dataset_cualitativo.sort(key=lambda x: (x.get("id_encuesta", ""), x.get("id_fragmento", "")))

    cache_hits = cache.get_hit_count() if cache is not None else 0

    metadata = {
        "total_encuestas": total_comentarios,
        "total_fragmentos": total_unidades,
        "errores": errores,
        "ruido_filtrado": ruido_filtrado,
        "cache_hits": cache_hits,
        "tiempo_segundos": round(_elapsed, 2),
        "stats_sentimiento": {
            "total_opinion_units": total_unidades,
            "positivos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "positivo" and d["es_valido"]),
            "negativos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "negativo" and d["es_valido"]),
            "neutros": sum(1 for d in dataset_cualitativo
                           if d["sentimiento"] == "neutro" and d["es_valido"]),
        },
        "usage": client.usage,
    }

    logger.info(
        f"Analisis IA completado: {total_comentarios} comentarios, "
        f"{total_unidades} unidades, {errores} errores, "
        f"{ruido_filtrado} ruido pre-filtrado. "
        f"Tiempo: {_elapsed:.1f}s."
    )

    return dataset_cualitativo, metadata


def _build_item(res_id, ord_id, facultad, carrera, ciclo, nps,
                sat_global, texto, asp_detectado, asp_normalizado,
                cat_padre, sub_aspectos, sentimiento, intensidad,
                confianza, comentario_orig, es_valido, motivo, motor):
    """Construye un item del dataset cualitativo."""
    return {
        "id_encuesta": res_id,
        "id_fragmento": f"{res_id}_{ord_id}",
        "facultad": facultad,
        "carrera": carrera,
        "ciclo": ciclo,
        "nps_score": nps,
        "segmento_nps": (
            "Promotor" if nps >= 9
            else "Pasivo" if nps >= 7
            else "Detractor"
        ),
        "satisfaccion_global": sat_global,
        "texto": texto,
        "aspecto_detectado": asp_detectado,
        "aspecto_normalizado": asp_normalizado,
        "categoria_padre": cat_padre,
        "sub_aspectos": sub_aspectos,
        "sentimiento": sentimiento,
        "intensidad": intensidad,
        "confianza_sentimiento": confianza,
        "comentario_original": comentario_orig,
        "es_valido": es_valido,
        "motivo_invalidez": motivo,
        "motor": motor,
    }


def _analizar_un_comentario(comentario, nps, csat_ratings, taxonomia,
                            categorias_padre, client, cache, res_id,
                            facultad, carrera, ciclo, satisfaccion_global):
    """Helper para ejecutar en ThreadPoolExecutor."""
    return analizar_comentario(
        comentario=comentario,
        nps_score=nps,
        csat_ratings=csat_ratings,
        taxonomia=taxonomia,
        categorias_padre=categorias_padre,
        client=client,
        cache=cache,
        id_encuesta=res_id,
    )


# ============================================================
# CAPA DE INTEGRACION CON build_json.py
# ============================================================

def generar_salidas_cualitativas_ia(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    cache_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Capa de integracion con build_json.py.

    Retorna (datos_fragmentos, dataset_cualitativo, metadata) en formato
    compatible con el pipeline legacy.
    """
    dataset_cualitativo, metadata = analizar_dataset_cualitativo(
        df_sent=df_sent,
        taxonomia=taxonomia,
        csat_columns_map=csat_columns_map,
        cache_path=cache_path,
    )

    from collections import defaultdict
    grupos: Dict[str, List[Dict]] = defaultdict(list)
    for item in dataset_cualitativo:
        grupos[item["id_encuesta"]].append(item)

    datos_fragmentos = []
    for res_id, unidades in grupos.items():
        primera = unidades[0]
        fragmentos = []
        for u in unidades:
            fragmentos.append({
                "id_fragmento": u["id_fragmento"],
                "texto": u["texto"],
                "sentimiento": u.get("sentimiento", "neutro"),
                "intensidad": u.get("intensidad", 3),
                "aspecto_normalizado": u.get("aspecto_normalizado", ""),
                "categoria_padre": u.get("categoria_padre", ""),
                "es_valido": u.get("es_valido", True),
                "motivo_invalidez": u.get("motivo_invalidez", ""),
            })

        datos_fragmentos.append({
            "id_encuesta": res_id,
            "facultad": primera.get("facultad", ""),
            "carrera": primera.get("carrera", ""),
            "ciclo": primera.get("ciclo", ""),
            "nps_score": primera.get("nps_score", 0),
            "segmento_nps": primera.get("segmento_nps", ""),
            "satisfaccion_global": primera.get("satisfaccion_global", ""),
            "comentario_original": primera.get("comentario_original", ""),
            "fragmentos": fragmentos,
        })

    return datos_fragmentos, dataset_cualitativo, metadata
