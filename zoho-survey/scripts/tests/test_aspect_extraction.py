import unittest
from lib.aspect_extraction import procesar_opinion_unit

class TestAspectExtraction(unittest.TestCase):
    def test_wifi(self):
        res = procesar_opinion_unit("El internet se cae")
        self.assertEqual(res["aspecto_normalizado"], "Wi-Fi / Conectividad")
        
    def test_ascensores(self):
        res = procesar_opinion_unit("Los elevadores de O fallan")
        self.assertEqual(res["aspecto_normalizado"], "Ascensores")
        
    def test_docencia(self):
        res = procesar_opinion_unit("Los profes explican muy bien")
        self.assertEqual(res["aspecto_normalizado"], "Calidad Docente")
        
    def test_matricula(self):
        res = procesar_opinion_unit("El sistema de inscripcion es lento")
        self.assertEqual(res["aspecto_normalizado"], "Sistema de Matrícula")
        
    def test_pendiente_clasificacion(self):
        res = procesar_opinion_unit("El unicornio volador es azul")
        self.assertEqual(res["aspecto_normalizado"], "Pendiente de Clasificación")

if __name__ == '__main__':
    unittest.main()
