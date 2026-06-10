"""
SURVEY ETL IO HELPER — Módulo de utilidades de entrada y salida de archivos.

Proporciona funciones para lectura segura de archivos JSON, lectura robusta
de CSVs (con detección específica de encoding) y normalización de campos fecha.
"""

import json
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def load_json(path: Path) -> any:
    """
    Carga de forma segura un archivo JSON con soporte para UTF-8 BOM.
    Lanza ValueError detallados en caso de fallo.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"no se pudo leer el archivo JSON: {exc}") from exc

    if not text.strip():
        raise ValueError("el archivo JSON está vacío")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"formato JSON inválido: {exc}") from exc


def read_csv_robust(path: Path) -> "pd.DataFrame":
    """
    Intenta leer un archivo CSV en UTF-8 y hace fallback a latin-1
    específicamente en caso de fallos de decodificación (UnicodeDecodeError).
    """
    import pandas as pd  # Lazy import para desacoplar dependencias en validadores
    
    if not path.is_file():
        raise FileNotFoundError(f"El archivo CSV no existe en la ruta: {path}")
        
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback controlado ante problemas de encoding en español
        return pd.read_csv(path, encoding="latin-1")


def normalize_dates(df: "pd.DataFrame", columns: List[str]) -> "pd.DataFrame":
    """
    Normaliza formatos de fecha localizados de Zoho Survey (español) a Datetime.
    Mapea meses en español a inglés y corrige el formato de AM/PM.
    """
    import pandas as pd  # Lazy import para desacoplar dependencias en validadores
    
    meses_es = {
        "ene.": "January", "feb.": "February", "mar.": "March", "abr.": "April",
        "may.": "May", "jun.": "June", "jul.": "July", "ago.": "August",
        "sep.": "September", "oct.": "October", "nov.": "November", "dic.": "December"
    }
    
    df_copy = df.copy()
    for col in columns:
        if col not in df_copy.columns:
            continue
            
        # Reemplazar abreviaciones de meses
        for es, en in meses_es.items():
            df_copy[col] = df_copy[col].str.replace(es, en, regex=False)
            
        # Formatear AM/PM de Zoho: "p. m." -> "PM", "a. m." -> "AM"
        df_copy[col] = df_copy[col].str.replace(r"p.\s*m\.", "PM", regex=True)
        df_copy[col] = df_copy[col].str.replace(r"a.\s*m\.", "AM", regex=True)
        
        # Conversión a datetime
        df_copy[col] = pd.to_datetime(df_copy[col], dayfirst=True, errors="coerce")
        
    return df_copy
