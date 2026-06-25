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

    # ── Fase 10.1: alias nuevos para recuperación de Pendiente de Clasificación ──

    def test_estacionamiento(self):
        """'estacionamiento' debe normalizar a 'Ubicación' (Infraestructura)."""
        res = procesar_opinion_unit("Falta estacionamiento en la universidad")
        self.assertEqual(res["aspecto_normalizado"], "Ubicación")
        self.assertEqual(res["categoria_padre"], "Infraestructura")
        self.assertEqual(res["metodo"], "alias")

    def test_estacionamientos_plural(self):
        """'estacionamientos' (plural) también debe clasificar a 'Ubicación'."""
        res = procesar_opinion_unit("Los estacionamientos son insuficientes")
        self.assertEqual(res["aspecto_normalizado"], "Ubicación")

    def test_banos(self):
        """'baños' debe normalizar a 'Aulas de clase' (Infraestructura)."""
        res = procesar_opinion_unit("Los baños están sucios")
        self.assertEqual(res["aspecto_normalizado"], "Aulas de clase")
        self.assertEqual(res["categoria_padre"], "Infraestructura")
        self.assertEqual(res["metodo"], "alias")

    def test_bano_singular(self):
        """'baño' (singular) también debe clasificar a 'Aulas de clase'."""
        res = procesar_opinion_unit("El baño del tercer piso no funciona")
        self.assertEqual(res["aspecto_normalizado"], "Aulas de clase")

    def test_edificio(self):
        """'edificio' debe normalizar a 'Aulas de clase' (Infraestructura)."""
        res = procesar_opinion_unit("El edificio H está lejos")
        self.assertEqual(res["aspecto_normalizado"], "Aulas de clase")
        self.assertEqual(res["categoria_padre"], "Infraestructura")
        self.assertEqual(res["metodo"], "alias")

    def test_edificios_plural(self):
        """'edificios' (plural) también debe clasificar a 'Aulas de clase'."""
        res = procesar_opinion_unit("Los edificios nuevos son modernos")
        self.assertEqual(res["aspecto_normalizado"], "Aulas de clase")

    def test_espacios(self):
        """'espacios' debe normalizar a 'Ambientes y salas para estudio' (Infraestructura)."""
        res = procesar_opinion_unit("Hay pocos espacios para estudiar")
        self.assertEqual(res["aspecto_normalizado"], "Ambientes y salas para estudio")
        self.assertEqual(res["categoria_padre"], "Infraestructura")
        self.assertEqual(res["metodo"], "alias")

    def test_espacio_singular(self):
        """'espacio' (singular) también debe clasificar a 'Ambientes y salas para estudio'."""
        res = procesar_opinion_unit("Falta espacio en la biblioteca")
        self.assertEqual(res["aspecto_normalizado"], "Ambientes y salas para estudio")

    def test_ppt(self):
        """'ppt' debe normalizar a 'Claridad de los recursos académicos' (Académico)."""
        res = procesar_opinion_unit("Muchas ppt en clase, poco práctica")
        self.assertEqual(res["aspecto_normalizado"], "Claridad de los recursos académicos")
        self.assertEqual(res["categoria_padre"], "Académico")
        self.assertEqual(res["metodo"], "alias")

    def test_ppts_plural(self):
        """'ppts' (plural) también debe clasificar a 'Claridad de los recursos académicos'."""
        res = procesar_opinion_unit("Las ppts son aburridas")
        self.assertEqual(res["aspecto_normalizado"], "Claridad de los recursos académicos")

    def test_maquetas(self):
        """'maquetas' debe normalizar a 'Cursos del programa y contenidos' (Académico)."""
        res = procesar_opinion_unit("No hay espacios para maquetas")
        self.assertEqual(res["aspecto_normalizado"], "Cursos del programa y contenidos")
        self.assertEqual(res["categoria_padre"], "Académico")
        self.assertEqual(res["metodo"], "alias")

    def test_maqueta_singular(self):
        """'maqueta' (singular) también debe clasificar a 'Cursos del programa y contenidos'."""
        res = procesar_opinion_unit("La maqueta del proyecto final")
        self.assertEqual(res["aspecto_normalizado"], "Cursos del programa y contenidos")

    def test_alias_antiguos_siguen_funcionando(self):
        """Regresión: alias existentes antes de Fase 10.1 deben seguir clasificando igual."""
        casos = [
            ("El internet se cae", "Conexión Wi-Fi en el campus"),
            ("Los elevadores de O fallan", "Aulas de clase"),
            ("Los profes explican muy bien", "Calidad de la enseñanza en la carrera"),
            ("El sistema de inscripcion es lento", "Procedimientos administrativos"),
        ]
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                res = procesar_opinion_unit(texto)
                self.assertEqual(res["aspecto_normalizado"], esperado,
                                 f"Regresión: '{texto}' debería ser '{esperado}' pero fue '{res['aspecto_normalizado']}'")

    def test_sin_match_sigue_como_pendiente(self):
        """Regresión: comentarios sin alias reconocible siguen en Pendiente de Clasificación."""
        res = procesar_opinion_unit("hay cosas que mejorar")
        self.assertEqual(res["aspecto_normalizado"], "Pendiente de Clasificación")


if __name__ == '__main__':
    unittest.main()
