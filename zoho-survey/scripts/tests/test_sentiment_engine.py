"""
Tests — Sentiment Engine (lib/sentiment_engine).

Verifica la clasificación de sentimiento (positivo/negativo/neutro) y la intensidad
(1-5) producida por analizar_sentimiento_intensidad().

Motor (Fase 7):
- SentenceTransformer + cosine similarity con 3 anclas (positivo, negativo, neutro).
- Softmax con temperatura 10 para convertir similitudes en probabilidades.
- Reglas léxicas para intensidad (intensificadores, atenuantes, severidad, impacto).
- Regla de negocio: si es_evento_negativo → fuerza 'negativo'.
- Calibración Fase 7: si confianza < SENTIMENT_CONFIDENCE_THRESHOLD (0.4 por defecto)
  Y no hay es_evento_negativo → fuerza 'neutro' (evita argmax arbitrario en empates).

Notas sobre el entorno de tests:
- Estos tests se ejecutan en CI donde sentence_transformers está instalado.
- En CI, los embeddings son reales y los scores varían según el texto.
- En entornos sin sentence_transformers, el fallback devuelve embeddings de ceros,
  produciendo scores 0,0,0 (confianza 0.333). En ese caso, los tests de "positivo
  esperado" pueden no pasar porque la confianza baja los reclasifica a neutro.
- Los tests de "negativo esperado" sí pasan en cualquier entorno porque dependen
  de es_evento_negativo (regla léxica fuerte), no del modelo.

Estrategia de tests:
- Casos negativos: verifican reglas léxicas (es_evento_negativo). Estables en
  cualquier entorno.
- Casos positivos: usan patch/mocking para simular modelo funcional, garantizando
  que el test verifique la lógica de decisión independientemente del modelo.
- Casos neutros/ambiguos: verifican la calibración por umbral de confianza.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.sentiment_engine import analizar_sentimiento_intensidad
from lib.config import SENTIMENT_CONFIDENCE_THRESHOLD


class TestSentimentEngine(unittest.TestCase):
    """Tests del motor de sentimiento con modelo simulado.

    Estos tests usan mock para simular un modelo SentenceTransformer funcional,
    garantizando que la lógica de decisión se verifica independientemente de
    si el modelo real está instalado en el entorno.
    """

    def _mock_model(self, score_pos, score_neg, score_neu):
        """Crea un mock del modelo que produce similitudes controladas."""
        class MockModel:
            def encode(self, texts, **kwargs):
                # Para cada texto, devolver el mismo embedding
                # que produce las similitudes deseadas contra anclas ortonormales.
                emb = np.array([score_pos, score_neg, score_neu])
                return np.array([emb] * len(texts))
        return MockModel()

    def _setup_mock(self, score_pos, score_neg, score_neu):
        """Aplica mocks para simular modelo funcional con scores controlados."""
        import lib.sentiment_engine as se
        mock_model = self._mock_model(score_pos, score_neg, score_neu)
        # Anclas ortonormales: la similitud coseno será igual al valor del embedding
        mock_anchor_embs = np.eye(3)
        return (
            patch.object(se, 'obtener_modelo', return_value=mock_model),
            patch.object(se, '_SENT_EMBEDDINGS', mock_anchor_embs),
            patch.object(se, '_SENT_KEYS', ['positivo', 'negativo', 'neutro']),
            patch.object(se, '_inicializar_embeddings', lambda: None),
        )

    # ── Casos negativos (estables en cualquier entorno) ──

    def test_caso3_negativo_alta(self):
        """'Los ascensores fallan constantemente' → negativo, intensidad alta.
        Estable: depende de es_evento_negativo (regla léxica), no del modelo.
        """
        res = analizar_sentimiento_intensidad("Los ascensores fallan constantemente")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertTrue(res["intensidad"] >= 4)

    def test_caso4_negativo_alta(self):
        """'Nunca encuentro vacantes' → negativo, intensidad alta.
        Estable: severidad 'nunca' fuerza es_evento_negativo=True.
        """
        res = analizar_sentimiento_intensidad("Nunca encuentro vacantes")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertTrue(res["intensidad"] >= 4)

    def test_caso6_negativo_muy_alta(self):
        """'El edificio se inunda cada invierno' → negativo, intensidad 5.
        La palabra 'inunda' tiene bonus +1 hardcodeado en el motor.
        """
        res = analizar_sentimiento_intensidad("El edificio se inunda cada invierno")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertEqual(res["intensidad"], 5)

    # ── Casos positivos (con mock de modelo funcional) ──

    def test_caso1_positivo_alta(self):
        """'Los profesores explican muy bien' → positivo, intensidad alta.
        Con modelo funcional: alta similitud con ancla positivo → confianza alta.
        """
        cm1, cm2, cm3, cm4 = self._setup_mock(0.9, 0.1, 0.2)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("Los profesores explican muy bien")
            self.assertEqual(res["sentimiento"], "positivo")
            self.assertTrue(res["intensidad"] >= 4)

    def test_caso2_positivo_baja(self):
        """'Está bien' → positivo con confianza suficiente, intensidad baja.
        Con modelo funcional: similitud media con positivo (0.6) → confianza > 0.4.
        """
        cm1, cm2, cm3, cm4 = self._setup_mock(0.6, 0.2, 0.3)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("Está bien")
            self.assertEqual(res["sentimiento"], "positivo")
            self.assertTrue(res["intensidad"] <= 3)

    # ── Casos neutros / ambiguos (calibración Fase 7) ──

    def test_caso5_neutro_baja_confianza(self):
        """'Podría mejorar un poco' → neutro cuando confianza < umbral.
        Caso que motivó la Fase 7: con scores iguales (empate), argmax caía en
        'positivo' por convención. Ahora se fuerza 'neutro'.
        """
        # Simular empate: scores iguales → softmax uniforme → confianza 0.333 < 0.4
        cm1, cm2, cm3, cm4 = self._setup_mock(0.1, 0.1, 0.1)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("Podría mejorar un poco")
            self.assertEqual(res["sentimiento"], "neutro")
            self.assertTrue(res["intensidad"] <= 2)

    def test_neutro_alta_similitud_ancla_neutro(self):
        """'Regular' → neutro cuando el modelo lo asocia fuertemente con ancla neutro."""
        cm1, cm2, cm3, cm4 = self._setup_mock(0.2, 0.2, 0.9)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("Regular")
            self.assertEqual(res["sentimiento"], "neutro")
            self.assertTrue(res["intensidad"] <= 2)

    def test_neutro_confianza_exactamente_en_umbral(self):
        """Si confianza == umbral, NO se fuerza neutro (se usa argmax)."""
        # Calcular scores que produzcan confianza exactamente 0.4
        # softmax([0.4*k, 0.4*k, 0.4*k]) no funciona (uniforme)
        # Necesitamos scores que produzcan probs = [0.4, 0.3, 0.3]
        # softmax([a, b, c]) con temp 10 = 0.4, 0.3, 0.3
        # → a-b = ln(4/3) ≈ 0.288, a-c = ln(4/3) ≈ 0.288
        import numpy as np
        a = 0.4
        b = a - np.log(4/3) / 10
        c = a - np.log(4/3) / 10
        cm1, cm2, cm3, cm4 = self._setup_mock(a, b, c)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("texto ambiguo")
            # Confianza = 0.4 = umbral → NO se fuerza neutro → argmax = positivo
            self.assertEqual(res["sentimiento"], "positivo")

    def test_es_evento_negativo_prevalece_sobre_confianza_baja(self):
        """Si hay es_evento_negativo Y confianza baja, prevalece negativo.
        La regla léxica fuerte tiene prioridad sobre la calibración por umbral.
        """
        # Simular empate (confianza 0.333 < 0.4) pero con severidad léxica
        cm1, cm2, cm3, cm4 = self._setup_mock(0.1, 0.1, 0.1)
        with cm1, cm2, cm3, cm4:
            res = analizar_sentimiento_intensidad("Los ascensores fallan constantemente")
            self.assertEqual(res["sentimiento"], "negativo")
            self.assertTrue(res["intensidad"] >= 4)

    def test_texto_vacio(self):
        """Texto vacío → neutro por defecto con confianza 1.0."""
        res = analizar_sentimiento_intensidad("")
        self.assertEqual(res["sentimiento"], "neutro")
        self.assertEqual(res["intensidad"], 1)
        self.assertEqual(res["confianza_sentimiento"], 1.0)

    def test_umbral_configurable(self):
        """El umbral debe estar definido en config.py como constante configurable."""
        self.assertIsInstance(SENTIMENT_CONFIDENCE_THRESHOLD, float)
        self.assertGreater(SENTIMENT_CONFIDENCE_THRESHOLD, 0.0)
        self.assertLess(SENTIMENT_CONFIDENCE_THRESHOLD, 1.0)
        # Valor por defecto razonable (entre 0.3 y 0.5 según calibración Fase 7)
        self.assertGreaterEqual(SENTIMENT_CONFIDENCE_THRESHOLD, 0.3)
        self.assertLessEqual(SENTIMENT_CONFIDENCE_THRESHOLD, 0.5)


if __name__ == '__main__':
    unittest.main()
