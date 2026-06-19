import unittest
from lib.sentiment_engine import analizar_sentimiento_intensidad

class TestSentimentEngine(unittest.TestCase):
    def test_caso1_positivo_alta(self):
        # "Los profesores explican muy bien" -> positivo, intensidad alta
        res = analizar_sentimiento_intensidad("Los profesores explican muy bien")
        self.assertEqual(res["sentimiento"], "positivo")
        self.assertTrue(res["intensidad"] >= 4)
        
    def test_caso2_positivo_baja(self):
        # "Está bien" -> positivo, intensidad baja
        res = analizar_sentimiento_intensidad("Está bien")
        self.assertEqual(res["sentimiento"], "positivo")
        self.assertTrue(res["intensidad"] <= 3)
        
    def test_caso3_negativo_alta(self):
        # "Los ascensores fallan constantemente" -> negativo, intensidad alta
        res = analizar_sentimiento_intensidad("Los ascensores fallan constantemente")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertTrue(res["intensidad"] >= 4)
        
    def test_caso4_negativo_alta(self):
        # "Nunca encuentro vacantes" -> negativo, intensidad alta
        res = analizar_sentimiento_intensidad("Nunca encuentro vacantes")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertTrue(res["intensidad"] >= 4)
        
    def test_caso5_neutro_baja(self):
        # "Podría mejorar un poco" -> negativo o neutro, intensidad baja
        res = analizar_sentimiento_intensidad("Podría mejorar un poco")
        self.assertIn(res["sentimiento"], ["negativo", "neutro"])
        self.assertTrue(res["intensidad"] <= 2)
        
    def test_caso6_negativo_muy_alta(self):
        # "El edificio se inunda cada invierno" -> negativo, intensidad muy alta
        res = analizar_sentimiento_intensidad("El edificio se inunda cada invierno")
        self.assertEqual(res["sentimiento"], "negativo")
        self.assertEqual(res["intensidad"], 5)

if __name__ == '__main__':
    unittest.main()
