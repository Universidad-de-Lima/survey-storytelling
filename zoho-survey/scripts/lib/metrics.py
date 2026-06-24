"""
SURVEY ETL METRICS — Módulo de cálculos matemáticos para encuestas.

Contiene funciones puras para el cálculo de Net Promoter Score (NPS)
y Customer Satisfaction Score (CSAT).
"""

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
    """
    if total == 0:
        return 0.0
    return round((t3b / total) * 100, 2)
