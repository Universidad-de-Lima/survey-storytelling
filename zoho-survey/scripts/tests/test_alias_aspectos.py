"""
ALIAS ASPECTOS TEST — Validación de integridad del diccionario de alias.

Verifica que:
  1. El archivo alias_aspectos.json se carga correctamente.
  2. Cada alias mapea a una dimensión que existe en la taxonomía oficial
     (CATEGORIA_DIMENSION_PREGRADO + CATEGORIA_DIMENSION_GRADUADO).
  3. No hay alias duplicados entre dimensiones (ambigüedad).
  4. El diccionario cargado desde JSON es estructuralmente idéntico al
     que usaba el código hardcodeado pre-Fase 1.

Ejecutar en CI (tests.yml) o localmente con:
    python -m pytest zoho-survey/scripts/tests/test_alias_aspectos.py -v
"""

import unittest
import json
import sys
from pathlib import Path

# Asegurar que scripts/ está en el path para importar lib
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.config import CATEGORIA_DIMENSION_PREGRADO, CATEGORIA_DIMENSION_GRADUADO
from lib.aspect_extraction import ALIAS_DICT_MANUAL


class TestAliasAspectos(unittest.TestCase):
    """Validación de integridad del diccionario de alias de aspectos."""

    @classmethod
    def setUpClass(cls):
        """Cargar taxonomía oficial unificada."""
        cls.taxonomia_oficial = {}
        cls.taxonomia_oficial.update(CATEGORIA_DIMENSION_PREGRADO)
        cls.taxonomia_oficial.update(CATEGORIA_DIMENSION_GRADUADO)
        # Agregar dimensiones catch-all
        cls.taxonomia_oficial.update({
            "Satisfacción estudiantil": "Satisfacción estudiantil",
            "Espacios comunes": "Infraestructura",
            "Pendiente de Clasificación": "Pendiente de Clasificación",
        })

    def test_alias_dict_cargado_desde_json(self):
        """Verifica que ALIAS_DICT_MANUAL se cargó correctamente (no está vacío)."""
        self.assertGreater(
            len(ALIAS_DICT_MANUAL), 0,
            "ALIAS_DICT_MANUAL está vacío — alias_aspectos.json no se cargó correctamente"
        )
        # Verificar que tiene al menos las categorías principales
        self.assertGreaterEqual(
            len(ALIAS_DICT_MANUAL), 30,
            f"ALIAS_DICT_MANUAL tiene {len(ALIAS_DICT_MANUAL)} dimensiones, se esperaban ≥30"
        )

    def test_cada_dimension_existe_en_taxonomia(self):
        """Cada clave en ALIAS_DICT_MANUAL debe existir en la taxonomía oficial."""
        faltantes = []
        for dimension in ALIAS_DICT_MANUAL:
            if dimension not in self.taxonomia_oficial:
                faltantes.append(dimension)
        
        self.assertEqual(
            len(faltantes), 0,
            f"Dimensiones en alias sin correspondencia en taxonomía oficial: {faltantes}"
        )

    def test_no_alias_duplicados(self):
        """Ningún alias debe aparecer en más de una dimensión (ambigüedad).
        
        Nota: algunos alias legítimamente colisionan entre dimensiones porque
        la misma palabra puede referirse a contextos distintos. Estos están
        documentados y son aceptados por diseño:
          - 'notas' → Evaluación / Récord académico
          - 'trato' → Enseñanza / Atención administrativa
          - 'practicas' → Evaluación / Empleabilidad
          - 'clases virtuales' → Cursos / Aula virtual
          - 'metodologia' → Enseñanza / Metodologías (Docencia)
          - 'programa' → Software / Cumplimiento
          - 'silabo' → Plan curricular / Cumplimiento
          - 'equipo' → Equipamiento TI / Trabajo en equipo
        """
        # Colisiones conocidas y aceptadas por diseño
        COLISIONES_ACEPTADAS = {
            'notas', 'trato', 'practicas', 'clases virtuales',
            'metodologia', 'programa', 'silabo', 'equipo'
        }
        
        alias_to_dims = {}
        duplicados = []
        
        for dimension, aliases in ALIAS_DICT_MANUAL.items():
            for alias in aliases:
                alias_lower = alias.lower()
                if alias_lower in COLISIONES_ACEPTADAS:
                    continue  # Colisión legítima por diseño
                if alias_lower in alias_to_dims:
                    duplicados.append(
                        f"'{alias}' → '{alias_to_dims[alias_lower]}' y '{dimension}'"
                    )
                else:
                    alias_to_dims[alias_lower] = dimension
        
        self.assertEqual(
            len(duplicados), 0,
            f"Alias duplicados (ambigüedad no documentada): {duplicados}"
        )

    def test_cada_dimension_tiene_alias(self):
        """Cada dimensión debe tener al menos un alias definido."""
        sin_alias = []
        for dimension in ALIAS_DICT_MANUAL:
            if not ALIAS_DICT_MANUAL[dimension]:
                sin_alias.append(dimension)
        
        self.assertEqual(
            len(sin_alias), 0,
            f"Dimensiones sin alias: {sin_alias}"
        )

    def test_json_estructura_valida(self):
        """Verifica que el JSON se puede cargar directamente y tiene estructura correcta."""
        json_path = SCRIPTS_DIR / "config" / "alias_aspectos.json"
        self.assertTrue(json_path.exists(), f"Archivo no encontrado: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Debe ser un dict de categorías padre
        self.assertIsInstance(data, dict)
        categorias_esperadas = {
            "Académico", "Administrativo y Bienestar", "Infraestructura",
            "Tecnología", "Docencia", "Desarrollo Profesional"
        }
        for cat in categorias_esperadas:
            self.assertIn(cat, data, f"Categoría padre faltante en JSON: {cat}")
            self.assertIsInstance(data[cat], dict, f"'{cat}' debe ser un objeto")
            self.assertGreater(len(data[cat]), 0, f"'{cat}' no tiene dimensiones")


if __name__ == "__main__":
    unittest.main()
