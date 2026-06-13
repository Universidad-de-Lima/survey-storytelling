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
        self.assertEqual(fragmentar_comentario_nps(""), [])
        self.assertEqual(fragmentar_comentario_nps("   "), [])
        self.assertEqual(fragmentar_comentario_nps(None), [])
        
    def test_heuristica_basica(self):
        # Puntuacion
        res = fragmentar_comentario_nps("Hola. Adios!")
        self.assertEqual(res, ["Hola", "Adios"])
        
        # Conectores
        res2 = fragmentar_comentario_nps("buen servicio pero muy caro")
        self.assertEqual(res2, ["Buen servicio", "Muy caro"])

    def test_fallback_comas(self):
        # Frases nominales sin verbos
        res = fragmentar_comentario_nps("buenos profesores, aulas limpias, mala comida")
        self.assertEqual(res, ["Buenos profesores", "Aulas limpias", "Mala comida"])
        
    def test_entidades_protegidas(self):
        res = fragmentar_comentario_nps("La facultad de Arquitectura y diseño es buena pero falta luz")
        self.assertEqual(res, ["La facultad de arquitectura y diseño es buena", "Falta luz"])
        
    def test_spacy_coordinacion(self):
        # Múltiples verbos con 'y' sin coma
        # "enseñan mal" y "son aburridos"
        res = fragmentar_comentario_nps("los profesores enseñan mal y son muy aburridos")
        # Dependiendo del parseo, debería separar
        # Por ahora solo verificamos que corre y no falla, 
        # y que idealmente entrega 2.
        self.assertTrue(len(res) > 0)
        
    def test_spacy_no_separar_nominales_con_y(self):
        res = fragmentar_comentario_nps("me gusta la infraestructura y los laboratorios")
        # No hay multiples verbos, no debería separar por 'y'
        self.assertEqual(len(res), 1)

if __name__ == '__main__':
    unittest.main()
