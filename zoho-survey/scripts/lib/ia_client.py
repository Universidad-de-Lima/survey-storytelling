"""
IA CLIENT — Cliente mínimo para la API de DeepSeek (OpenAI-compatible).

Usa urllib de la stdlib para no añadir dependencias externas.
Incluye reintentos con backoff, rate limiting y acumulación de
tokens de uso.
"""

import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("IA_CUALITATIVO_MODEL", "deepseek-v4-flash")
DEFAULT_MAX_RPM = int(os.environ.get("IA_CUALITATIVO_MAX_RPM", "60"))
DEFAULT_TIMEOUT = int(os.environ.get("IA_CUALITATIVO_TIMEOUT", "60"))
DEFAULT_MAX_RETRIES = 3
DEFAULT_WORKERS = int(os.environ.get("IA_CUALITATIVO_WORKERS", "15"))


class DeepSeekClient:
    """Cliente mínimo para la API de DeepSeek (compatible OpenAI)."""

    def __init__(self,
                 api_key: str,
                 model: str = DEFAULT_MODEL,
                 max_rpm: int = DEFAULT_MAX_RPM,
                 timeout: int = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 http_client=None):  # FM-009: inyectable para tests
        self.api_key = api_key
        self.model = model
        self.max_rpm = max_rpm
        self.timeout = timeout
        self.max_retries = max_retries
        # FM-009: http_client inyectable (default: urllib.request del módulo).
        # Permite inyectar un mock en tests sin parchear urllib globalmente.
        self._http_client = http_client if http_client is not None else urllib_request
        self._min_interval = 60.0 / max_rpm if max_rpm > 0 else 0
        self._last_call_ts = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._rate_lock = threading.Lock()
        self._usage_lock = threading.Lock()

    def _wait_rate_limit(self) -> None:
        """Rate limiting thread-safe: spacing mínimo entre calls globales."""
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
                # FM-009: usar self._http_client (urllib_request por default, mock en tests)
                with self._http_client.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    usage = data.get("usage", {})
                    with self._usage_lock:
                        self._total_input_tokens += usage.get("prompt_tokens", 0)
                        self._total_output_tokens += usage.get("completion_tokens", 0)
                    content = data["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        logger.error(
                            f"Contenido vacío de DeepSeek. Raw: {raw[:300]!r}"
                        )
                        raise json.JSONDecodeError("Contenido vacío", "", 0)
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        _match = re.search(r'(\{.*\})', content, re.DOTALL)
                        if _match:
                            try:
                                return json.loads(_match.group(1))
                            except json.JSONDecodeError:
                                pass
                        logger.error(
                            f"JSON inválido de DeepSeek. Content: {content[:500]!r}"
                        )
                        raise
            except HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code == 429:
                    wait = 2 ** attempt
                    logger.warning(
                        f"Rate limit (429). Reintento {attempt}/{self.max_retries} "
                        f"en {wait}s."
                    )
                    time.sleep(wait)
                    continue
                if 400 <= e.code < 500:
                    try:
                        err_body = e.read().decode("utf-8")
                        last_error = f"HTTP {e.code}: {err_body[:300]}"
                    except (UnicodeDecodeError, IOError):
                        pass
                    break
                wait = 2 ** attempt
                logger.warning(
                    f"Error {e.code}. Reintento {attempt}/{self.max_retries} "
                    f"en {wait}s."
                )
                time.sleep(wait)
            except URLError as e:
                last_error = f"URLError: {e.reason}"
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"URLError. Reintento {attempt}/{self.max_retries} "
                        f"en {wait}s."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"URLError tras {self.max_retries} reintentos: {e.reason}"
                    )
            except (json.JSONDecodeError, OSError, ValueError) as e:
                last_error = str(e)
                if "char 0" in str(e) or "Contenido vacío" in str(e):
                    break
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"Error: {e}. Reintento {attempt}/{self.max_retries} "
                        f"en {wait}s."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Error tras {self.max_retries} reintentos: {e}")

        raise RuntimeError(
            f"DeepSeek API no respondió tras {self.max_retries} reintentos: "
            f"{last_error}"
        )

    @property
    def usage(self) -> Dict[str, int]:
        with self._usage_lock:
            return {
                "input_tokens": self._total_input_tokens,
                "output_tokens": self._total_output_tokens,
                "total_tokens": self._total_input_tokens + self._total_output_tokens,
            }
