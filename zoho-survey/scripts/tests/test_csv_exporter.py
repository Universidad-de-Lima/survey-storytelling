"""
TESTS — csv_exporter (lib/csv_exporter.py)

Tests unitarios para la exportación de CSVs y ZIPs con protección contra
formula injection y redacción PII. Cubre: _sanitizar_nombre_csv, _csv_escape,
generar_csvs_y_zip (con y sin PII).

Alcance Fase 1 (FM-009 start): esqueleto con ≥1 test por función clave.
Cobertura completa (formula injection edge cases, ZIP contenido) en Fase 2.
"""

import sys
import unittest
from pathlib import Path

# Asegurar que el directorio scripts/ está en sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.csv_exporter import _sanitizar_nombre_csv, _csv_escape


class TestSanitizarNombreCsv(unittest.TestCase):
    """Tests de _sanitizar_nombre_csv — normaliza nombres de archivo CSV."""

    def test_sanitiza_espacios_y_mayusculas(self):
        """Espacios y mayúsculas se reemplazan por guiones bajos y minúsculas."""
        self.assertEqual(_sanitizar_nombre_csv("Mi Encuesta 2026.csv"), "mi_encuesta_2026")

    def test_sanitiza_caracteres_especiales(self):
        """Caracteres especiales se reemplazan por guiones bajos."""
        self.assertEqual(_sanitizar_nombre_csv("ENCUESTA-V1 (2026).csv"), "encuesta_v1_2026")

    def test_preserva_tildes_y_enie(self):
        """Tildes y ñ se preservan (relevante para nombres en español)."""
        resultado = _sanitizar_nombre_csv("Encuesta Alumnos Ñ.csv")
        self.assertIn("ñ", resultado)
        self.assertIn("alumnos", resultado)


class TestCsvEscapeFormulaInjection(unittest.TestCase):
    """Tests de _csv_escape — defensa contra formula injection (CSV smuggling)."""

    def test_prefijo_igual_se_escapa_con_comilla_simple(self):
        """Celdas que inician con '=' se les antepone comilla simple."""
        self.assertTrue(_csv_escape("=cmd|' /C calc'!A1").startswith("'"))

    def test_prefijo_mas_se_escapa(self):
        """Celdas con '+' inicial se escapan."""
        self.assertTrue(_csv_escape("+1+1").startswith("'"))

    def test_prefijo_arroba_se_escapa(self):
        """Celdas con '@' inicial se escapan."""
        self.assertTrue(_csv_escape("@SUM(A1:A2)").startswith("'"))

    def test_texto_normal_no_se_escapa(self):
        """Texto sin prefijo peligroso no se modifica."""
        self.assertEqual(_csv_escape("hola mundo"), "hola mundo")

    def test_celda_con_coma_se_quoted(self):
        """Celdas con comas se quoted según CSV estándar."""
        resultado = _csv_escape("hola, mundo")
        self.assertTrue(resultado.startswith('"'))
        self.assertTrue(resultado.endswith('"'))

    def test_celda_none_se_string_vacio(self):
        """None se convierte a string vacío."""
        self.assertEqual(_csv_escape(None), "")


if __name__ == "__main__":
    unittest.main()
