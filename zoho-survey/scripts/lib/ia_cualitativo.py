"""
IA CUALITATIVO — Motor de análisis cualitativo basado en DeepSeek.

Reemplaza a los 3 módulos locales (segmentacion_nps.py, aspect_extraction.py,
sentiment_engine.py) por una única llamada a DeepSeek que ejecuta las 5 tareas
en conjunto, con coherencia de contexto y reglas de sesgo NPS aplicadas.

Diseño:
  - Cliente DeepSeek (OpenAI-compatible) con reintentos y rate limiting.
  - Caché persistente por hash(comentario + contexto) para evitar re-llamadas.
  - Validación de salida contra schema JSON.
  - Fallback opcional al pipeline local si la API falla (feature flag).

Uso principal (integrado en build_json.py):
  from lib.ia_cualitativo import analizar_dataset_cualitativo
  dataset = analizar_dataset_cualitativo(
      df_sent=df_sent,
      taxonomia=CATEGORIA_DIMENSION_PREGRADO,
      cache_path=BASE_DIR / "ia_cache.json",
  )

Variables de entorno:
  - DEEPSEEK_API_KEY (obligatorio para modo IA; si ausente, hace fallback al
    pipeline local con un warning).
  - IA_CUALITATIVO_MODEL (opcional, default "deepseek-chat").
  - IA_CUALITATIVO_MAX_RPM (opcional, default 50).
  - IA_CUALITATIVO_CACHE (opcional, "1" para habilitar caché, "0" para deshabilitar).
"""

import os
import json
import time
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

# pandas se usa solo para cleaning defensivo en analizar_dataset_cualitativo.
# Si no está disponible (entorno mínimo), los checks del bucle usan fallback.
try:
    import pandas as _pd
except ImportError:
    _pd = None

from .prompts_cualitativo import (
    build_system_prompt,
    build_user_prompt,
    OUTPUT_SCHEMA,
    RATING_TO_SCORE,
    rating_to_score,
)

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("IA_CUALITATIVO_MODEL", "deepseek-chat")
DEFAULT_MAX_RPM = int(os.environ.get("IA_CUALITATIVO_MAX_RPM", "50"))
DEFAULT_TIMEOUT = 90  # segundos
DEFAULT_MAX_RETRIES = 4
CACHE_ENABLED = os.environ.get("IA_CUALITATIVO_CACHE", "1") == "1"


# ============================================================
# GESTOR DE CACHÉ
# ============================================================

class CacheManager:
    """Caché persistente en JSON para resultados de análisis cualitativo.

    La clave es un hash de (comentario + nps_score + csat_ratings ordenado).
    Esto evita re-llamar a la API en builds subsiguientes si el CSV no cambió.
    """

    def __init__(self, cache_path: Path):
        self.cache_path = Path(cache_path)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not CACHE_ENABLED:
            self._cache = {}
            return
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Caché IA cargada: {len(self._cache)} entradas desde {self.cache_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Caché IA corrupta, ignorando: {e}")
                self._cache = {}
        else:
            self._cache = {}

    def _save(self) -> None:
        if not CACHE_ENABLED:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, separators=(",", ":"))
        except OSError as e:
            logger.warning(f"No se pudo guardar caché IA: {e}")

    @staticmethod
    def _make_key(comentario: str, nps_score: int,
                  csat_ratings: Dict[str, str]) -> str:
        # Ordenar csat_ratings para determinismo
        csat_sorted = json.dumps(csat_ratings, sort_keys=True, ensure_ascii=False)
        payload = f"{comentario}||{nps_score}||{csat_sorted}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, comentario: str, nps_score: int,
            csat_ratings: Dict[str, str]) -> Optional[Dict[str, Any]]:
        if not CACHE_ENABLED:
            return None
        key = self._make_key(comentario, nps_score, csat_ratings)
        entry = self._cache.get(key)
        if entry is None:
            return None
        # Validar que la entrada cacheada tenga la estructura esperada
        if not isinstance(entry, dict) or "unidades" not in entry:
            return None
        return entry

    def set(self, comentario: str, nps_score: int,
            csat_ratings: Dict[str, str], result: Dict[str, Any]) -> None:
        if not CACHE_ENABLED:
            return
        key = self._make_key(comentario, nps_score, csat_ratings)
        self._cache[key] = result
        self._save()


# ============================================================
# CLIENTE DEEPSEEK
# ============================================================

class DeepSeekClient:
    """Cliente mínimo para la API de DeepSeek (compatible OpenAI).

    Usa urllib de la stdlib para no añadir dependencias. Si el proyecto ya
    depende de `requests` o `openai`, se puede sustituir esta clase.
    """

    def __init__(self,
                 api_key: str,
                 model: str = DEFAULT_MODEL,
                 max_rpm: int = DEFAULT_MAX_RPM,
                 timeout: int = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES):
        self.api_key = api_key
        self.model = model
        self.max_rpm = max_rpm
        self.timeout = timeout
        self.max_retries = max_retries
        self._min_interval = 60.0 / max_rpm if max_rpm > 0 else 0
        self._last_call_ts = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def _wait_rate_limit(self) -> None:
        if self._min_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_call_ts
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_ts = time.monotonic()

    def chat_completion(self,
                        system_prompt: str,
                        user_prompt: str,
                        temperature: float = 0.1,
                        max_tokens: int = 2000) -> Dict[str, Any]:
        """Llama a DeepSeek y retorna la respuesta parseada como dict.

        Raises:
            RuntimeError: si todos los reintentos fallan.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        last_error: Optional[str] = None
        for attempt in range(1, self.max_retries + 1):
            self._wait_rate_limit()
            req = urllib_request.Request(
                DEEPSEEK_API_URL, data=body, headers=headers, method="POST"
            )
            try:
                with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    # Acumular usage
                    usage = data.get("usage", {})
                    self._total_input_tokens += usage.get("prompt_tokens", 0)
                    self._total_output_tokens += usage.get("completion_tokens", 0)
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                # 4xx no recuperable salvo 429
                if e.code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limit DeepSeek (429). Reintento {attempt}/{self.max_retries} en {wait}s.")
                    time.sleep(wait)
                    continue
                if 400 <= e.code < 500:
                    # Leer cuerpo para mensaje detallado
                    try:
                        err_body = e.read().decode("utf-8")
                        last_error = f"HTTP {e.code}: {err_body[:300]}"
                    except Exception:
                        pass
                    break  # no reintentar errores de cliente
                # 5xx: reintentar con backoff
                wait = 2 ** attempt
                logger.warning(f"Error {e.code} DeepSeek. Reintento {attempt}/{self.max_retries} en {wait}s.")
                time.sleep(wait)
            except URLError as e:
                last_error = f"URLError: {e.reason}"
                wait = 2 ** attempt
                logger.warning(f"Error de red DeepSeek: {e.reason}. Reintento {attempt}/{self.max_retries} en {wait}s.")
                time.sleep(wait)
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                last_error = f"Respuesta inesperada de DeepSeek: {e}"
                logger.warning(f"{last_error}. Reintento {attempt}/{self.max_retries}.")
                time.sleep(2 ** attempt)

        raise RuntimeError(f"DeepSeek falló tras {self.max_retries} intentos. Último error: {last_error}")

    @property
    def usage(self) -> Dict[str, int]:
        return {
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
        }


# ============================================================
# VALIDACIÓN DE SALIDA
# ============================================================

SENTIMIENTOS_VALIDOS = {"Positivo", "Negativo", "Neutro"}
MOTIVOS_INVALIDEZ_VALIDOS = {
    "Caracter suelto sin significado",
    "Ruido/Sin sentido",
    "Respuesta vacía",
    "Frase repetida en la respuesta",
    "Solo repite la calificación",
    "Respuesta genérica sin información específica",
    "Frase muy general sin contenido específico",
    "Frase incompleta sin sentido",
}


def _validar_unidad(u: Dict[str, Any],
                    taxonomia: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """Valida una unidad contra el schema. Retorna (ok, error_msg)."""
    if not isinstance(u, dict):
        return False, "Unidad no es dict"
    required = {"orden", "texto", "es_valido", "motivo_invalidez", "sentimiento",
                "intensidad", "justificacion_sentimiento", "dimension",
                "categoria_padre", "es_mencion_mejora", "es_salvavidas",
                "dimension_evaluada_rating", "dimension_evaluada_score",
                "sub_aspectos"}
    missing = required - set(u.keys())
    if missing:
        return False, f"Campos faltantes: {missing}"
    if not isinstance(u["orden"], int) or u["orden"] < 1:
        return False, "orden inválido"
    if not isinstance(u["texto"], str):
        return False, "texto no es string"
    if not isinstance(u["es_valido"], bool):
        return False, "es_valido no es bool"
    if u["motivo_invalidez"] is not None and not isinstance(u["motivo_invalidez"], str):
        return False, "motivo_invalidez inválido"
    if u["sentimiento"] not in SENTIMIENTOS_VALIDOS:
        return False, f"sentimiento inválido: {u['sentimiento']}"
    if not isinstance(u["intensidad"], int) or not (1 <= u["intensidad"] <= 5):
        return False, f"intensidad inválida: {u['intensidad']}"
    if not isinstance(u["dimension"], str):
        return False, "dimension no es string"
    if not isinstance(u["categoria_padre"], str):
        return False, "categoria_padre no es string"
    # Validar coherencia dimension → categoria_padre
    expected_cat = taxonomia.get(u["dimension"])
    if expected_cat is not None and u["categoria_padre"] != expected_cat:
        # Corregir automáticamente (defensivo)
        u["categoria_padre"] = expected_cat
    # Validar rating/score
    if u["dimension_evaluada_rating"] is not None and not isinstance(u["dimension_evaluada_rating"], str):
        return False, "dimension_evaluada_rating inválido"
    if u["dimension_evaluada_score"] is not None:
        if not isinstance(u["dimension_evaluada_score"], int) or not (0 <= u["dimension_evaluada_score"] <= 5):
            return False, f"dimension_evaluada_score inválido: {u['dimension_evaluada_score']}"
    if not isinstance(u["sub_aspectos"], list):
        return False, "sub_aspectos no es lista"
    return True, None


def _corregir_unidad(u: Dict[str, Any], taxonomia: Dict[str, str]) -> Dict[str, Any]:
    """Aplica correcciones defensivas a una unidad (no reválida, solo sanea)."""
    # Asegurar categoria_padre coherente
    expected_cat = taxonomia.get(u.get("dimension", ""))
    if expected_cat is not None:
        u["categoria_padre"] = expected_cat
    # Asegurar consistencia motivo_invalidez <-> es_valido
    if u.get("es_valido") is True:
        u["motivo_invalidez"] = None
    elif u.get("es_valido") is False and not u.get("motivo_invalidez"):
        u["motivo_invalidez"] = "Frase incompleta sin sentido"
    # Clamp intensidad
    try:
        u["intensidad"] = max(1, min(5, int(u.get("intensidad", 3))))
    except (TypeError, ValueError):
        u["intensidad"] = 3
    # Saneamiento sub_aspectos
    sa = u.get("sub_aspectos")
    if not isinstance(sa, list):
        u["sub_aspectos"] = []
    else:
        u["sub_aspectos"] = [str(x).lower()[:50] for x in sa if isinstance(x, str)][:5]
    return u


def validar_respuesta_ia(resp: Dict[str, Any],
                         taxonomia: Dict[str, str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Valida y sanea la respuesta de DeepSeek.

    Returns:
        (resp_sanada, None) si OK, (None, error_msg) si fatal.
    """
    if not isinstance(resp, dict):
        return None, "La respuesta no es un objeto JSON"
    unidades = resp.get("unidades")
    if not isinstance(unidades, list) or len(unidades) == 0:
        return None, "La respuesta no tiene 'unidades' o está vacía"
    sanadas = []
    for i, u in enumerate(unidades):
        u = _corregir_unidad(dict(u), taxonomia)
        ok, err = _validar_unidad(u, taxonomia)
        if not ok:
            logger.warning(f"Unidad {i+1} inválida ({err}). Se descarta.")
            continue
        sanadas.append(u)
    if not sanadas:
        return None, "Todas las unidades fueron descartadas por inválidas"
    # Re-numerar orden secuencial
    for i, u in enumerate(sanadas, 1):
        u["orden"] = i
    return {"unidades": sanadas}, None


# ============================================================
# FUNCIÓN PRINCIPAL: analizar un comentario
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

    Usa caché si está disponible. Si la API falla y no hay fallback, devuelve
    una unidad placeholder no válida (para no romper el pipeline).
    """
    # 1. Intentar caché
    if cache is not None:
        cached = cache.get(comentario, nps_score, csat_ratings)
        if cached is not None:
            logger.debug(f"Cache hit para {id_encuesta}")
            return cached

    # 2. Construir prompts
    system_prompt = build_system_prompt(taxonomia, categorias_padre)
    user_prompt = build_user_prompt(comentario, nps_score, csat_ratings, id_encuesta)

    # 3. Llamar a DeepSeek
    try:
        raw_resp = client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=2000,
        )
    except RuntimeError as e:
        logger.error(f"DeepSeek falló para {id_encuesta}: {e}")
        # Devolver unidad placeholder no válida
        placeholder = {
            "unidades": [{
                "orden": 1,
                "texto": comentario[:100],
                "es_valido": False,
                "motivo_invalidez": "Error de API (fallback)",
                "sentimiento": "Neutro",
                "intensidad": 1,
                "justificacion_sentimiento": f"DeepSeek falló: {str(e)[:100]}",
                "dimension": "Pendiente de Clasificación",
                "categoria_padre": "Pendiente de Clasificación",
                "es_mencion_mejora": False,
                "es_salvavidas": False,
                "dimension_evaluada_rating": None,
                "dimension_evaluada_score": None,
                "sub_aspectos": [],
            }]
        }
        return placeholder

    # 4. Validar y sanear
    sanada, err = validar_respuesta_ia(raw_resp, taxonomia)
    if sanada is None:
        logger.warning(f"Respuesta IA inválida para {id_encuesta}: {err}")
        return {
            "unidades": [{
                "orden": 1,
                "texto": comentario[:100],
                "es_valido": False,
                "motivo_invalidez": "Respuesta IA inválida",
                "sentimiento": "Neutro",
                "intensidad": 1,
                "justificacion_sentimiento": f"Validación falló: {err}",
                "dimension": "Pendiente de Clasificación",
                "categoria_padre": "Pendiente de Clasificación",
                "es_mencion_mejora": False,
                "es_salvavidas": False,
                "dimension_evaluada_rating": None,
                "dimension_evaluada_score": None,
                "sub_aspectos": [],
            }]
        }

    # 5. Guardar en caché
    if cache is not None:
        cache.set(comentario, nps_score, csat_ratings, sanada)

    return sanada


# ============================================================
# FUNCIÓN DE ALTO NIVEL: analizar todo el dataset (reemplaza 3 módulos)
# ============================================================

def analizar_dataset_cualitativo(
    df_sent: Any,  # DataFrame con columnas: comentario, nps_score, facultad, carrera, ciclo, satisfaccion_global, ID, + columnas CSAT por dimensión
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],  # {dimension: nombre_columna_csv}
    cache_path: Optional[Path] = None,
    progress_every: int = 25,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Analiza cualitativamente todo el dataset de comentarios NPS.

    Reemplaza el bloque de build_json.py que llama a fragmentar_comentario_nps +
    procesar_opinion_unit + analizar_sentimiento_intensidad.

    Args:
        df_sent: DataFrame filtrado (comentario y nps_score no nulos).
        taxonomia: dict {dimension: categoria_padre}.
        csat_columns_map: dict {dimension: nombre_columna_en_df} para extraer ratings.
        cache_path: ruta del archivo de caché. None para deshabilitar.
        progress_every: loguear progreso cada N comentarios.

    Returns:
        (dataset_cualitativo, metadata) donde:
        - dataset_cualitativo: lista de dicts (uno por unidad) compatible con
          el schema de dataset_cualitativo.json + campos IA adicionales.
        - metadata: {stats, usage, errores, total_comentarios, total_unidades}.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY no configurada. Establécela como GitHub Actions Secret "
            "o variable de entorno local. El pipeline local legacy está disponible "
            "como fallback configurando IA_CUALITATIVO_FALLBACK=1."
        )

    client = DeepSeekClient(api_key=api_key)
    cache = CacheManager(cache_path) if cache_path else None
    categorias_padre = sorted(set(taxonomia.values()))

    # ── CLEANING DEFENSIVO ──────────────────────────────────────
    # Garantiza que df_sent no tenga NaN en nps_score ni comentarios
    # vacíos, independientemente del cleaning upstream en build_json.py.
    # Esto es crítico porque build_json.py puede añadir columnas CSAT
    # vía `df_sent[col] = df[col]` que en algunos casos de pandas
    # SettingWithCopyWarning puede interferir con el dropna previo.
    if _pd is not None:
        try:
            df_sent = df_sent.copy()
            df_sent["nps_score"] = _pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"]).reset_index(drop=True)
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            # Filtrar comentarios vacíos o que sean solo whitespace
            df_sent = df_sent[df_sent["comentario"].str.strip() != ""]
            # Filtrar el string "nan" que aparece cuando str(NaN) se cuela
            df_sent = df_sent[df_sent["comentario"].str.strip().str.lower() != "nan"]
        except Exception as clean_err:
            logger.warning(f"Cleaning defensivo falló (continuando con df original): {clean_err}")

    dataset_cualitativo: List[Dict[str, Any]] = []
    total_comentarios = 0
    total_unidades = 0
    errores = 0
    cache_hits = 0
    cache_misses = 0

    total_rows = len(df_sent)
    logger.info(f"Iniciando análisis IA de {total_rows} comentarios con DeepSeek (modelo: {client.model}).")

    for idx, row in df_sent.iterrows():
        # Extraer y validar comentario (defensivo vs NaN y "nan" string)
        comentario_val = row["comentario"]
        if _pd is not None and _pd.isna(comentario_val):
            continue
        if comentario_val is None:
            continue
        comentario = str(comentario_val).strip()
        if not comentario or comentario.lower() == "nan":
            continue

        # Extraer y validar nps_score (defensivo vs NaN)
        nps_val = row["nps_score"]
        if _pd is not None and _pd.isna(nps_val):
            continue
        try:
            nps = int(nps_val)
        except (ValueError, TypeError):
            logger.warning(f"Skip fila {idx}: nps_score inválido = {nps_val!r}")
            continue

        total_comentarios += 1
        seg_nps = "Promotor" if nps >= 9 else ("Pasivo" if nps >= 7 else "Detractor")
        res_id = str(row.get("ID", f"R_{idx}"))

        # Extraer CSAT ratings del row
        csat_ratings: Dict[str, str] = {}
        for dim, col in csat_columns_map.items():
            if col in row.index:
                val = row[col]
                if val and str(val).strip() and str(val).strip() in RATING_TO_SCORE:
                    csat_ratings[dim] = str(val).strip()

        # Verificar caché antes de contar miss
        was_cached = cache is not None and cache.get(comentario, nps, csat_ratings) is not None
        if was_cached:
            cache_hits += 1
        else:
            cache_misses += 1

        # Analizar
        resultado = analizar_comentario(
            comentario=comentario,
            nps_score=nps,
            csat_ratings=csat_ratings,
            taxonomia=taxonomia,
            categorias_padre=categorias_padre,
            client=client,
            cache=cache,
            id_encuesta=res_id,
        )

        # Expander a filas por unidad
        for u in resultado["unidades"]:
            total_unidades += 1
            if not u.get("es_valido", True):
                errores += 1
            dataset_cualitativo.append({
                "id_encuesta": res_id,
                "id_fragmento": f"{res_id}_{u['orden']:02d}",
                "facultad": str(row.get("facultad", "")),
                "carrera": str(row.get("carrera", "")),
                "ciclo": str(row.get("ciclo", "")),
                "nps_score": nps,
                "segmento_nps": seg_nps,
                "satisfaccion_global": str(row.get("satisfaccion_global", "No respondido")),
                "texto": u["texto"],
                "aspecto_normalizado": u["dimension"],  # compat backward
                "dimension": u["dimension"],
                "categoria_padre": u["categoria_padre"],
                "sub_aspectos": u.get("sub_aspectos", []),
                "sentimiento": u["sentimiento"].lower(),  # minúsculas para compat
                "sentimiento_display": u["sentimiento"],  # display con mayúscula
                "intensidad": u["intensidad"],
                "es_valido": u.get("es_valido", True),
                "motivo_invalidez": u.get("motivo_invalidez"),
                "es_mencion_mejora": u.get("es_mencion_mejora", False),
                "es_salvavidas": u.get("es_salvavidas", False),
                "justificacion_sentimiento": u.get("justificacion_sentimiento", ""),
                "dimension_evaluada_rating": u.get("dimension_evaluada_rating"),
                "dimension_evaluada_score": u.get("dimension_evaluada_score"),
                "confianza_sentimiento": 1.0,  # placeholder para compat
                "motor": "deepseek",
                "comentario_original": comentario,
            })

        if total_comentarios % progress_every == 0:
            logger.info(
                f"Progreso IA: {total_comentarios}/{total_rows} comentarios "
                f"({total_unidades} unidades, {cache_hits} cache hits, {errores} inválidas, "
                f"{client.usage['total_tokens']} tokens)."
            )

    metadata = {
        "motor": "deepseek",
        "model": client.model,
        "total_comentarios": total_comentarios,
        "total_unidades": total_unidades,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "unidades_invalidas": errores,
        "usage": client.usage,
        "promedio_unidades_por_comentario": (
            total_unidades / total_comentarios if total_comentarios else 0
        ),
    }
    logger.info(
        f"Análisis IA completo: {total_comentarios} comentarios → {total_unidades} unidades "
        f"({cache_hits} cache hits, {errores} inválidas, {client.usage['total_tokens']} tokens totales)."
    )
    return dataset_cualitativo, metadata


# ============================================================
# FUNCIÓN DE INTEGRACIÓN CON build_json.py
# ============================================================

def generar_salidas_cualitativas_ia(
    df_sent: Any,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    cache_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Genera las dos salidas cualitativas (fragmentos_nps + dataset_cualitativo)
    en una sola pasada con DeepSeek, listas para escribir a JSON.

    Reemplaza al bloque de build_json.py que produce:
      - fragmentos_nps.json
      - dataset_cualitativo.json

    Args:
        df_sent: DataFrame con columnas comentario, nps_score, facultad, carrera,
                 ciclo, satisfaccion_global, ID + columnas CSAT por dimensión.
        taxonomia: dict {dimension: categoria_padre}.
        csat_columns_map: dict {dimension: nombre_columna_en_df_sent}.
        cache_path: ruta del caché IA (None para deshabilitar).

    Returns:
        (datos_fragmentos, dataset_cualitativo, metadata_para_json) donde:
        - datos_fragmentos: lista agrupada por encuesta (para fragmentos_nps.json).
        - dataset_cualitativo: lista plana por unidad (para dataset_cualitativo.json).
        - metadata_para_json: dict con stats para el campo "metadata" del JSON.
    """
    dataset_cualitativo, ia_metadata = analizar_dataset_cualitativo(
        df_sent=df_sent,
        taxonomia=taxonomia,
        csat_columns_map=csat_columns_map,
        cache_path=cache_path,
    )

    # Agrupar por id_encuesta para fragmentos_nps.json
    por_encuesta: Dict[str, Dict[str, Any]] = {}
    for item in dataset_cualitativo:
        eid = item["id_encuesta"]
        if eid not in por_encuesta:
            por_encuesta[eid] = {
                "id_encuesta": eid,
                "facultad": item["facultad"],
                "carrera": item["carrera"],
                "ciclo": item["ciclo"],
                "nps_score": item["nps_score"],
                "segmento_nps": item["segmento_nps"],
                "satisfaccion_global": item["satisfaccion_global"],
                "comentario_original": item["comentario_original"],
                "fragmentos": [],
            }
        por_encuesta[eid]["fragmentos"].append({
            "id_fragmento": item["id_fragmento"],
            "texto": item["texto"],
        })
    datos_fragmentos = list(por_encuesta.values())

    # Stats de sentimiento para metadata (compat con schema legacy)
    total = len(dataset_cualitativo)
    pos = sum(1 for d in dataset_cualitativo if d["sentimiento"] == "positivo")
    neg = sum(1 for d in dataset_cualitativo if d["sentimiento"] == "negativo")
    neu = sum(1 for d in dataset_cualitativo if d["sentimiento"] == "neutro")
    intensidad_prom = (
        sum(d["intensidad"] for d in dataset_cualitativo) / total if total else 0
    )
    validos = sum(1 for d in dataset_cualitativo if d.get("es_valido", True))

    metadata_para_json = {
        "version": "2.0",
        "motor": "deepseek",
        "model": ia_metadata["model"],
        "total_encuestas": len(datos_fragmentos),
        "total_fragmentos": total,
        "total_unidades_validas": validos,
        "total_unidades_invalidas": ia_metadata["unidades_invalidas"],
        "cache_hits": ia_metadata["cache_hits"],
        "cache_misses": ia_metadata["cache_misses"],
        "usage": ia_metadata["usage"],
        "promedio_unidades_por_comentario": round(
            ia_metadata["promedio_unidades_por_comentario"], 3
        ),
        "stats_sentimiento": {
            "total_opinion_units": total,
            "positivos": pos,
            "negativos": neg,
            "neutros": neu,
            "intensidad_promedio": round(intensidad_prom, 2),
            "confianza_promedio": 1.0,
        },
    }

    return datos_fragmentos, dataset_cualitativo, metadata_para_json
