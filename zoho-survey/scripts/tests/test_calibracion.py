"""
TEST-03: Test de calibración cualitativa convertido a test unitario real.

El archivo original era un script de calibración manual sin assertions (solo prints).
Convertido a TestCase con assertions para integrarse correctamente en la suite de CI.

Las frases de prueba provienen del análisis manual de la encuesta 2026-1
y verifican que el pipeline cualitativo produce resultados coherentes.
"""
import os
import sys
import unittest

# Añadir lib al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.aspect_extraction import procesar_opinion_unit
from lib.segmentacion_nps import extraer_unidades_opinion
from lib.sentiment_engine import analizar_sentimiento_intensidad


class TestCalibracionCualitativa(unittest.TestCase):
    """Tests de regresión sobre frases calibradas del análisis manual."""

    TEST_FRASES = [
        "Falta de enchufes en aulas",
        "No me gustan cursos y horarios",
        "Estoy satisfecha pero falta mejorar ascensores",
    ]

    def test_frases_producen_unidades_no_vacias(self):
        """Cada frase calibrada debe producir al menos 1 unidad de opinión."""
        for frase in self.TEST_FRASES:
            with self.subTest(frase=frase):
                unidades = extraer_unidades_opinion(frase)
                self.assertGreaterEqual(
                    len(unidades), 1,
                    f"La frase '{frase}' no produjo unidades de opinión"
                )

    def test_unidades_tienen_aspecto_detectado(self):
        """Cada unidad procesada debe retornar un aspecto_detectado (string)."""
        for frase in self.TEST_FRASES:
            unidades = extraer_unidades_opinion(frase)
            for u in unidades:
                with self.subTest(frase=frase, unidad=u):
                    res = procesar_opinion_unit(u)
                    self.assertIsInstance(
                        res.get("aspecto_detectado"), str,
                        f"aspecto_detectado no es string para unidad: '{u}'"
                    )

    def test_unidades_tienen_sentimiento_valido(self):
        """Cada unidad debe clasificarse con sentimiento positivo/negativo/neutro."""
        sentimientos_validos = {"positivo", "negativo", "neutro"}
        for frase in self.TEST_FRASES:
            unidades = extraer_unidades_opinion(frase)
            for u in unidades:
                with self.subTest(frase=frase, unidad=u):
                    sent = analizar_sentimiento_intensidad(u)
                    self.assertIn(
                        sent.get("sentimiento", ""), sentimientos_validos,
                        f"Sentimiento inválido para unidad: '{u}'"
                    )

    def test_unidades_tienen_intensidad_en_rango(self):
        """La intensidad debe estar en el rango 1-5."""
        for frase in self.TEST_FRASES:
            unidades = extraer_unidades_opinion(frase)
            for u in unidades:
                with self.subTest(frase=frase, unidad=u):
                    sent = analizar_sentimiento_intensidad(u)
                    intensidad = sent.get("intensidad", 0)
                    self.assertGreaterEqual(intensidad, 1, f"Intensidad < 1 para: '{u}'")
                    self.assertLessEqual(intensidad, 5, f"Intensidad > 5 para: '{u}'")


if __name__ == "__main__":
    unittest.main()
