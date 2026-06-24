import json
from sklearn.metrics import classification_report
from lib.sentiment_engine import analizar_sentimiento_intensidad

# Muestra manual de validación
muestras = [
    {"texto": "La biblioteca tiene buenos libros pero el wifi es muy malo", "true_sent": "negativo"}, # es_evento_negativo (falla o malo? "malo" es intenso)
    {"texto": "Me encanta la malla curricular, excelentes profesores", "true_sent": "positivo"},
    {"texto": "Todo normal, sin quejas", "true_sent": "neutro"},
    {"texto": "Se inunda el pabellón cada vez que llueve", "true_sent": "negativo"},
    {"texto": "Podría ser un poco mejor la cafetería", "true_sent": "neutro"}, # o negativo leve
    {"texto": "Pésimo sistema de matrícula, no pude ingresar", "true_sent": "negativo"},
    {"texto": "Los ascensores siempre están malogrados", "true_sent": "negativo"},
    {"texto": "El trato de los docentes es aceptable", "true_sent": "neutro"},
    {"texto": "Muy buen ambiente de estudio", "true_sent": "positivo"},
    {"texto": "Es imposible conseguir vacante", "true_sent": "negativo"}
]

y_true = []
y_pred = []

print("Resultados de Validación Empírica:")
print("-" * 50)
for m in muestras:
    res = analizar_sentimiento_intensidad(m["texto"])
    pred = res["sentimiento"]
    y_true.append(m["true_sent"])
    y_pred.append(pred)
    print(f"Texto: {m['texto']}")
    print(f"Predicción: {pred} (Intensidad: {res['intensidad']}) | Esperado: {m['true_sent']}")
    print("-" * 50)

print("\nMétricas de Clasificación:")
print(classification_report(y_true, y_pred))
