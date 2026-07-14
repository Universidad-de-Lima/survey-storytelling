"""
IA VALIDACION — Validación y corrección de respuestas de DeepSeek.

Valida y corrige unidades individuales y respuestas completas de la API
de DeepSeek, asegurando consistencia de tipos, campos requeridos y
coherencia entre dimensiones y categorías padre.
"""

import logging
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .ia_filtro_ruido import SENTIMIENTOS_VALIDOS, MOTIVOS_INVALIDEZ_VALIDOS
from .io_helper import enmascarar_pii

logger = logging.getLogger(__name__)

PENDIENTE_CLASIFICACION = "Pendiente de Clasificación"
_DIMENSIONES_ESPECIALES = {PENDIENTE_CLASIFICACION, "none"}


def _normalizar_texto_clave(value: Any) -> str:
    """Normaliza texto para comparar variantes seguras sin cambiar el valor final."""
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value.strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def _normalizar_sentimiento(value: Any) -> Any:
    """Acepta variantes seguras de capitalización del set canónico."""
    if not isinstance(value, str):
        return value
    key = _normalizar_texto_clave(value)
    if key in SENTIMIENTOS_VALIDOS:
        return key
    return value


def _normalizar_intensidad(value: Any) -> Any:
    """Convierte números enviados como texto, sin corregir rangos inválidos."""
    if not isinstance(value, str):
        return value
    try:
        parsed = float(value.strip())
    except ValueError:
        return value
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _normalizar_pendiente(value: Any) -> Any:
    """Canonicaliza solo la pseudo-categoría Pendiente de Clasificación."""
    if _normalizar_texto_clave(value) == "pendiente de clasificacion":
        return PENDIENTE_CLASIFICACION
    return value


def _normalizar_unidad(unidad: dict) -> dict:
    """Normaliza variaciones de formato de DeepSeek antes de validar."""
    unidad["sentimiento"] = _normalizar_sentimiento(unidad.get("sentimiento"))
    if "intensidad" in unidad:
        unidad["intensidad"] = _normalizar_intensidad(unidad.get("intensidad"))
    unidad["dimension"] = _normalizar_pendiente(unidad.get("dimension", ""))
    unidad["categoria_padre"] = _normalizar_pendiente(unidad.get("categoria_padre", ""))
    return unidad


def _resumen_errores(errores: List[str]) -> str:
    """Resume errores de validación sin incluir texto libre de encuestados."""
    if not errores:
        return "Todas las unidades son inválidas"
    total = len(errores)
    counter = Counter(errores)
    muestras = [f"{count}x {msg}" for msg, count in counter.most_common(3)]
    unidad = "unidad descartada" if total == 1 else "unidades descartadas"
    return f"Todas las unidades son inválidas ({total} {unidad}: {'; '.join(muestras)})"


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
    if dimension not in taxonomia and dimension not in _DIMENSIONES_ESPECIALES:
        return f"Dimensión desconocida: {dimension}"

    if dimension in _DIMENSIONES_ESPECIALES:
        if cat_padre != dimension:
            return f"Categoría padre incoherente: {cat_padre}"
        return None

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

    Asegura: variantes canónicas de campos, es_valido/motivo_invalidez
    sincronizados, sub_aspectos normalizados (max 5, lowercase, 50 chars).
    No corrige intensidades fuera de rango: esas deben fallar validación.
    """
    unidad = _normalizar_unidad(unidad)

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
    errores_unidades: List[str] = []
    for i, unidad in enumerate(respuesta["unidades"]):
        if not isinstance(unidad, dict):
            err = "Unidad no es un dict"
            errores_unidades.append(err)
            logger.debug(f"Unidad {i} inválida ({err}), descartando")
            continue
        unidad = corregir_unidad(unidad)
        err = validar_unidad(unidad, taxonomia)
        if err:
            errores_unidades.append(err)
            logger.debug(f"Unidad {i} inválida ({err}), descartando")
            continue
        unidad["orden"] = len(unidades_validas) + 1
        # Redactar PII en campos de texto para evitar exposicion publica.
        # Aplica a texto del fragmento y justificacion del sentimiento.
        if "texto" in unidad and isinstance(unidad["texto"], str):
            unidad["texto"] = enmascarar_pii(unidad["texto"])
        if "justificacion_sentimiento" in unidad and isinstance(unidad["justificacion_sentimiento"], str):
            unidad["justificacion_sentimiento"] = enmascarar_pii(unidad["justificacion_sentimiento"])
        unidades_validas.append(unidad)

    if not unidades_validas:
        return None, _resumen_errores(errores_unidades)

    return {
        "unidades": unidades_validas,
        "metadata": respuesta.get("metadata", {})
    }, None
