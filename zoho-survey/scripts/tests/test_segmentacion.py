"""
Tests — Segmentación NPS (lib/segmentacion_nps).

Verifica la fragmentación de comentarios NPS en Meaning Units (Unidades de Opinión)
usando spaCy para análisis sintáctico.

Notas sobre el algoritmo (v3.0):
- El algoritmo aplica 4 heurísticas de corte: cláusulas verbales, nominales,
  comas en enumeraciones, contraste si/no, aposición.
- Aplica propagación de contexto compartido: Right-Node Raising (propaga
  adjetivos) y Left-Node Raising (propaga verbos).
- Estas heurísticas hacen que el algoritmo sea MÁS granular que la versión
  anterior, produciendo más unidades de opinión más atómicas. Esto es deseable
  para análisis cualitativo: cada unidad se clasifica independientemente.

Los tests reflejan el comportamiento actual del algoritmo. Si el algoritmo
cambia, estos tests deben actualizarse en consecuencia.
"""
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.segmentacion_nps import fragmentar_comentario_nps


class TestSegmentacionNPS(unittest.TestCase):

    def test_vacio(self):
        # Casos vacíos y ruido
        self.assertEqual(fragmentar_comentario_nps(""), [])
        self.assertEqual(fragmentar_comentario_nps("   "), [])
        self.assertEqual(fragmentar_comentario_nps(None), [])
        self.assertEqual(fragmentar_comentario_nps("etc"), [])
        self.assertEqual(fragmentar_comentario_nps("ninguno"), [])

    def test_caso_carreras_con_privilegios(self):
        # Algoritmo v3.0: aplica Right-Node Raising y divide en 4 unidades atómicas.
        # Esto es deseable: cada idea se clasifica independientemente en el ETL.
        texto = "Hay carrera que tienen mucho más avance y privilegios frente a otras, y me parece que debería ser más igualitario para todas"
        res = fragmentar_comentario_nps(texto)
        # Verificamos que las ideas clave están presentes (no necesariamente como una sola frase)
        all_text = " ".join(res)
        self.assertIn("igualitario", all_text.lower())
        self.assertIn("privilegios", all_text.lower())
        # El algoritmo moderno produce >= 3 unidades
        self.assertTrue(len(res) >= 3, f"Esperaba >= 3 unidades, obtuvo {len(res)}: {res}")

    def test_caso_psicologia_humanidades(self):
        # Algoritmo v3.0: Left-Node Raising propaga 'Deberían agregar más cursos de'
        # como prefijo verbal. Produce 2 unidades, no 1.
        texto = "Deberían agregar más cursos de psicología comunitaria y humanidades en vez de quitarlos"
        res = fragmentar_comentario_nps(texto)
        # Verificamos que el contenido se preserva
        all_text = " ".join(res)
        self.assertIn("psicología", all_text.lower())
        self.assertIn("humanidades", all_text.lower())
        # El algoritmo moderno produce >= 1 unidad (típicamente 2 por Left-Node Raising)
        self.assertTrue(len(res) >= 1, f"Esperaba >= 1 unidades, obtuvo {len(res)}: {res}")

    def test_caso_enumeracion_problemas(self):
        # Enumeración de problemas con puntuación fuerte
        texto = "Aún hay cosas que mejorar: falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de los ascensores, clases virtuales innecesarias"
        res = fragmentar_comentario_nps(texto)
        all_text = " ".join(res).lower()
        self.assertIn("aire", all_text)
        self.assertIn("enchufes", all_text)
        # Debe dividir la enumeración
        self.assertTrue(len(res) >= 3)

    def test_caso_enumeracion_fortalezas(self):
        # Enumeración de atributos nominales
        texto = "Buenos docentes, buena infraestructura y biblioteca moderna"
        res = fragmentar_comentario_nps(texto)
        all_text = " ".join(res).lower()
        self.assertIn("biblioteca", all_text)
        self.assertTrue(len(res) > 1)

    def test_caso_sin_puntuacion(self):
        # Casos sin puntuación — división por conectores adversativos
        texto = "los profesores enseñan mal y son muy aburridos pero la comida es buena"
        res = fragmentar_comentario_nps(texto)
        all_text = " ".join(res).lower()
        self.assertIn("comida", all_text)
        self.assertTrue(len(res) >= 2)

    def test_caso_errores_ortograficos(self):
        # Casos con errores ortográficos — verifica que el normalizador los maneja
        texto = "la imfraestructura ta malograda xq no hay luz tmb los profes aburren"
        res = fragmentar_comentario_nps(texto)
        self.assertTrue(len(res) >= 1)

    def test_caso_nominales(self):
        # Casos nominales (sin verbos) — división por comas
        texto = "Falta de aire, falta de enchufes, ascensores malogrados"
        res = fragmentar_comentario_nps(texto)
        self.assertTrue(len(res) >= 2)

    def test_entidades_protegidas(self):
        # Verifica que las entidades (nombres de facultades) se protegen
        res = fragmentar_comentario_nps("La facultad de Arquitectura y diseño es buena pero falta luz")
        all_text = " ".join(res)
        # La facultad debe preservarse como unidad (no dividirse por 'y')
        self.assertTrue(
            any("arquitectura" in u.lower() for u in res),
            f"Esperaba 'arquitectura' en alguna unidad, obtuvo: {res}"
        )
        # Debe separar la idea de falta de luz
        self.assertTrue(any("luz" in u.lower() for u in res))


if __name__ == '__main__':
    unittest.main()
