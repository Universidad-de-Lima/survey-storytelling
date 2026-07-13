"""
TESTS — IAClient (lib/ia_client.py)

Tests unitarios para el cliente HTTP de DeepSeek. Cubre el refactor FM-009
(http_client inyectable) y el flujo básico de chat_completion con mock.

Alcance Fase 1 (FM-009 start): esqueleto con ≥1 test por caso clave.
Cobertura completa (timeouts, HTTPError 429, JSON malformado) en Fase 2.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Asegurar que el directorio scripts/ está en sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.ia_client import DeepSeekClient


class TestDeepSeekClientInit(unittest.TestCase):
    """Tests del constructor — parámetros por defecto e inyectables (FM-009)."""

    def test_init_con_http_client_inyectable(self):
        """FM-009: el cliente acepta un http_client inyectable para tests."""
        mock_http = MagicMock()
        client = DeepSeekClient(
            api_key="test-key",
            model="deepseek-test",
            http_client=mock_http,
        )
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.model, "deepseek-test")
        # FM-009: el http_client inyectado se almacena como self._http_client.
        self.assertIs(client._http_client, mock_http)

    def test_init_sin_http_client_usa_urllib_por_defecto(self):
        """Si no se pasa http_client, se usa urllib.request (backward compat)."""
        from urllib import request as urllib_request
        client = DeepSeekClient(api_key="test-key")
        self.assertIs(client._http_client, urllib_request)


class TestDeepSeekClientChatCompletion(unittest.TestCase):
    """Tests de chat_completion con http_client mock."""

    def test_chat_completion_retorna_contenido_parseado(self):
        """FM-009: chat_completion con mock HTTP retorna el JSON parseado de DeepSeek."""
        mock_http = MagicMock()
        # Configurar el mock para simular la respuesta HTTP de DeepSeek
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "choices": [{
                "message": {
                    "content": json.dumps({"sentimiento": "positivo", "unidades": []})
                }
            }],
        }).encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_http.urlopen.return_value = mock_resp

        client = DeepSeekClient(
            api_key="test-key",
            model="deepseek-test",
            http_client=mock_http,
            max_retries=1,
        )
        result = client.chat_completion(
            system_prompt="test system",
            user_prompt="test user",
            temperature=0.1,
            max_tokens=100,
        )
        # El cliente debe retornar el JSON parseado (no el string crudo).
        self.assertIsInstance(result, dict)
        self.assertEqual(result["sentimiento"], "positivo")
        # El mock fue llamado una vez (no reintentos).
        mock_http.urlopen.assert_called_once()
        # El acumulador de usage se actualizó.
        self.assertEqual(client.usage["input_tokens"], 10)
        self.assertEqual(client.usage["output_tokens"], 5)


if __name__ == "__main__":
    unittest.main()
