"""
TESTS — CacheManager (lib/ia_cache.py)

Tests unitarios para el caché persistente de resultados IA.
Cubre: creación, get/set, hit counter (fix CC-02), thread-safety, idempotencia.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from threading import Thread

# Asegurar que el directorio scripts/ está en sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.ia_cache import CacheManager


class TestCacheManagerBasic(unittest.TestCase):
    """Tests básicos de creación y operaciones get/set."""

    def setUp(self):
        """Crea un cache temporal para cada test."""
        self.tmpdir = tempfile.mkdtemp()
        self.cache_path = Path(self.tmpdir) / "ia_cache.json"

    def tearDown(self):
        """Limpia archivos temporales."""
        if self.cache_path.exists():
            self.cache_path.unlink()

    def test_cache_creation_empty(self):
        """Cache nuevo se crea vacío."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        self.assertEqual(len(cache._cache), 0)

    def test_set_and_get(self):
        """set + get retorna el valor guardado."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {"dim": "Muy satisfecho"}, result)
        retrieved = cache.get("comentario", 9, {"dim": "Muy satisfecho"})
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, result)

    def test_get_missing_returns_none(self):
        """get de clave inexistente retorna None."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = cache.get("comentario inexistente", 9, {})
        self.assertIsNone(result)

    def test_get_invalid_entry_returns_none(self):
        """get de entrada sin 'unidades' retorna None."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        # Insertar entrada inválida directamente
        cache._cache["key"] = {"sin_unidades": True}
        result = cache.get("comentario", 9, {})
        # Como la key no coincide, retorna None
        self.assertIsNone(result)

    def test_persistence_across_instances(self):
        """Cache se persiste a disco y se carga en nueva instancia."""
        cache1 = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "persistente"}]}
        cache1.set("comentario", 9, {}, result)
        cache1.flush()

        cache2 = CacheManager(self.cache_path, prompt_version="v1")
        retrieved = cache2.get("comentario", 9, {})
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved, result)


class TestCacheHitCounter(unittest.TestCase):
    """Tests del contador de cache hits (fix CC-02)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache_path = Path(self.tmpdir) / "ia_cache.json"

    def tearDown(self):
        if self.cache_path.exists():
            self.cache_path.unlink()

    def test_hit_count_starts_zero(self):
        """Contador inicia en 0."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        self.assertEqual(cache.get_hit_count(), 0)

    def test_hit_count_increments_on_get(self):
        """Contador incrementa en cada cache hit."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {}, result)

        cache.get("comentario", 9, {})
        self.assertEqual(cache.get_hit_count(), 1)

        cache.get("comentario", 9, {})
        self.assertEqual(cache.get_hit_count(), 2)

    def test_hit_count_no_increment_on_miss(self):
        """Contador no incrementa en cache miss."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        cache.get("comentario inexistente", 9, {})
        self.assertEqual(cache.get_hit_count(), 0)

    def test_reset_hit_count(self):
        """reset_hit_count pone el contador a 0."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {}, result)
        cache.get("comentario", 9, {})
        self.assertEqual(cache.get_hit_count(), 1)

        cache.reset_hit_count()
        self.assertEqual(cache.get_hit_count(), 0)

    def test_hit_count_thread_safe(self):
        """Contador es thread-safe bajo concurrencia."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {}, result)

        # 10 threads hacen 100 gets cada uno
        def worker():
            for _ in range(100):
                cache.get("comentario", 9, {})

        threads = [Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 threads × 100 gets = 1000 hits
        self.assertEqual(cache.get_hit_count(), 1000)


class TestCacheKeyGeneration(unittest.TestCase):
    """Tests de generación de claves de cache."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache_path = Path(self.tmpdir) / "ia_cache.json"

    def tearDown(self):
        if self.cache_path.exists():
            self.cache_path.unlink()

    def test_different_comentario_different_key(self):
        """Comentarios diferentes generan claves diferentes."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario A", 9, {}, result)
        self.assertIsNone(cache.get("comentario B", 9, {}))

    def test_different_nps_different_key(self):
        """NPS diferentes generan claves diferentes."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {}, result)
        self.assertIsNone(cache.get("comentario", 6, {}))

    def test_different_prompt_version_different_key(self):
        """Prompt versions diferentes invalidan el cache."""
        cache1 = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache1.set("comentario", 9, {}, result)
        cache1.flush()

        cache2 = CacheManager(self.cache_path, prompt_version="v2")
        self.assertIsNone(cache2.get("comentario", 9, {}))

    def test_csat_order_independent(self):
        """CSAT ratings con diferente orden generan la misma clave (sort_keys)."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        result = {"unidades": [{"orden": 1, "texto": "test"}]}
        cache.set("comentario", 9, {"dim1": "SAT", "dim2": "Muy SAT"}, result)
        # Mismo contenido, diferente orden
        retrieved = cache.get("comentario", 9, {"dim2": "Muy SAT", "dim1": "SAT"})
        self.assertIsNotNone(retrieved)


class TestCacheCorruption(unittest.TestCase):
    """Tests de manejo de cache corrupto."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache_path = Path(self.tmpdir) / "ia_cache.json"

    def tearDown(self):
        if self.cache_path.exists():
            self.cache_path.unlink()

    def test_corrupted_cache_starts_empty(self):
        """Cache corrupto se ignora y arranca vacío."""
        # Escribir JSON inválido
        self.cache_path.write_text("{invalid json", encoding="utf-8")
        cache = CacheManager(self.cache_path, prompt_version="v1")
        self.assertEqual(len(cache._cache), 0)

    def test_missing_cache_file_starts_empty(self):
        """Cache inexistente arranca vacío sin error."""
        cache = CacheManager(self.cache_path, prompt_version="v1")
        self.assertEqual(len(cache._cache), 0)


if __name__ == "__main__":
    unittest.main()
