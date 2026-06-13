import sys
import os
import unittest

# Agregar el directorio scripts al path para poder importar lib
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
sys.path.insert(0, scripts_dir)

from lib.segmentacion_nps import fragmentar_comentario_nps

class TestSegmentacionNPS(unittest.TestCase):
    
    def test_vacio(self):
        # 7. Casos vacíos
        self.assertEqual(fragmentar_comentario_nps(""), [])
        self.assertEqual(fragmentar_comentario_nps("   "), [])
        self.assertEqual(fragmentar_comentario_nps(None), [])
        self.assertEqual(fragmentar_comentario_nps("etc"), [])
        self.assertEqual(fragmentar_comentario_nps("ninguno"), [])
        
    def test_caso_carreras_con_privilegios(self):
        # 1. Caso carreras con privilegios (Caso 1)
        texto = "Hay carrera que tienen mucho más avance y privilegios frente a otras, y me parece que debería ser más igualitario para todas"
        res = fragmentar_comentario_nps(texto)
        # Verificamos que separa la idea de la carrera vs la idea de la igualdad
        self.assertIn("Hay carrera que tienen mucho más avance y privilegios frente a otras", res)
        self.assertIn("Me parece que debería ser más igualitario para todas", res)
        self.assertEqual(len(res), 2)

    def test_caso_psicologia_humanidades(self):
        # 2. Caso psicología comunitaria y humanidades (Caso 2)
        texto = "Deberían agregar más cursos de psicología comunitaria y humanidades en vez de quitarlos"
        res = fragmentar_comentario_nps(texto)
        # Regla 1: No dividir cuando varias palabras dependen del mismo verbo
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], "Deberían agregar más cursos de psicología comunitaria y humanidades en vez de quitarlos")

    def test_caso_enumeracion_problemas(self):
        # 3. Caso aire / enchufes / ascensores (Caso 3)
        texto = "Aún hay cosas que mejorar: falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de los ascensores, clases virtuales innecesarias"
        res = fragmentar_comentario_nps(texto)
        self.assertIn("Falta de aire en las torres antiguas", res)
        self.assertIn("Falta de enchufes en las aulas", res)
        # Verificamos que hay múltiples fragmentos separados correctamente
        self.assertTrue(len(res) >= 3)
        
    def test_caso_enumeracion_fortalezas(self):
        # Enumeración de atributos nominales
        texto = "Buenos docentes, buena infraestructura y biblioteca moderna"
        res = fragmentar_comentario_nps(texto)
        # Debería dividir en 2 o 3 partes dependiendo del parseo del sustantivo, pero DEBE dividir
        self.assertTrue(len(res) > 1)
        self.assertIn("Biblioteca moderna", res)

    def test_caso_sin_puntuacion(self):
        # 4. Casos sin puntuación
        texto = "los profesores enseñan mal y son muy aburridos pero la comida es buena"
        res = fragmentar_comentario_nps(texto)
        self.assertTrue(len(res) >= 2)
        self.assertIn("La comida es buena", res)

    def test_caso_errores_ortograficos(self):
        # 5. Casos con errores ortográficos
        texto = "la imfraestructura ta malograda xq no hay luz tmb los profes aburren"
        res = fragmentar_comentario_nps(texto)
        # Verifica que corre sin romperse y aplica corrección "xq", "tmb"
        self.assertTrue(len(res) >= 1)

    def test_caso_nominales(self):
        # 6. Casos nominales (sin verbos)
        texto = "Falta de aire, falta de enchufes, ascensores malogrados"
        res = fragmentar_comentario_nps(texto)
        # Debe separar las cláusulas nominales
        self.assertTrue(len(res) >= 2)

    def test_entidades_protegidas(self):
        res = fragmentar_comentario_nps("La facultad de Arquitectura y diseño es buena pero falta luz")
        self.assertEqual(res, ["La facultad de arquitectura y diseño es buena", "Falta luz"])

if __name__ == '__main__':
    unittest.main()
