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
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
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
DEFAULT_MAX_RPM = int(os.environ.get("IA_CUALITATIVO_MAX_RPM", "60"))
DEFAULT_TIMEOUT = int(os.environ.get("IA_CUALITATIVO_TIMEOUT", "60"))  # segundos
DEFAULT_MAX_RETRIES = 3
DEFAULT_WORKERS = int(os.environ.get("IA_CUALITATIVO_WORKERS", "15"))
CACHE_ENABLED = os.environ.get("IA_CUALITATIVO_CACHE", "1") == "1"


# ============================================================
# GESTOR DE CACHÉ
# ============================================================

class CacheManager:
    """Caché persistente en JSON para resultados de análisis cualitativo.

    La clave es un hash de (comentario + nps_score + csat_ratings ordenado).
    Esto evita re-llamar a la API en builds subsiguientes si el CSV no cambió.
    """

    def __init__(self, cache_path: Path, save_every: int = 50):
        self.cache_path = Path(cache_path)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._save_counter = 0
        self._save_every = save_every
        self._load()

    def _load(self) -> None:
        if not CACHE_ENABLED:
            with self._lock:
                self._cache = {}
            return
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    with self._lock:
                        self._cache = json.load(f)
                logger.info(f"Caché IA cargada: {len(self._cache)} entradas desde {self.cache_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Caché IA corrupta, ignorando: {e}")
                with self._lock:
                    self._cache = {}
        else:
            with self._lock:
                self._cache = {}

    def flush(self) -> None:
        """Guarda el caché a disco inmediatamente (thread-safe)."""
        if not CACHE_ENABLED:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                cache_copy = dict(self._cache)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_copy, f, ensure_ascii=False, separators=(",", ":"))
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
        with self._lock:
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
        should_save = False
        with self._lock:
            self._cache[key] = result
            self._save_counter += 1
            if self._save_counter >= self._save_every:
                should_save = True
                self._save_counter = 0
                cache_copy = dict(self._cache)
        if should_save:
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_copy, f, ensure_ascii=False, separators=(",", ":"))
            except OSError as e:
                logger.warning(f"No se pudo guardar caché IA: {e}")


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
        self._rate_lock = threading.Lock()
        self._usage_lock = threading.Lock()

    def _wait_rate_limit(self) -> None:
        """Rate limiting thread-safe: garantiza spacing mínimo entre calls globales."""
        if self._min_interval <= 0:
            return
        with self._rate_lock:
            elapsed = time.monotonic() - self._last_call_ts
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call_ts = time.monotonic()

    def chat_completion(self,
                        system_prompt: str,
                        user_prompt: str,
                        temperature: float = 0.1,
                        max_tokens: int = 1500) -> Dict[str, Any]:
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
                    # Acumular usage (thread-safe)
                    usage = data.get("usage", {})
                    with self._usage_lock:
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
        with self._usage_lock:
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


# ============================================================
# FILTRO PRE-DEEPSEEK — Detección de ruido sin IA
# ============================================================
# Basado en el análisis manual (analisis_nps_cualitativo.xlsx) + revisión
# de casos reportados por el usuario. Detecta comentarios inválidos evidentes
# sin llamar a la API, ahorrando tokens y mejorando la calidad del dashboard.

# Patrones regex de ruido
_RE_SOLO_PUNTUACION = re.compile(r'^[\.\-,_/;:!?*\s…ªº·•·–—\-\(\)\[\]\{\}]+$')
_RE_LETRA_REPETIDA = re.compile(r'^(.)\1{2,}$')  # 3+ repeticiones del mismo char
_RE_SOLO_NUMERO = re.compile(r'^\d+$')
_RE_PUNTUACION_REPETIDA = re.compile(r'^([.\-_…])\1{1,}$')  # "..", "---", "……"
# Ruido de teclado: 8+ consonantes seguidas (Sbdhdjsjxdjdjxhdbdjxdjejxjc)
_RE_RUIDO_TECLADO = re.compile(r'[bcdfghjklmnpqrstvwxyzñ]{8,}', re.IGNORECASE)
# "Solo repite la calificación": "Merece un 7", "Nota: 8/10", "Le doy 8"
_RE_REPITE_CALIFICACION = re.compile(
    r'^\s*(?:merece\s+un\s+\d+|nota\s*:?\s*\d+(?:/\d+)?|le\s+doy\s+\d+|'
    r'\d+\s*/\s*\d+|calific[oó]\s+(?:con|con\s+un)\s+\d+|punt[oó]n\s*:?\s*\d+)\s*\.?\s*$',
    re.IGNORECASE
)
# Palabra repetida 5+ veces ("me gustaaaaa" no, pero "me gusta me gusta me gusta" sí)
_RE_PALABRA_REPETIDA = re.compile(r'\b(\w{2,})\b(?:\s+\1){4,}', re.IGNORECASE)
# Carácter repetido 5+ veces dentro del texto ("gustaaaaaaaaa")
_RE_CHAR_REPETIDO_INTERNO = re.compile(r'(.)\1{6,}', re.IGNORECASE)

# Set de comentarios sin contexto (lowercase, sin puntuación final).
# Calibrado contra el análisis manual: TODOS fueron marcados como inválidos.
_RUIDO_SIN_CONTEXTO = {
    # Ruido corto
    "hola", "trash", "xd", "je", "jeje", "jaja", "jeej", "jajaja",
    "asdf", "pq", "xq", "noc", "hhjh", "test", "asdfg",
    "aaaa", "bbbb", "cccc", "xxxx", "zzzz", "kkkkk", "kkkk",
    "nada", "nose", "no se", "n/a", "n.a", "na", "null", "none",
    # Respuestas cortas genéricas (el manual las marca inválidas por falta de contexto)
    "si", "sí", "no", "ok", "muy buenas", "muy buenos", "normal",
    # NOTA: "bien", "bien.", "muy bien", "satisfecho", "calidad", "regular",
    # "está bien", "esta bien", "todo bien", "todo puede mejorar" son SI (van a _FRASES_CORTAS_VALIDAS)
    # Frases de evasión (el estudiante no quiere comentar)
    "sin comentarios", "sin comentario", "ningun comentario", "ningún comentario",
    "no hay comentarios", "no hay comentario", "no hay nada que decir",
    "sin nada que decir", "nada que decir", "nada que agregar",
    "no tengo comentarios", "no tengo comentario", "no deseo comentar",
    "no deseo", "no puedo escribir", "no puedo comentar",
    "no se", "no se xd", "no gracias", "y ya", "no se, está bien.",
    "las razones estan en mis respuestas",
    "debido a que yo estudio aquí", "debido a que el comien",
    # NOTA: "No me deja poner mi respuesta completa." NO está en ruido (v4):
    # es una queja sobre el sistema de encuesta → SI, la IA la clasifica
    # como Satisfacción estudiantil / negativo / intensidad 2.
    # "Porque si" y variantes (NO incluye "porque es buena" que es SI)
    "porque si", "proque si", "por que si",
    # Palabras sueltas sin contexto evaluativo
    "aura", "separenos", "sapo eres", "buenos quesitos", "creencia de poder",
    "peru es clave", "es una universidad", "muy buenos mm",
    # Frases coloquiales/filosóficas sin dimensión específica (calibrado v3)
    "piola p", "ta bien", "lindo", "nadie es perfecto",
    "no conozco muchos de sus servicios.", "no conozco muchos de sus servicios",
}

# Set de palabras/frases cortas que SÍ son válidas y se envían a la IA.
# Calibrado contra el análisis manual v3: TODAS fueron marcadas como válidas
# y la IA les asignó una dimensión coherente.
_FRASES_CORTAS_VALIDAS = {
    # Evaluativas claras (1 palabra) → IA clasifica como Satisfacción estudiantil
    "bien", "bien.", "muy bien", "satisfecho", "regular", "calidad",
    "debe mejorar", "es completa",
    # "Porque es buena" → SI (Satisfacción estudiantil)
    "porque es buena",
    # Frases evaluativas cortas (2-3 palabras) → IA clasifica
    "todo es bueno", "todo muy adecuado", "muchos alumnos",
    "siempre recomendaría", "8/10 buena universidad",
    "todo bien", "todo puede mejorar",
    "esta bien", "está bien",
    "buen servicio", "me gusta", "no me gusta",
    "dependiendo de la carrera",  # → La carrera (v3: SI)
    "las demás carreras no se",   # → La carrera (v3: SI)
    # Palabras evaluativas aisladas
    "bueno", "buena", "malo", "mala", "cool", "nice", "wow",
    "aceptable", "buena.", "bueno.",
    "linda", "feo", "fea", "excelente", "pesimo", "pésimo",
    "increible", "increíble", "horrible", "genial",
}


def _es_ruido_pre_filtro(comentario: str) -> Tuple[bool, Optional[str]]:
    """Detecta si un comentario es ruido evidente sin necesidad de IA.

    Calibrado contra el análisis manual + casos reportados por el usuario.
    Retorna (es_ruido, motivo_invalidez).

    Criterios (en orden de especificidad):
      1. Vacío → "Respuesta vacía"
      2. Solo puntuación/símbolos → "Caracter suelto sin significado"
      3. Puntuación repetida (.., ---, …) → "Caracter suelto sin significado"
      4. Letra repetida 3+ veces → "Ruido/Sin sentido"
      5. Char repetido 7+ veces interno ("gustaaaaaaa") → "Ruido/Sin sentido"
      6. Solo números → "Caracter suelto sin significado"
      7. Solo repite la calificación ("Merece un 7") → "Solo repite la calificación"
      8. Palabra/frase corta válida → NO filtrar
      9. 1 solo char alfanumérico → "Caracter suelto sin significado"
     10. Set explícito de ruido → "Ruido/Sin sentido"
     11. 1 solo tipo de char alfanumérico repetido → "Ruido/Sin sentido"
     12. Ruido de teclado (8+ consonantes seguidas) → "Ruido/Sin sentido"
     13. Ratio consonante/vocal alto (≥ 0.7) con longitud ≥ 8 → "Ruido/Sin sentido"
     14. Palabra repetida 5+ veces → "Ruido/Sin sentido"
     15. Frase corta genérica no evaluativa (≤ 2 palabras) → "Ruido/Sin sentido"

    NO filtra:
      - Frases evaluativas claras ("Lindo", "Ta bien", "Piola p").
      - Comentarios con 3+ palabras que podrían tener contexto.
    """
    if not comentario or not comentario.strip():
        return True, "Respuesta vacía"

    c = comentario.strip()
    c_lower = c.lower().rstrip('.!,:')
    c_lower_full = c.lower().strip()

    # 1. Solo puntuación/símbolos
    if _RE_SOLO_PUNTUACION.match(c):
        return True, "Caracter suelto sin significado"

    # 2. Puntuación repetida (.., ---, ………)
    if _RE_PUNTUACION_REPETIDA.match(c):
        return True, "Caracter suelto sin significado"

    # 3. Letra repetida 3+ veces (aaaa, lllll, jjjj)
    if _RE_LETRA_REPETIDA.match(c) and len(c) >= 3:
        return True, "Ruido/Sin sentido"

    # 4. Char repetido 7+ veces interno ("gustaaaaaaa", "AAAAAAAAA")
    #    PERO solo filtrar si el texto normalizado (colapsando repeticiones)
    #    es muy corto. "me gustaaaaaaaaa..." → normalizado = "me gusta" (válido, IA corrige).
    #    "aaaaaaaaaaaa" → normalizado = "a" (ruido, filtrar).
    if _RE_CHAR_REPETIDO_INTERNO.search(c):
        # Normalizar: colapsar secuencias de 7+ chars repetidos a 1 solo
        c_norm = _RE_CHAR_REPETIDO_INTERNO.sub(r'\1', c)
        alnum_norm = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ]', '', c_norm)
        if len(alnum_norm) < 4:
            return True, "Ruido/Sin sentido"
        # Si el texto normalizado tiene ≥ 4 chars alfanuméricos, enviar a IA
        # (ej. "me gustaaaaaaaaa" → "me gusta" → la IA corregirá).

    # 5. Solo números (8, 10, 2025)
    if _RE_SOLO_NUMERO.match(c):
        return True, "Caracter suelto sin significado"

    # 6. "Solo repite la calificación" ("Merece un 7", "Nota: 8/10")
    if _RE_REPITE_CALIFICACION.match(c):
        return True, "Solo repite la calificación"

    # 7. Frase corta válida → NO filtrar (enviar a IA)
    if c_lower in _FRASES_CORTAS_VALIDAS:
        return False, None

    # 8. Extraer solo caracteres alfanuméricos
    alnum = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ]', '', c)
    if len(alnum) < 2:
        # Solo 1 char alfanumérico ("J", "h", "a", "O", "H", "D", etc.)
        return True, "Caracter suelto sin significado"

    # 9. Set explícito de ruido (lowercase, con y sin puntuación final)
    if c_lower in _RUIDO_SIN_CONTEXTO or c_lower_full in _RUIDO_SIN_CONTEXTO:
        return True, "Ruido/Sin sentido"

    # 10. 1 solo tipo de char alfanumérico repetido ("aaaa.", ".aaa.")
    alnum_chars = set(alnum.lower())
    if len(alnum_chars) == 1 and len(alnum) >= 3:
        return True, "Ruido/Sin sentido"

    # 11. Ruido de teclado: 8+ consonantes seguidas
    if _RE_RUIDO_TECLADO.search(c):
        return True, "Ruido/Sin sentido"

    # 12. Ratio consonante/vocal alto (ruido de teclado con vocales intercaladas)
    #     "hydrruhf ytghi utghi" → 18 chars, 14 consonantes, ratio 0.78
    c_clean = re.sub(r'[^a-zA-Záéíóúñ]', '', c_lower)
    if len(c_clean) >= 8:
        consonantes = sum(1 for ch in c_clean if ch in 'bcdfghjklmnpqrstvwxyzñ')
        ratio = consonantes / len(c_clean) if c_clean else 0
        if ratio >= 0.75:
            return True, "Ruido/Sin sentido"

    # 13. Palabra repetida 5+ veces
    if _RE_PALABRA_REPETIDA.search(c_lower):
        return True, "Ruido/Sin sentido"

    # NOTA: La regla "frase corta genérica ≤ 2 palabras" fue eliminada (v3) porque
    # generaba falsos positivos con frases como "Buenas instalaciones", "Lejania",
    # "Mas edificios", "Demasiada gente", "El prestigio", "Networking" que el
    # análisis manual marcó como SI (la IA las clasifica a una dimensión específica).
    # Las frases cortas inválidas ya están en el set _RUIDO_SIN_CONTEXTO explícitamente.

    return False, None


def _generar_unidad_ruido(comentario: str, motivo: str) -> Dict[str, Any]:
    """Genera una unidad inválida placeholder para comentarios de ruido.
    No llama a la API. Compatible con el schema de salida de DeepSeek.
    """
    return {
        "unidades": [{
            "orden": 1,
            "texto": comentario[:100],
            "es_valido": False,
            "motivo_invalidez": motivo,
            "sentimiento": "Neutro",
            "intensidad": 1,
            "justificacion_sentimiento": f"Filtrado pre-IA (sin llamada a DeepSeek): {motivo}",
            "dimension": "Pendiente de Clasificación",
            "categoria_padre": "Pendiente de Clasificación",
            "es_mencion_mejora": False,
            "es_salvavidas": False,
            "dimension_evaluada_rating": None,
            "dimension_evaluada_score": None,
            "sub_aspectos": [],
        }]
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
    ruido_filtrado = 0

    total_rows = len(df_sent)
    workers = DEFAULT_WORKERS
    logger.info(
        f"Iniciando análisis IA de {total_rows} comentarios con DeepSeek "
        f"(modelo: {client.model}, {workers} workers paralelos, timeout={client.timeout}s)."
    )

    # ── PRE-COLECCIONAR filas válidas ────────────────────────────
    # Validamos todo antes de lanzar threads para que el ThreadPoolExecutor
    # solo procese work items limpios.
    tasks: List[Tuple[Any, str, int, str, str, str, str, str, Dict[str, str]]] = []
    for idx, row in df_sent.iterrows():
        # Validar comentario
        comentario_val = row["comentario"]
        if _pd is not None and _pd.isna(comentario_val):
            continue
        if comentario_val is None:
            continue
        comentario = str(comentario_val).strip()
        if not comentario or comentario.lower() == "nan":
            continue

        # Validar nps_score
        nps_val = row["nps_score"]
        if _pd is not None and _pd.isna(nps_val):
            continue
        try:
            nps = int(nps_val)
        except (ValueError, TypeError):
            logger.warning(f"Skip fila {idx}: nps_score inválido = {nps_val!r}")
            continue

        res_id = str(row.get("ID", f"R_{idx}"))
        facultad = str(row.get("facultad", ""))
        carrera = str(row.get("carrera", ""))
        ciclo = str(row.get("ciclo", ""))
        satisfaccion_global = str(row.get("satisfaccion_global", "No respondido"))

        # Extraer CSAT ratings del row
        csat_ratings: Dict[str, str] = {}
        for dim, col in csat_columns_map.items():
            if col in row.index:
                val = row[col]
                if val and str(val).strip() and str(val).strip() in RATING_TO_SCORE:
                    csat_ratings[dim] = str(val).strip()

        # ── FILTRO PRE-DEEPSEEK ──────────────────────────────────
        # Detecta ruido evidente (puntuación sola, 1 letra, "hola", etc.)
        # sin llamar a la API. Genera unidad inválida placeholder directo.
        es_ruido, motivo_ruido = _es_ruido_pre_filtro(comentario)
        if es_ruido:
            ruido_filtrado += 1
            resultado_ruido = _generar_unidad_ruido(comentario, motivo_ruido)
            seg_nps_ruido = "Promotor" if nps >= 9 else ("Pasivo" if nps >= 7 else "Detractor")
            for u in resultado_ruido["unidades"]:
                total_unidades += 1
                errores += 1
                dataset_cualitativo.append({
                    "id_encuesta": res_id,
                    "id_fragmento": f"{res_id}_01",
                    "facultad": facultad,
                    "carrera": carrera,
                    "ciclo": ciclo,
                    "nps_score": nps,
                    "segmento_nps": seg_nps_ruido,
                    "satisfaccion_global": satisfaccion_global,
                    "texto": u["texto"],
                    "aspecto_normalizado": u["dimension"],
                    "dimension": u["dimension"],
                    "categoria_padre": u["categoria_padre"],
                    "sub_aspectos": u.get("sub_aspectos", []),
                    "sentimiento": u["sentimiento"].lower(),
                    "sentimiento_display": u["sentimiento"],
                    "intensidad": u["intensidad"],
                    "es_valido": False,
                    "motivo_invalidez": motivo_ruido,
                    "es_mencion_mejora": False,
                    "es_salvavidas": False,
                    "justificacion_sentimiento": u["justificacion_sentimiento"],
                    "dimension_evaluada_rating": None,
                    "dimension_evaluada_score": None,
                    "confianza_sentimiento": 1.0,
                    "motor": "deepseek",
                    "comentario_original": comentario,
                })
            continue  # NO se añade a tasks, no se llama a la API

        # Verificar caché antes de enviar a la API
        if cache is not None and cache.get(comentario, nps, csat_ratings) is not None:
            cache_hits += 1
        else:
            cache_misses += 1

        tasks.append((row, comentario, nps, res_id, facultad, carrera, ciclo,
                      satisfaccion_global, csat_ratings))

    total_valid = len(tasks)
    logger.info(
        f"Filas a procesar con IA: {total_valid} (cache hits pre-existentes: {cache_hits}, "
        f"ruido filtrado sin IA: {ruido_filtrado}). "
        f"Estimado: ~{total_valid * 30 / workers / 60:.0f} min con {workers} workers."
    )

    # ── FUNCIÓN WORKER (ejecutada en thread pool) ────────────────
    def _process_one(task_args):
        (_row, _comentario, _nps, _res_id, _facultad, _carrera, _ciclo,
         _satisfaccion_global, _csat_ratings) = task_args
        _resultado = analizar_comentario(
            comentario=_comentario,
            nps_score=_nps,
            csat_ratings=_csat_ratings,
            taxonomia=taxonomia,
            categorias_padre=categorias_padre,
            client=client,
            cache=cache,
            id_encuesta=_res_id,
        )
        return _res_id, _comentario, _nps, _facultad, _carrera, _ciclo, \
               _satisfaccion_global, _resultado

    # ── EJECUCIÓN PARALELA ───────────────────────────────────────
    completed = 0
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_process_one, t): t for t in tasks}
            for future in as_completed(futures):
                try:
                    res_id, comentario, nps, facultad, carrera, ciclo, \
                        satisfaccion_global, resultado = future.result()
                except Exception as e:
                    logger.error(f"Error en worker: {e}")
                    completed += 1
                    continue

                completed += 1
                total_comentarios += 1
                seg_nps = "Promotor" if nps >= 9 else ("Pasivo" if nps >= 7 else "Detractor")

                # Expander a filas por unidad
                for u in resultado["unidades"]:
                    total_unidades += 1
                    if not u.get("es_valido", True):
                        errores += 1
                    dataset_cualitativo.append({
                        "id_encuesta": res_id,
                        "id_fragmento": f"{res_id}_{u['orden']:02d}",
                        "facultad": facultad,
                        "carrera": carrera,
                        "ciclo": ciclo,
                        "nps_score": nps,
                        "segmento_nps": seg_nps,
                        "satisfaccion_global": satisfaccion_global,
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

                if completed % progress_every == 0:
                    logger.info(
                        f"Progreso IA: {completed}/{total_valid} comentarios "
                        f"({total_unidades} unidades, {cache_hits} cache hits, "
                        f"{errores} inválidas, {client.usage['total_tokens']} tokens)."
                    )
    finally:
        # Guardar caché al final (o si se cancela a mitad)
        if cache is not None:
            cache.flush()

    metadata = {
        "motor": "deepseek",
        "model": client.model,
        "workers": workers,
        "total_comentarios": total_comentarios,
        "total_unidades": total_unidades,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "ruido_filtrado_sin_ia": ruido_filtrado,
        "unidades_invalidas": errores,
        "usage": client.usage,
        "promedio_unidades_por_comentario": (
            total_unidades / total_comentarios if total_comentarios else 0
        ),
    }
    logger.info(
        f"Análisis IA completo: {total_comentarios} comentarios → {total_unidades} unidades "
        f"({cache_hits} cache hits, {ruido_filtrado} ruido filtrado sin IA, "
        f"{errores} inválidas, {client.usage['total_tokens']} tokens totales, {workers} workers)."
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
