"""
TESTS — prompts_cualitativo (lib/prompts_cualitativo.py)

Tests unitarios para la construcción de prompts (system + user) enviados a DeepSeek.
Cubre: build_system_prompt, build_user_prompt, PROMPT_VERSION.

Alcance Fase 1 (FM-009 start): esqueleto con ≥1 test por función clave.
Cobertura completa (casos borde, reglas de contexto NPS, CSAT faltante) en Fase 2.
"""

import sys
import unittest
from pathlib import Path

# Asegurar que el directorio scripts/ está en sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.prompts_cualitativo import (
    PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
)


class TestPromptVersion(unittest.TestCase):
    """Tests de la constante PROMPT_VERSION (invalida caché IA)."""

    def test_prompt_version_es_string_no_vacio(self):
        """PROMPT_VERSION es un string no vacío (usado como cache-key)."""
        self.assertIsInstance(PROMPT_VERSION, str)
        self.assertGreater(len(PROMPT_VERSION), 0)

    def test_prompt_version_bumpeada_tras_fm002(self):
        """FM-002: PROMPT_VERSION debe reflejar la redacción pre-LLM (v8+)."""
        # Tras FM-002, la versión debe incluir 'redaccion-pre-llm' o ser > v7.
        self.assertTrue(
            "redaccion" in PROMPT_VERSION.lower() or PROMPT_VERSION > "v7",
            f"PROMPT_VERSION={PROMPT_VERSION} no refleja el bump de FM-002",
        )


class TestBuildSystemPrompt(unittest.TestCase):
    """Tests de build_system_prompt — system prompt con taxonomía inyectada."""

    def test_system_prompt_incluye_taxonomia(self):
        """El system prompt incluye las dimensiones de la taxonomía oficial."""
        taxonomia = {
            "Calidad de la enseñanza": "Académico",
            "Conexión Wi-Fi": "Tecnología",
        }
        categorias_padre = ["Académico", "Tecnología"]
        prompt = build_system_prompt(taxonomia, categorias_padre)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        # Las dimensiones se inyectan en el prompt.
        self.assertIn("Calidad de la enseñanza", prompt)
        self.assertIn("Conexión Wi-Fi", prompt)
        # Las categorías padre aparecen como headers.
        self.assertIn("Académico", prompt)
        self.assertIn("Tecnología", prompt)


class TestBuildUserPrompt(unittest.TestCase):
    """Tests de build_user_prompt — user prompt por comentario."""

    def test_user_prompt_incluye_comentario_y_nps(self):
        """El user prompt incluye el comentario y el score NPS del estudiante."""
        comentario = "los profesores son excelentes"
        prompt = build_user_prompt(
            comentario=comentario,
            nps_score=10,
            csat_ratings={"Calidad de la enseñanza": "Totalmente satisfecho"},
            id_encuesta="R123",
        )
        self.assertIsInstance(prompt, str)
        self.assertIn(comentario, prompt)
        self.assertIn("10", prompt)  # NPS score
        self.assertIn("Promotor", prompt)  # segmento NPS para score 10
        self.assertIn("R123", prompt)  # id_encuesta

    def test_user_prompt_segmento_detractor(self):
        """NPS 0-6 → segmento 'Detractor' en el prompt."""
        prompt = build_user_prompt(
            comentario="mal servicio",
            nps_score=3,
            csat_ratings={},
            id_encuesta="R456",
        )
        self.assertIn("Detractor", prompt)
        self.assertIn("3", prompt)


if __name__ == "__main__":
    unittest.main()
