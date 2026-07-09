"""
IA CACHE — Caché persistente para resultados de análisis cualitativo.

La clave es un hash SHA-256 de (comentario + nps_score + csat_ratings + prompt_version).
Esto evita re-llamar a la API en builds subsiguientes si el CSV no cambió.
"""

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import os

CACHE_ENABLED = os.environ.get("IA_CUALITATIVO_CACHE", "1") == "1"

logger = logging.getLogger(__name__)


class CacheManager:
    """Caché persistente en JSON para resultados de análisis cualitativo."""

    def __init__(self, cache_path: Path, save_every: int = 50,
                 prompt_version: str = ""):
        self.cache_path = Path(cache_path)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._save_counter = 0
        self._save_every = save_every
        self._prompt_version = prompt_version
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
                logger.info(
                    f"Caché IA cargada: {len(self._cache)} entradas "
                    f"desde {self.cache_path}"
                )
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
                  csat_ratings: Dict[str, str],
                  prompt_version: str = "") -> str:
        csat_sorted = json.dumps(csat_ratings, sort_keys=True, ensure_ascii=False)
        payload = f"{comentario}||{nps_score}||{csat_sorted}||{prompt_version}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, comentario: str, nps_score: int,
            csat_ratings: Dict[str, str]) -> Optional[Dict[str, Any]]:
        if not CACHE_ENABLED:
            return None
        key = self._make_key(comentario, nps_score, csat_ratings, self._prompt_version)
        with self._lock:
            entry = self._cache.get(key)
        if entry is None:
            return None
        if not isinstance(entry, dict) or "unidades" not in entry:
            return None
        return entry

    def set(self, comentario: str, nps_score: int,
            csat_ratings: Dict[str, str], result: Dict[str, Any]) -> None:
        if not CACHE_ENABLED:
            return
        key = self._make_key(comentario, nps_score, csat_ratings, self._prompt_version)
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
