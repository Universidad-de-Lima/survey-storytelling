"""
TESTS — ia_cualitativo (lib/ia_cualitativo.py)

Tests unitarios para el orquestador del análisis cualitativo con DeepSeek.
Cubre: analizar_comentario, _placeholder, redacción pre-LLM (FM-002).

Alcance Fase 1 (FM-009 start): esqueleto con ≥1 test por función clave.
Cobertura completa (análisis de dataset, concurrencia, fallback) en Fase 2.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Asegurar que el directorio scripts/ está en sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.ia_cualitativo import analizar_comentario, _placeholder


class TestAnalizarComentarioRedaccionPreLLM(unittest.TestCase):
    """FM-002: verificar que el comentario se redacta ANTES de enviar a DeepSeek."""

    def test_comentario_con_pii_se_redacta_antes_del_llm(self):
        """FM-002: el user_prompt enviado al LLM no contiene el email original."""
        mock_client = MagicMock()
        # Simular respuesta válida de DeepSeek ( estructura esperada por validar_respuesta_ia)
        mock_client.chat_completion.return_value = {
            "unidades": [{
                "orden": 1,
                "texto": "mi correo es [CORREO ENMASCARADO]",
                "es_valido": True,
                "motivo_invalidez": None,
                "sentimiento": "neutro",
                "intensidad": 1,
                "justificacion_sentimiento": "test",
                "dimension": "Pendiente de Clasificación",
                "categoria_padre": "Pendiente de Clasificación",
                "es_mencion_mejora": False,
                "es_salvavidas": False,
                "dimension_evaluada_rating": None,
                "dimension_evaluada_score": None,
                "sub_aspectos": [],
            }]
        }

        comentario_con_pii = "mi correo es test@example.com y el profesor no responde"
        analizar_comentario(
            comentario=comentario_con_pii,
            nps_score=5,
            csat_ratings={},
            taxonomia={"Profesores": "Académico"},
            categorias_padre=["Académico"],
            client=mock_client,
            cache=None,
            id_encuesta="R-TEST",
        )

        # Verificar que chat_completion fue llamado
        mock_client.chat_completion.assert_called_once()
        # Extraer el user_prompt enviado al LLM
        call_kwargs = mock_client.chat_completion.call_args.kwargs
        user_prompt_enviado = call_kwargs["user_prompt"]
        # FM-002: el email original NO debe estar en el user_prompt enviado a DeepSeek.
        self.assertNotIn(
            "test@example.com",
            user_prompt_enviado,
            "FM-002 violado: el email original llegó al LLM sin redactar",
        )
        # El placeholder [CORREO ENMASCARADO] SÍ debe estar.
        self.assertIn("[CORREO ENMASCARADO]", user_prompt_enviado)


class TestAnalizarComentarioCacheKeyPreservaOriginal(unittest.TestCase):
    """FM-002: el cache-key usa el comentario ORIGINAL (no el redactado)
    para preservar hits existentes en caché legacy."""

    def test_cache_get_recibe_comentario_original(self):
        """Si se pasa un cache, cache.get se llama con el comentario original."""
        mock_client = MagicMock()
        mock_cache = MagicMock()
        # Cache miss → se llama al LLM.
        mock_cache.get.return_value = None
        mock_client.chat_completion.return_value = {
            "unidades": [{
                "orden": 1, "texto": "test", "es_valido": True,
                "motivo_invalidez": None, "sentimiento": "neutro",
                "intensidad": 1, "justificacion_sentimiento": "t",
                "dimension": "Pendiente de Clasificación",
                "categoria_padre": "Pendiente de Clasificación",
                "es_mencion_mejora": False, "es_salvavidas": False,
                "dimension_evaluada_rating": None, "dimension_evaluada_score": None,
                "sub_aspectos": [],
            }]
        }
        comentario = "mi codigo es 20123456"
        analizar_comentario(
            comentario=comentario,
            nps_score=7,
            csat_ratings={},
            taxonomia={},
            categorias_padre=[],
            client=mock_client,
            cache=mock_cache,
            id_encuesta="R1",
        )
        # cache.get recibe el comentario ORIGINAL (con PII), no el redactado.
        mock_cache.get.assert_called_once_with(comentario, 7, {})
        # cache.set también recibe el comentario original como clave.
        mock_cache.set.assert_called_once()
        set_args = mock_cache.set.call_args.args
        self.assertEqual(set_args[0], comentario)


class TestPlaceholder(unittest.TestCase):
    """Tests del generador de placeholder para comentarios fallidos."""

    def test_placeholder_retorna_unidad_no_valida(self):
        """_placeholder retorna 1 unidad marcada es_valido=False."""
        resultado = _placeholder("comentario de prueba", "Error de API", "fallback")
        self.assertIsInstance(resultado, dict)
        self.assertIn("unidades", resultado)
        self.assertEqual(len(resultado["unidades"]), 1)
        unidad = resultado["unidades"][0]
        self.assertFalse(unidad["es_valido"])
        self.assertEqual(unidad["motivo_invalidez"], "fallback")
        self.assertIn("comentario de prueba", unidad["texto"])


if __name__ == "__main__":
    unittest.main()
