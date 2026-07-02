"""
SURVEY ETL METRICS — Módulo de cálculos matemáticos para encuestas.

Contiene funciones puras para el cálculo de Net Promoter Score (NPS),
Customer Satisfaction Score (CSAT) y Promedio Ponderado de satisfacción.
"""

from typing import List


def calc_nps(promotores: int, pasivos: int, detractores: int) -> float:
    """
    Calcula el Net Promoter Score (NPS).
    Rango de retorno: [-100.0, 100.0]
    """
    total = promotores + pasivos + detractores
    if total == 0:
        return 0.0
    return round(((promotores - detractores) / total) * 100, 2)


def calc_csat(t3b: int, total: int) -> float:
    """
    Calcula el Customer Satisfaction Score (CSAT) basado en Top 3 Box.
    Rango de retorno: [0.0, 100.0]

    Es una función de "box score" genérica: calcula (subset / total) * 100.
    Por eso el Top 2 Box (T2B) se obtiene reutilizando esta misma función con
    el conteo de las dos respuestas más altas como primer argumento.
    """
    if total == 0:
        return 0.0
    return round((t3b / total) * 100, 2)


def calc_promedio_ponderado(counts: List[int], weights: List[int], max_scale: int) -> float:
    """
    Calcula el Promedio Ponderado de satisfacción sobre una escala Likert.

    Metodología:
        1. proporción_i = count_i / total
        2. suma = Σ (proporción_i * peso_i)
        3. normalizado = suma / max_scale
        4. porcentaje = normalizado * 100

    Rango de retorno: [0.0, 100.0].

    `counts` y `weights` deben estar alineados posicionalmente y en el mismo
    orden (de más positivo a más negativo). `max_scale` es el peso máximo
    (5 para una escala Likert de 5 puntos). No se redondea internamente: la
    precisión se preserva y el redondeo ocurre solo al mostrar.
    """
    total = sum(counts)
    if total == 0 or max_scale <= 0:
        return 0.0
    suma_ponderada = sum(c * w for c, w in zip(counts, weights))
    return (suma_ponderada / total / max_scale) * 100
