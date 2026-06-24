"""
Tests — Aspect Extraction (lib/aspect_extraction).

Verifica la normalización de aspectos desde Opinion Units hacia las dimensiones
oficiales definidas en CATEGORIA_PADRE_MAP (construido desde CATEGORIA_DIMENSION_PREGRADO
y CATEGORIA_DIMENSION_GRADUADO en lib/config.py).

Los buckets esperados por estos tests son los nombres OFICIALES de las dimensiones
tal como existen en CATEGORIA_PADRE_MAP, NO alias informales. Si una dimensión se
renombra en config.py, estos tests deben actualizarse en consecuencia.

Notas:
- 'Wi-Fi / Conectividad', 'Calidad Docente', 'Sistema de Matrícula', 'Ascensores'
  son NOMBRES INFORMALES que NO existen como dimensiones oficiales. Los tests
  originales esperaban estos nombres y fallaban porque el ETL normaliza a los
  nombres oficiales del catálogo.
- 'Ascensores' fue agregado como alias al bucket 'Aulas de clase' (que agrupa
  instalaciones) en Fase 6, porque aparece en comentarios reales.
"""
import os
import sys
import unittest

# Agregar el directorio scripts al path para poder importar lib
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.aspect_extraction import procesar_opinion_unit


class TestAspectExtraction(unittest.TestCase):
    def test_wifi(self):
        """'internet' debe normalizar a 'Conexión Wi-Fi en el campus' (Tecnología)."""
        res = procesar_opinion_unit("El internet se cae")
        self.assertEqual(res["aspecto_normalizado"], "Conexión Wi-Fi en el campus")
        self.assertEqual(res["categoria_padre"], "Tecnología")
        self.assertEqual(res["metodo"], "alias")

    def test_ascensores(self):
        """'ascensores'/'elevadores' deben normalizar a 'Aulas de clase' (Infraestructura).

        Antes de Fase 6, estos términos caían en 'Pendiente de Clasificación' porque
        no estaban en ALIAS_DICT_MANUAL. Fueron agregados al bucket 'Aulas de clase'
        (que agrupa instalaciones) tras verificar que aparecen en comentarios reales.
        """
        res = procesar_opinion_unit("Los elevadores de O fallan")
        self.assertEqual(res["aspecto_normalizado"], "Aulas de clase")
        self.assertEqual(res["categoria_padre"], "Infraestructura")
        self.assertEqual(res["metodo"], "alias")

        # Verificar también la variante 'ascensor'
        res2 = procesar_opinion_unit("Los ascensores están malogrados")
        self.assertEqual(res2["aspecto_normalizado"], "Aulas de clase")

    def test_docencia(self):
        """'profes' debe normalizar a 'Calidad de la enseñanza en la carrera' (Académico)."""
        res = procesar_opinion_unit("Los profes explican muy bien")
        self.assertEqual(res["aspecto_normalizado"], "Calidad de la enseñanza en la carrera")
        self.assertEqual(res["categoria_padre"], "Académico")
        self.assertEqual(res["metodo"], "alias")

    def test_matricula(self):
        """'sistema de inscripcion' debe normalizar a 'Procedimientos administrativos' (Administrativo)."""
        res = procesar_opinion_unit("El sistema de inscripcion es lento")
        self.assertEqual(res["aspecto_normalizado"], "Procedimientos administrativos")
        self.assertEqual(res["categoria_padre"], "Administrativo y Bienestar")
        self.assertEqual(res["metodo"], "alias")

    def test_pendiente_clasificacion(self):
        """Textos sin aspecto reconocible deben caer en 'Pendiente de Clasificación'."""
        res = procesar_opinion_unit("El unicornio volador es azul")
        self.assertEqual(res["aspecto_normalizado"], "Pendiente de Clasificación")
        self.assertEqual(res["categoria_padre"], "Pendiente de Clasificación")


if __name__ == '__main__':
    unittest.main()
