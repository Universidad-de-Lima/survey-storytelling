import os
import sys

# Añadir lib al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.aspect_extraction import procesar_opinion_unit
from lib.segmentacion_nps import extraer_unidades_opinion
from lib.sentiment_engine import analizar_sentimiento_intensidad

tests = [
    "Falta de enchufes en aulas",
    "No me gustan cursos y horarios",
    "Estoy satisfecha pero falta mejorar ascensores"
]

print("=== PRUEBAS DE REGRESIÓN ===")
for t in tests:
    print(f"\nOriginal: {t}")
    unidades = extraer_unidades_opinion(t)
    for i, u in enumerate(unidades):
        print(f"  Unidad {i+1}: {u}")
        res = procesar_opinion_unit(u)
        sent = analizar_sentimiento_intensidad(u)
        print(f"    Aspecto: {res['aspecto_detectado']}")
        print(f"    Sub Aspectos: {res['sub_aspectos']}")
        print(f"    Sentimiento: {sent['sentimiento']}")
