"""
IA VALIDACION — Validación y corrección de respuestas de DeepSeek.

Valida y corrige unidades individuales y respuestas completas de la API
de DeepSeek, asegurando consistencia de tipos, campos requeridos y
coherencia entre dimensiones y categorías padre.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .ia_filtro_ruido import SENTIMIENTOS_VALIDOS, MOTIVOS_INVALIDEZ_VALIDOS

logger = logging.getLogger(__name__)


def validar_unidad(unidad: dict, taxonomia: Dict[str, str]) -> Optional[str]:
    """Valida una unidad y retorna mensaje de error o None si es válida.

    Verifica: campos requeridos, tipos, sentimiento en set válido,
    intensidad 1-5, coherencia dimensión→categoria_padre.
    """
    if not isinstance(unidad, dict):
        return "Unidad no es un dict"

    required = ["orden", "texto", "sentimiento", "intensidad", "dimension",
                 "categoria_padre"]
    for field in required:
        if field not in unidad:
            return f"Campo requerido '{field}' no encontrado"

    if unidad.get("sentimiento") not in SENTIMIENTOS_VALIDOS:
        return f"Sentimiento inválido: {unidad.get('sentimiento')}"

    if not isinstance(unidad.get("intensidad"), (int, float)):
        return f"Intensidad debe ser numérica: {unidad.get('intensidad')}"

    intensidad = int(unidad["intensidad"])
    if intensidad < 1 or intensidad > 5:
        return f"Intensidad fuera de rango 1-5: {intensidad}"

    # Validar coherencia dimensión → categoria_padre
    dimension = unidad.get("dimension", "")
    cat_padre = unidad.get("categoria_padre", "")
    if dimension and dimension in taxonomia and cat_padre:
        expected_cat = taxonomia[dimension]
        if cat_padre == "none" and expected_cat != "none":
            unidad["categoria_padre"] = expected_cat
        elif cat_padre != expected_cat and expected_cat != "none" \
                and cat_padre != "none":
            logger.debug(
                f"Corrigiendo categoria_padre '{cat_padre}' → "
                f"'{expected_cat}' para dimensión '{dimension}'"
            )
            unidad["categoria_padre"] = expected_cat

    return None


def corregir_unidad(unidad: dict) -> dict:
    """Corrige defensivamente una unidad individual.

    Asegura: categoria_padre coherente, es_valido/motivo_invalidez sincronizados,
    intensidad en 1-5, sub_aspectos normalizados (max 5, lowercase, 50 chars).
    """
    unidad["intensidad"] = max(1, min(5, int(unidad.get("intensidad", 3))))

    if "es_valido" not in unidad:
        unidad["es_valido"] = True
    if not unidad.get("es_valido") and not unidad.get("motivo_invalidez"):
        unidad["motivo_invalidez"] = "Motivo no especificado"

    if unidad.get("es_valido") and unidad.get("motivo_invalidez"):
        unidad["motivo_invalidez"] = None

    sub = unidad.get("sub_aspectos", [])
    if isinstance(sub, list):
        sub = sub[:5]
        sub = [str(s).strip().lower()[:50] for s in sub if str(s).strip()]
        unidad["sub_aspectos"] = sub

    if "justificacion_sentimiento" not in unidad:
        unidad["justificacion_sentimiento"] = ""

    return unidad


def validar_respuesta_ia(respuesta: dict,
                         taxonomia: Dict[str, str]
                         ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valida y sanea la respuesta completa de DeepSeek.

    Retorna (respuesta_saneada, None) o (None, mensaje_error).
    Descarta unidades inválidas y re-numera secuencialmente.
    """
    if not isinstance(respuesta, dict):
        return None, "Respuesta no es un diccionario"

    if "unidades" not in respuesta or not isinstance(respuesta["unidades"], list):
        return None, "Campo 'unidades' ausente o no es lista"

    unidades_validas = []
    for i, unidad in enumerate(respuesta["unidades"]):
        unidad = corregir_unidad(unidad)
        err = validar_unidad(unidad, taxonomia)
        if err:
            logger.debug(f"Unidad {i} inválida ({err}), descartando")
            continue
        unidad["orden"] = len(unidades_validas) + 1
        unidades_validas.append(unidad)

    if not unidades_validas:
        return None, "Todas las unidades son inválidas"

    return {
        "unidades": unidades_validas,
        "metadata": respuesta.get("metadata", {})
    }, None
