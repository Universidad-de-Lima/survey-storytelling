"""
ETL PIPELINE — Transforma y agrega datos de encuestas de Zoho Survey.

Importa mapeos centralizados, calcula métricas de NPS/CSAT,
clasifica tópicos cualitativos y genera archivos JSON de contratos de datos.
"""

import pandas as pd
import json
import re
import logging
import time
import zipfile
import csv as csv_mod
from pathlib import Path
from shutil import copyfile
from collections import defaultdict
from typing import Dict, List, Set

# Importar configuración, métricas, nlp e io_helpers modularizados
from lib.config import (
    COLUMN_RENAME_PREGRADO,
    COLUMN_RENAME_GRADUADO,
    CARRERA_FACULTAD,
    CATEGORIA_DIMENSION_PREGRADO,
    CATEGORIA_DIMENSION_GRADUADO,
    RESPUESTAS_TEXTO,
    CSAT_WEIGHTS,
    CSAT_SCALE_MAX,
    ETAPA_MAP,
    EMPLEABILIDAD_CATEGORIAS
)
from lib.metrics import calc_nps, calc_csat, calc_promedio_ponderado
from lib.nlp import sanitizar_comentario
from lib.segmentacion_nps import fragmentar_comentario_nps
from lib.io_helper import read_csv_robust, normalize_dates

# Configurar logging nativo de Python
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR.parent.parent / "data"
ZOHO_DIR: Path = BASE_DIR.parent
STUDENTS_DIR: Path = ZOHO_DIR / "students"

SURVEY_DIRS: Dict[str, Path] = {
    "undergraduate": STUDENTS_DIR / "undergraduate",
    "graduate": STUDENTS_DIR / "graduate",
    "posgraduate": STUDENTS_DIR / "posgraduate",
    "alumni-ug": ZOHO_DIR / "alumni" / "undergraduate",
    "alumni-pg": ZOHO_DIR / "alumni" / "posgraduate",
    "faculty-ug": ZOHO_DIR / "facultyStaff" / "undergraduate",
    "faculty-pg": ZOHO_DIR / "facultyStaff" / "posgraduate",
    "nonfaculty": ZOHO_DIR / "nonfacultyStaff",
    "employers": ZOHO_DIR / "employers",
}

SUPPORTED_EXTENSIONS: List[str] = [".csv"]


# ============================================================
# FUNCIONES EXTRAÍDAS (Fase 11: refactorización estructural)
# Funciones puras testeables extraídas de main() para mejorar mantenibilidad.
# NO cambian comportamiento: mismo CSV → mismo JSON.
# ============================================================

def _detectar_nivel(filename: str) -> str:
    """Detecta el nivel de encuesta desde el nombre del archivo.
    
    Usa substring matching sobre el filename en mayúsculas.
    Retorna el nivel o None si no se puede determinar.
    """
    filename_upper = filename.upper()
    if "NO DOCENTES" in filename_upper:
        return "nonfaculty"
    elif "EMPLEADORES" in filename_upper:
        return "employers"
    elif "EGRESADOS" in filename_upper:
        return "alumni-pg" if "POSGRADO" in filename_upper else "alumni-ug"
    elif "DOCENTES" in filename_upper:
        return "faculty-pg" if "POSGRADO" in filename_upper else "faculty-ug"
    elif "GRADUADOS" in filename_upper:
        return "graduate"
    elif "ESTUDIANTIL" in filename_upper or "ESTUDIANTES" in filename_upper:
        return "posgraduate" if "POSGRADO" in filename_upper else "undergraduate"
    else:
        return None


def _inyectar_html(template_index: Path, index_file: Path, periodo_dir: Path, zoho_dir: Path) -> bool:
    """Copia el template HTML al directorio del periodo, reemplazando {{SHARED_PATH}}.
    
    Retorna True si tuvo éxito con inyección, False si usó fallback (copyfile directo).
    """
    try:
        rel_parent = periodo_dir.relative_to(zoho_dir)
        depth = len(rel_parent.parts)
        shared_path = "/".join([".."] * depth) + "/shared"
        
        html_content = template_index.read_text(encoding="utf-8")
        html_content = html_content.replace("{{SHARED_PATH}}", shared_path)
        index_file.write_text(html_content, encoding="utf-8")
        logging.info(f"Plantilla HTML copiada e inyectada con shared_path '{shared_path}' para {periodo_dir.relative_to(zoho_dir)}")
        return True
    except Exception as html_err:
        logging.error(f"Error al escribir index.html con shared_path para {periodo_dir}: {html_err}")
        copyfile(template_index, index_file)
        return False


def _calcular_nps_carrera(df_nps, nps_col: str) -> list:
    """Calcula NPS por carrera desde df_nps.
    
    Retorna lista de dicts con: carrera, promotores, pasivos, detractores, score.
    """
    nps_carrera = []
    for carrera, sub in df_nps.groupby("Carrera"):
        p = int((sub[nps_col] >= 9).sum())
        pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
        d = int((sub[nps_col] <= 6).sum())
        nps_carrera.append({
            "carrera": carrera,
            "promotores": p,
            "pasivos": pa,
            "detractores": d,
            "score": calc_nps(p, pa, d)
        })
    return nps_carrera


def _calcular_csat_carrera(df, csat_col: str) -> list:
    """Calcula CSAT por carrera desde df.
    
    Retorna lista de dicts con: carrera, facultad, conteos por respuesta, score.
    """
    csat_carrera = []
    for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
        serie = sub[csat_col].dropna()
        row = {"carrera": car, "facultad": fac}
        for r in RESPUESTAS_TEXTO:
            row[r] = int((serie == r).sum())
        t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
        total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
        row["score"] = calc_csat(t3b, total)
        csat_carrera.append(row)
    return csat_carrera


def _construir_dashboard_data(
    resumen: dict,
    csat_score: float,
    nps_score: float,
    nps_etapas: dict,
    top_dims: list,
    top_facs: list,
    promotores_total: int,
    pasivos_total: int,
    detractores_total: int,
    serie_csat,
) -> dict:
    """Construye el objeto dashboard_data.json desde sus componentes.
    
    Recibe todas las métricas pre-calculadas y las ensambla en la estructura final.
    """
    return {
        "version": "2.0",
        "resumen": resumen,
        "hallazgos": {
            "csat_pct": int(csat_score),
            "nps_score": int(nps_score),
            "nps_tipo": "Excelente" if nps_score >= 60 else "Bueno" if nps_score >= 30 else "Regular" if nps_score >= 0 else "Pésimo",
            "nps_etapas": nps_etapas,
            "tendencia": "disminuye" if nps_etapas.get("Inicial", 0) > nps_etapas.get("Avanzado", 0)
                         else "aumenta" if nps_etapas.get("Inicial", 0) < nps_etapas.get("Avanzado", 0)
                         else "se mantiene",
            "delta": abs(int(nps_etapas.get("Inicial", 0) - nps_etapas.get("Avanzado", 0))),
            "top_dimensiones": top_dims,
            "top_facultades": top_facs
        },
        "nps": {
            "promotores": promotores_total,
            "pasivos": pasivos_total,
            "detractores": detractores_total,
            "score": nps_score
        },
        "csat": {r: int((serie_csat == r).sum()) for r in RESPUESTAS_TEXTO}
    }


def _hash_csv(csv_path: Path) -> str:
    """Calcula el hash SHA256 del contenido del CSV para detección de cambios."""
    import hashlib as _hl
    h = _hl.sha256()
    with open(csv_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _csv_cambiado(csv_path: Path, ruta_salida: Path) -> bool:
    """Detecta si un CSV cambió desde el último build comparando su hash.

    El hash se guarda en `<ruta_salida>/.csv_hash`. Si el archivo no existe
    (primer build) o el hash difiere, retorna True (procesar).
    Si el hash coincide, retorna False (saltar, los JSON ya están actualizados).
    """
    hash_file = ruta_salida / ".csv_hash"
    current_hash = _hash_csv(csv_path)
    if not hash_file.exists():
        return True
    try:
        saved_hash = hash_file.read_text(encoding="utf-8").strip()
        return saved_hash != current_hash
    except OSError:
        return True


def _guardar_hash_csv(csv_path: Path, ruta_salida: Path) -> None:
    """Guarda el hash del CSV para comparación en el próximo build."""
    hash_file = ruta_salida / ".csv_hash"
    try:
        hash_file.write_text(_hash_csv(csv_path), encoding="utf-8")
    except OSError as e:
        logging.warning(f"No se pudo guardar hash de CSV: {e}")


# ── Ayudantes de exportación CSV ──────────────────────────────────

def _sanitizar_nombre_csv(filename: str) -> str:
    """Convierte nombre de archivo CSV a formato limpio en minúsculas con guiones bajos.
    Ej: 'ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv'
        → 'encuesta_de_satisfaccion_estudiantil_pregrado_2026_1'
    """
    name = filename.replace(".csv", "").lower()
    name = re.sub(r"[^a-z0-9áéíóúñü]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _csv_escape(val) -> str:
    """Escapa un valor para CSV manejando comas, comillas dobles y saltos de línea."""
    s = str(val) if val is not None else ""
    if "," in s or '"' in s or "\n" in s or "\r" in s:
        return f'"{s.replace(chr(34), chr(34)+chr(34))}"'
    return s


def _generar_csvs_y_zip(
    df: pd.DataFrame,
    comentarios_detallados: list,
    ruta_salida: Path,
    csv_file: Path,
    nivel: str,
    categoria_dim: Dict[str, str],
    nps_col: str,
    csat_col: str,
    comentario_col: str,
) -> None:
    """Genera dos CSVs (analisis_cualitativo + respuestas_dimensiones) y los
    empaqueta en un ZIP dentro del directorio de salida."""
    import os as _os

    nombre_base = _sanitizar_nombre_csv(csv_file.name)
    fecha = pd.Timestamp.now().strftime("%Y-%m-%d")

    # ── Construir reverse mapping (renombrado → original) ──
    rev_pregrado = {v: k for k, v in COLUMN_RENAME_PREGRADO.items()}
    rev_graduado = {v: k for k, v in COLUMN_RENAME_GRADUADO.items()}
    rev_map = rev_graduado if nivel == "graduate" else rev_pregrado

    # ── CSV 1: analisis_cualitativo ──
    csv1_headers = [
        "ID", "CID", "Carrera", "Facultad", "Ciclo",
        "NPS Score", "Sentimiento", "Intensidad",
        "Tema", "Tema Padre",
        "Comentario Original", "Comentario Corregido"
    ]
    csv1_rows = []
    for c in comentarios_detallados:
        csv1_rows.append([
            (c.get("comentario_id_original", "") or "").rsplit("_", 1)[0] if "_" in (c.get("comentario_id_original", "") or "") else (c.get("comentario_id_original", "") or ""),
            c.get("id", ""),
            c.get("carrera", ""),
            c.get("facultad", ""),
            c.get("ciclo", ""),
            c.get("nps_score", ""),
            c.get("sentimiento", ""),
            c.get("intensidad", ""),
            c.get("aspecto_normalizado", ""),
            c.get("categoria_padre", ""),
            c.get("comentario_original", ""),
            c.get("fragmento_mostrar", ""),
        ])
    csv1_name = f"analisis_cualitativo_{nombre_base}_{fecha}.csv"

    # ── CSV 2: respuestas por dimensión ──
    # Identificar columnas de dimensión presentes en el DataFrame
    dim_cols_renamed = [d for d in categoria_dim.keys() if d in df.columns]
    # Mapear a nombres originales para cabeceras
    csv2_headers = ["ID", "Carrera"]
    if "Situación laboral" in df.columns:
        csv2_headers.append("Situación laboral")
    if "Tiempo laboral" in df.columns:
        csv2_headers.append("Tiempo laboral")
    csv2_headers.append("Facultad")
    if "Ciclo" in df.columns:
        csv2_headers.append("Ciclo")

    for d_renamed in dim_cols_renamed:
        csv2_headers.append(rev_map.get(d_renamed, d_renamed))

    # Añadir columnas fijas finales
    rev_carrera = rev_map.get("La carrera", "Tu carrera")
    csv2_headers.append(rev_carrera)
    csv2_headers.append(rev_map.get(csat_col, csat_col))
    csv2_headers.append(rev_map.get(nps_col, nps_col))
    csv2_headers.append("Comentario Original")

    csv2_rows = []
    # El comentario original se obtiene de la columna de comentario NPS
    comentario_df_col = comentario_col
    for _, row in df.iterrows():
        r = [
            row.get("ID", ""),
            row.get("Carrera", ""),
        ]
        if "Situación laboral" in df.columns:
            r.append(row.get("Situación laboral", ""))
        if "Tiempo laboral" in df.columns:
            r.append(row.get("Tiempo laboral", ""))
        r.append(row.get("Facultad", ""))
        if "Ciclo" in df.columns:
            r.append(row.get("Ciclo", ""))

        for d_renamed in dim_cols_renamed:
            r.append(row.get(d_renamed, ""))

        r.append(row.get("La carrera", ""))
        r.append(row.get(csat_col, ""))
        r.append(row.get(nps_col, ""))
        r.append(row.get(comentario_df_col, ""))
        csv2_rows.append(r)

    csv2_name = f"{nombre_base}_{fecha}.csv"
    zip_name = f"data_{nombre_base}_{fecha}.zip"

    # ── Escribir ZIP ──
    zip_path = ruta_salida / zip_name
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # CSV 1
            csv1_content = "\ufeff" + ",".join(csv1_headers) + "\n"
            csv1_content += "\n".join(
                ",".join(_csv_escape(v) for v in row) for row in csv1_rows
            )
            zf.writestr(csv1_name, csv1_content.encode("utf-8-sig"))

            # CSV 2
            csv2_content = "\ufeff" + ",".join(csv2_headers) + "\n"
            csv2_content += "\n".join(
                ",".join(_csv_escape(v) for v in row) for row in csv2_rows
            )
            zf.writestr(csv2_name, csv2_content.encode("utf-8-sig"))

        logging.info(f"📦 ZIP generado: {zip_name} ({len(csv1_rows)} comentarios, {len(csv2_rows)} encuestados)")
    except Exception as exc:
        logging.warning(f"No se pudo generar ZIP {zip_name}: {exc}")


def main() -> None:
    if not DATA_DIR.is_dir():
        logging.error(f"El directorio de datos de entrada no existe: {DATA_DIR}")
        return

    csv_files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and "ENCUESTA" in f.name.upper()
    ]

    if not csv_files:
        logging.warning("No se encontraron archivos CSV con el patrón 'ENCUESTA' en data/.")
        return

    periodos_por_nivel = defaultdict(set)
    _build_start = time.perf_counter()
    _timings: Dict[str, float] = {}

    for csv_file in csv_files:
        _csv_start = time.perf_counter()
        filename = csv_file.name.upper()
        logging.info(f"Iniciando procesamiento de: {csv_file.name}")

        # Detección del nivel de encuesta (Fase 11: delegado a _detectar_nivel)
        nivel = _detectar_nivel(filename)
        if nivel is None:
            logging.warning(f"No se pudo determinar el nivel para el archivo: {csv_file.name}")
            continue

        # Detección del periodo académico (año e.g. 2026-1)
        match = re.search(r"(20\d{2}(?:-[12])?)", filename)
        if not match:
            logging.warning(f"Omitiendo archivo: no contiene indicador de periodo en su nombre: {csv_file.name}")
            continue

        periodo: str = match.group()
        survey_dir = SURVEY_DIRS[nivel]
        periodos_por_nivel[nivel].add(periodo)

        ruta_salida: Path = survey_dir / periodo / "json"
        ruta_salida.mkdir(parents=True, exist_ok=True)

        # ── DETECCIÓN DE CSV MODIFICADO ──────────────────────────
        # Si el CSV no cambió desde el último build Y los JSON ya existen,
        # saltar el reprocesamiento completo (ahorra tiempo de CPU y ETL).
        # El caché IA (ia_cache.json) ya evita re-pagar DeepSeek; esto
        # adicionalmente evita releer el CSV, recalcular métricas y
        # reescribir JSONs idénticos.
        if not _csv_cambiado(csv_file, ruta_salida):
            jsons_existen = all(
                (ruta_salida / f"{j}.json").exists()
                for j in ["dashboard_data", "filtros", "dimensiones",
                          "nps_carrera", "nps_ciclo_carrera",
                          "csat_carrera", "csat_ciclo_carrera",
                          "sentimiento", "ids", "fragmentos_nps",
                          "dataset_cualitativo"]
            )
            if jsons_existen:
                logging.info(f"CSV sin cambios desde último build, saltando: {csv_file.name}")
                continue
            else:
                logging.info(f"CSV sin cambios pero faltan JSONs, reprocesando: {csv_file.name}")
        else:
            logging.info(f"CSV modificado o primer build, procesando: {csv_file.name}")

        periodo_dir: Path = survey_dir / periodo
        index_file: Path = periodo_dir / "index.html"
        template_index: Path = ZOHO_DIR / "template" / "index.html"

        # Inyección dinámica de la ruta a la carpeta shared (Fase 11: delegado a _inyectar_html)
        _inyectar_html(template_index, index_file, periodo_dir, ZOHO_DIR)

        # Lectura robusta de CSV
        try:
            df = read_csv_robust(csv_file)
        except Exception as exc:
            logging.error(f"Error crítico al leer {csv_file.name}: {exc}")
            continue

        # Limpiar headers
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        # Validación Temprana de Columnas Críticas en CSV
        columnas_criticas = ["ID de respuesta", "Net Promoter Score (de un total de 10)", "La Universidad de Lima"]
        if nivel == "graduate":
            columnas_criticas.append("¿Qué carrera profesional estudiaste?")
        else:
            columnas_criticas.append("¿Qué carrera profesional estudias?")

        columnas_faltantes = [c for c in columnas_criticas if c not in df.columns]
        if columnas_faltantes:
            logging.error(f"Archivo {csv_file.name} omitido: faltan columnas de negocio requeridas: {columnas_faltantes}")
            continue

        # Renombrar columnas
        column_rename = COLUMN_RENAME_GRADUADO if nivel == "graduate" else COLUMN_RENAME_PREGRADO
        df.rename(columns=column_rename, inplace=True)

        # Manejo de Ciclo
        tiene_ciclo: bool = "Ciclo" in df.columns
        if not tiene_ciclo:
            df["Ciclo"] = "NA"

        # Asignación de Facultad
        df["Facultad"] = df["Carrera"].map(CARRERA_FACULTAD)
        # Fallback genérico si alguna carrera no tiene mapeo
        df["Facultad"] = df["Facultad"].fillna("Programa de Estudios Generales" if nivel == "undergraduate" else "Otra")

        # Normalización de fechas de Inicio y Fin
        df = normalize_dates(df, ["Inicio", "Fin"])
        inicio = df["Inicio"].min()
        fin = max(df["Inicio"].max(), df["Fin"].max())
        if pd.isnull(inicio):
            inicio = pd.Timestamp.now()
        if pd.isnull(fin):
            fin = pd.Timestamp.now()

        anio = df["Inicio"].dt.year.mode()[0] if not df["Inicio"].empty else inicio.year
        fechas_unicas = df["Inicio"].dt.date.nunique() if not df["Inicio"].empty else 1

        # metricas NPS y CSAT globales
        nps_col: str = "Recomiendas la Universidad de Lima"
        df_nps = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna()
        df_nps[nps_col] = pd.to_numeric(df_nps[nps_col], errors="coerce")
        df_nps = df_nps.dropna(subset=[nps_col])

        promotores_total = int(df_nps[df_nps[nps_col] >= 9].shape[0])
        pasivos_total = int(df_nps[(df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)].shape[0])
        detractores_total = int(df_nps[df_nps[nps_col] <= 6].shape[0])
        nps_score = calc_nps(promotores_total, pasivos_total, detractores_total)

        csat_col: str = "La Universidad de Lima"
        serie_csat = df[csat_col].dropna()
        csat_t3b = int(serie_csat.isin(RESPUESTAS_TEXTO[:3]).sum())
        csat_t2b = int(serie_csat.isin(RESPUESTAS_TEXTO[:2]).sum())
        csat_total = int(serie_csat.isin(RESPUESTAS_TEXTO[:5]).sum())
        csat_score = calc_csat(csat_t3b, csat_total)
        # T2B reutiliza calc_csat (misma fórmula de box score, distinto subset).
        csat_t2b_pct = calc_csat(csat_t2b, csat_total)
        # Promedio Ponderado: conteos por nivel alineados a CSAT_WEIGHTS.
        csat_counts = [int((serie_csat == r).sum()) for r in RESPUESTAS_TEXTO[:5]]
        csat_ponderado = calc_promedio_ponderado(csat_counts, CSAT_WEIGHTS, CSAT_SCALE_MAX)

        # Métrica de Empleabilidad (solo graduados)
        empleabilidad = None
        if "Situación laboral" in df.columns:
            serie_emp = df["Situación laboral"].dropna()
            total_emp = len(serie_emp)
            if total_emp > 0:
                empleados = int(serie_emp.isin(EMPLEABILIDAD_CATEGORIAS).sum())
                empleabilidad = {
                    "score": round((empleados / total_emp) * 100, 2),
                    "empleados": empleados,
                    "total": total_emp
                }

        # NPS Carrera (Fase 11: delegado a _calcular_nps_carrera)
        nps_carrera = _calcular_nps_carrera(df_nps, nps_col)
        with open(ruta_salida / "nps_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_carrera, f, ensure_ascii=False, indent=2)

        # NPS Ciclo Carrera
        nps_ciclo_carrera: List[Dict[str, any]] = []
        if tiene_ciclo:
            for (fac, car, cic), sub in df_nps.groupby(["Facultad", "Carrera", "Ciclo"]):
                p = int((sub[nps_col] >= 9).sum())
                pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
                d = int((sub[nps_col] <= 6).sum())
                nps_ciclo_carrera.append({
                    "facultad": fac,
                    "carrera": car,
                    "ciclo": cic,
                    "promotores": p,
                    "pasivos": pa,
                    "detractores": d,
                    "score": calc_nps(p, pa, d)
                })
        with open(ruta_salida / "nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_ciclo_carrera, f, ensure_ascii=False)

        # CSAT Carrera (Fase 11: delegado a _calcular_csat_carrera)
        csat_carrera = _calcular_csat_carrera(df, csat_col)
        with open(ruta_salida / "csat_carrera.json", "w", encoding="utf-8") as f:
            json.dump(csat_carrera, f, ensure_ascii=False, indent=2)

        # CSAT Ciclo Carrera
        csat_ciclo_carrera: List[Dict[str, any]] = []
        if tiene_ciclo:
            for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
                serie = sub[csat_col].dropna()
                row = {"facultad": fac, "carrera": car, "ciclo": cic}
                for r in RESPUESTAS_TEXTO:
                    row[r] = int((serie == r).sum())
                t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
                total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
                row["score"] = calc_csat(t3b, total)
                csat_ciclo_carrera.append(row)
        with open(ruta_salida / "csat_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(csat_ciclo_carrera, f, ensure_ascii=False)

        # Dimensiones
        rows: List[Dict[str, any]] = []
        # Análisis Cualitativo Cuantitativo: Heatmap de Categorías (solo para survey)
        categoria_dim = CATEGORIA_DIMENSION_GRADUADO if nivel == "graduate" else CATEGORIA_DIMENSION_PREGRADO
        for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
            for dim, cat in categoria_dim.items():
                if dim not in sub.columns:
                    continue
                serie = sub[dim].dropna()
                conteos = {r: int((serie == r).sum()) for r in RESPUESTAS_TEXTO}
                t3b = conteos["Totalmente satisfecho"] + conteos["Muy satisfecho"] + conteos["Satisfecho"]
                b2b = conteos["Insatisfecho"] + conteos["Totalmente insatisfecho"]
                total = t3b + b2b
                rows.append({
                    "facultad": fac,
                    "carrera": car,
                    "ciclo": cic,
                    "categoria": cat,
                    "dimension": dim,
                    "t3b": t3b,
                    "b2b": b2b,
                    "total": total,
                    "t3b_pct": calc_csat(t3b, total),
                    "no_utilizo": conteos["No utilizo"],
                    "no_conozco": conteos["No conozco"],
                    **conteos
                })
        with open(ruta_salida / "dimensiones.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)

        # IDs
        ids_conteo: List[Dict[str, any]] = []
        for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
            ids_conteo.append({
                "facultad": fac,
                "carrera": car,
                "ciclo": cic,
                "total": int(len(sub))
            })
        with open(ruta_salida / "ids.json", "w", encoding="utf-8") as f:
            json.dump(ids_conteo, f, ensure_ascii=False, indent=2)

        # Agrupamiento NPS etapas (inicial, intermedio, avanzado)
        etapas: Dict[str, Dict[str, int]] = {}
        if tiene_ciclo:
            for ciclo, sub in df_nps.groupby("Ciclo"):
                p = int((sub[nps_col] >= 9).sum())
                pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
                d = int((sub[nps_col] <= 6).sum())
                ciclo_num = int("".join(filter(str.isdigit, ciclo)) or 0)
                etapa = ETAPA_MAP.get(ciclo_num, "Otro")
                if etapa not in etapas:
                    etapas[etapa] = {"p": 0, "pa": 0, "d": 0}
                etapas[etapa]["p"] += p
                etapas[etapa]["pa"] += pa
                etapas[etapa]["d"] += d

        nps_etapas = {etapa: calc_nps(v["p"], v["pa"], v["d"]) for etapa, v in etapas.items()}

        dim_agg = {}
        for r in rows:
            if r["dimension"] not in dim_agg:
                dim_agg[r["dimension"]] = {"t3b": 0, "total": 0}
            dim_agg[r["dimension"]]["t3b"] += r["t3b"]
            dim_agg[r["dimension"]]["total"] += r["total"]

        top_dims = sorted(
            [{"name": k, "score": calc_csat(v["t3b"], v["total"])} for k, v in dim_agg.items()],
            key=lambda x: x["score"], reverse=True
        )[:2]

        fac_agg = {}
        for item in csat_carrera:
            fac = item["facultad"]
            if fac not in fac_agg:
                fac_agg[fac] = {"t3b": 0, "total": 0}
            t3b = item["Totalmente satisfecho"] + item["Muy satisfecho"] + item["Satisfecho"]
            total = t3b + item["Insatisfecho"] + item["Totalmente insatisfecho"]
            fac_agg[fac]["t3b"] += t3b
            fac_agg[fac]["total"] += total

        top_facs = sorted(
            [{"name": k, "score": calc_csat(v["t3b"], v["total"])} for k, v in fac_agg.items()],
            key=lambda x: x["score"], reverse=True
        )[:2]

        resumen = {
            "encuestas": int(len(df)),
            "carreras": int(df["Carrera"].nunique()),
            "facultades": int(df["Facultad"].nunique()),
            "fecha_inicio": inicio.strftime("%Y-%m-%d"),
            "fecha_fin": fin.strftime("%Y-%m-%d"),
            "dias": int((fin - inicio).days + 1),
            "dias_recoleccion": fechas_unicas,
            "año": int(anio),
            "periodo": periodo,
            "nps": {
                "score": nps_score,
                "promotores": promotores_total,
                "pasivos": pasivos_total,
                "detractores": detractores_total,
                "total": promotores_total + pasivos_total + detractores_total
            },
            "csat": {
                "score": csat_score,
                "t3b": csat_t3b,
                "total": csat_total,
                "t2b": csat_t2b,
                "t2b_pct": csat_t2b_pct,
                "ponderado": csat_ponderado
            }
        }
        if empleabilidad:
            resumen["empleabilidad"] = empleabilidad

        # Generar dashboard_data.json (Fase 11: delegado a _construir_dashboard_data)
        dashboard_data = _construir_dashboard_data(
            resumen=resumen,
            csat_score=csat_score,
            nps_score=nps_score,
            nps_etapas=nps_etapas,
            top_dims=top_dims,
            top_facs=top_facs,
            promotores_total=promotores_total,
            pasivos_total=pasivos_total,
            detractores_total=detractores_total,
            serie_csat=serie_csat,
        )
        # Nombre sanitizado del CSV fuente para exportaciones
        dashboard_data["_export"] = {
            "nombre_encuesta": _sanitizar_nombre_csv(csv_file.name),
            "fecha_generacion": pd.Timestamp.now().strftime("%Y-%m-%d")
        }
        with open(ruta_salida / "dashboard_data.json", "w", encoding="utf-8") as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

        # Generar filtros.json
        filtros = {
            "version": "2.0",
            "has_ciclo": tiene_ciclo,
            "facultades": sorted(df["Facultad"].dropna().unique().tolist()),
            "carreras": sorted(df["Carrera"].dropna().unique().tolist()),
            "ciclos": sorted(df["Ciclo"].dropna().unique().tolist(),
                             key=lambda x: int("".join(filter(str.isdigit, x)) or 0)) if tiene_ciclo else [],
            "facultad_carrera": {
                fac: sorted(df[df["Facultad"] == fac]["Carrera"].unique().tolist())
                for fac in df["Facultad"].dropna().unique()
            }
        }
        with open(ruta_salida / "filtros.json", "w", encoding="utf-8") as f:
            json.dump(filtros, f, ensure_ascii=False, indent=2)

        # Análisis Cualitativo (sentimiento.json v3.0)
        comentario_col: str = "Comentario NPS"
        if comentario_col in df.columns:
            # Incluir csat_col (Satisfacción Global) si existe
            cols_to_extract = [comentario_col, nps_col, "Carrera", "Facultad", "Ciclo"]
            if csat_col in df.columns:
                cols_to_extract.append(csat_col)
                
            df_sent = df[cols_to_extract].copy()
            
            rename_dict = {
                comentario_col: "comentario",
                nps_col: "nps_score",
                "Carrera": "carrera",
                "Facultad": "facultad",
                "Ciclo": "ciclo"
            }
            if csat_col in df.columns:
                rename_dict[csat_col] = "satisfaccion_global"
                
            df_sent.rename(columns=rename_dict, inplace=True)
            
            # Si la columna ID de respuesta existe, agregarla
            if "ID de respuesta" in df.columns:
                df_sent["ID"] = df["ID de respuesta"]
            elif "ID" in df.columns:
                df_sent["ID"] = df["ID"]

            df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"])

            # ================================================================
            # ANALISIS CUALITATIVO CON IA (DeepSeek) - Fase IA
            # Configuración centralizada en lib/config.py → IA_CUALITATIVO_MODE.
            # Activar con: DEEPSEEK_API_KEY en entorno (GitHub Actions Secret).
            # Forzar legacy: IA_CUALITATIVO_FALLBACK=1 o IA_CUALITATIVO_MODE="legacy".
            # Fallback automatico al pipeline legacy si la key no esta.
            # ================================================================
            import os as _os
            _use_ia_cualitativo = bool(_os.environ.get("DEEPSEEK_API_KEY", "")) and _os.environ.get("IA_CUALITATIVO_FALLBACK", "0") != "1"
            
            if _use_ia_cualitativo:
                logging.info("Modo IA Cualitativo ACTIVADO (DeepSeek). Pipeline legacy omitido.")
                from lib.config import CATEGORIA_DIMENSION_PREGRADO as _TAX, DIMENSIONES_SIN_CSAT
                from lib.ia_cualitativo import generar_salidas_cualitativas_ia
            
                # Merge columnas CSAT por dimension en df_sent (para cross-reference)
                _dimension_cols = [d for d in _TAX.keys()
                                   if d in df.columns and d not in DIMENSIONES_SIN_CSAT]
                for _dc in _dimension_cols:
                    if _dc not in df_sent.columns:
                        df_sent[_dc] = df[_dc]
                _csat_cols_map = {d: d for d in _dimension_cols}
            
                _cache_path = BASE_DIR / "ia_cache.json"
                datos_fragmentos, dataset_cualitativo, _ia_metadata = (
                    generar_salidas_cualitativas_ia(
                        df_sent=df_sent,
                        taxonomia=_TAX,
                        csat_columns_map=_csat_cols_map,
                        cache_path=_cache_path,
                    )
                )
            
                # Escribir fragmentos_nps.json (formato compatible con el legado)
                fragmentos_payload = {
                    "metadata": {
                        "version": "2.0",
                        "motor": "deepseek",
                        "total_encuestas": len(datos_fragmentos),
                        "total_fragmentos": sum(len(d["fragmentos"]) for d in datos_fragmentos)
                    },
                    "data": datos_fragmentos
                }
                with open(ruta_salida / "fragmentos_nps.json", "w", encoding="utf-8") as f_frag:
                    json.dump(fragmentos_payload, f_frag, ensure_ascii=False, indent=2)
            
                # Escribir dataset_cualitativo.json
                cualitativo_payload = {"metadata": _ia_metadata, "data": dataset_cualitativo}
                with open(ruta_salida / "dataset_cualitativo.json", "w", encoding="utf-8") as f_cual:
                    json.dump(cualitativo_payload, f_cual, ensure_ascii=False, indent=2)
            
                # Stats para compatibilidad con codigo downstream
                stats_aspectos = {"alias": 0, "embedding": 0, "embedding_fallback": 0, "fallback": 0, "ninguno": 0, "total": len(dataset_cualitativo)}
                stats_sentimiento = _ia_metadata["stats_sentimiento"]
                _ia_msg = f"IA Cualitativo: {_ia_metadata['total_encuestas']} encuestas, {_ia_metadata['total_fragmentos']} unidades, {_ia_metadata['cache_hits']} cache hits, {_ia_metadata['usage']['total_tokens']} tokens."
                logging.info(_ia_msg)
            
            if not _use_ia_cualitativo:
                # ---- GENERAR fragmentos_nps.json ----
                logging.info("Generando fragmentos_nps.json con modelo híbrido...")
                datos_fragmentos = []
                for idx_f, row_f in df_sent.iterrows():
                    comentario_orig = str(row_f["comentario"])
                    if not comentario_orig.strip():
                        continue
                
                    nps = int(row_f["nps_score"])
                    seg_nps = "Promotor" if nps >= 9 else ("Pasivo" if nps >= 7 else "Detractor")
                    res_id = str(row_f.get("ID", f"R_{idx_f}"))
                
                    lista_frags = fragmentar_comentario_nps(comentario_orig, sanitizar_func=sanitizar_comentario)
                
                    if lista_frags:
                        fragmentos_objetos = []
                        for i_f, fr in enumerate(lista_frags):
                            fragmentos_objetos.append({
                                "id_fragmento": f"{res_id}_{i_f+1:02d}",
                                "texto": fr
                            })
                        
                        datos_fragmentos.append({
                            "id_encuesta": res_id,
                            "facultad": str(row_f.get("facultad", "")),
                            "carrera": str(row_f.get("carrera", "")),
                            "ciclo": str(row_f.get("ciclo", "")),
                            "nps_score": nps,
                            "segmento_nps": seg_nps,
                            "satisfaccion_global": str(row_f.get("satisfaccion_global", "No respondido")),
                            "comentario_original": comentario_orig,
                            "fragmentos": fragmentos_objetos
                        })
            
                fragmentos_payload = {
                    "metadata": {
                        "version": "1.0",
                        "total_encuestas": len(datos_fragmentos),
                        "total_fragmentos": sum(len(d["fragmentos"]) for d in datos_fragmentos)
                    },
                    "data": datos_fragmentos
                }
                with open(ruta_salida / "fragmentos_nps.json", "w", encoding="utf-8") as f:
                    json.dump(fragmentos_payload, f, ensure_ascii=False, indent=2)

                # ---- GENERAR dataset_cualitativo.json ----
                logging.info("Generando dataset_cualitativo.json con extracción y normalización de aspectos...")
                from lib.aspect_extraction import procesar_opinion_unit
                from lib.sentiment_engine import analizar_sentimiento_intensidad
            
                dataset_cualitativo = []
            
                # Recolectar metricas empiricas
                stats_aspectos = {
                    "alias": 0,
                    "embedding": 0,
                    "embedding_fallback": 0,
                    "fallback": 0,
                    "ninguno": 0,
                    "total": 0
                }
                stats_sentimiento = {
                    "total_opinion_units": 0,
                    "positivos": 0,
                    "negativos": 0,
                    "neutros": 0,
                    "confianza_promedio": 0.0,
                    "intensidad_promedio": 0.0
                }
                suma_confianza = 0.0
                suma_intensidad = 0.0
            
                for d in datos_fragmentos:
                    for f in d["fragmentos"]:
                        res = procesar_opinion_unit(f["texto"])
                        stats_aspectos[res["metodo"]] += 1
                        stats_aspectos["total"] += 1
                    
                        sent_res = analizar_sentimiento_intensidad(f["texto"])
                    
                        stats_sentimiento["total_opinion_units"] += 1
                        sent_val = sent_res["sentimiento"]
                        if sent_val == "positivo": stats_sentimiento["positivos"] += 1
                        elif sent_val == "negativo": stats_sentimiento["negativos"] += 1
                        else: stats_sentimiento["neutros"] += 1
                    
                        suma_confianza += sent_res["confianza_sentimiento"]
                        suma_intensidad += sent_res["intensidad"]
                    
                        dataset_cualitativo.append({
                            "id_encuesta": d["id_encuesta"],
                            "id_fragmento": f["id_fragmento"],
                            "facultad": d["facultad"],
                            "carrera": d["carrera"],
                            "ciclo": d["ciclo"],
                            "nps_score": d["nps_score"],
                            "segmento_nps": d["segmento_nps"],
                            "satisfaccion_global": d["satisfaccion_global"],
                            "texto": f["texto"],
                            "aspecto_detectado": res["aspecto_detectado"],
                            "aspecto_normalizado": res["aspecto_normalizado"],
                            "categoria_padre": res["categoria_padre"],
                            "sub_aspectos": res.get("sub_aspectos", []),
                            "sentimiento": sent_res["sentimiento"],
                            "intensidad": sent_res["intensidad"],
                            "confianza_sentimiento": sent_res["confianza_sentimiento"],
                            "comentario_original": d["comentario_original"]
                        })
                    
                if stats_sentimiento["total_opinion_units"] > 0:
                    stats_sentimiento["confianza_promedio"] = round(suma_confianza / stats_sentimiento["total_opinion_units"], 4)
                    stats_sentimiento["intensidad_promedio"] = round(suma_intensidad / stats_sentimiento["total_opinion_units"], 2)
                    
                logging.info(f"Metricas de normalizacion: Alias {stats_aspectos['alias']}, Embedding {stats_aspectos['embedding']}, Embedding Fallback {stats_aspectos['embedding_fallback']}, Fallback {stats_aspectos['fallback']}")
                logging.info(f"Metricas sentimiento: POS {stats_sentimiento['positivos']}, NEG {stats_sentimiento['negativos']}, NEU {stats_sentimiento['neutros']}")
            
                cualitativo_payload = {
                    "metadata": {
                        "version": "1.0",
                        "total_encuestas": len(datos_fragmentos),
                        "total_fragmentos": len(dataset_cualitativo),
                        "stats_normalizacion": stats_aspectos,
                        "stats_sentimiento": stats_sentimiento
                    },
                    "data": dataset_cualitativo
                }
                with open(ruta_salida / "dataset_cualitativo.json", "w", encoding="utf-8") as f_cual:
                    json.dump(cualitativo_payload, f_cual, ensure_ascii=False, indent=2)
            # ------------------------------------------
            # Migración: Conectar el Motor Nuevo (dataset_cualitativo) a la UI
            # Fase IA v3: filtrar unidades inválidas (es_valido=false) para que
            # NO se muestren en el dashboard. Solo se incluyen en dataset_cualitativo.json
            # para trazabilidad, pero no en sentimiento.json (que alimenta la UI).
            comentarios_detallados = []
            topicos_dict = {}

            for item in dataset_cualitativo:
                # Fase IA v3: respetar es_valido del dataset; filtrar inválidas de la UI
                es_valido_item = item.get("es_valido", True)
                if not es_valido_item:
                    continue  # NO se muestra en el dashboard

                frag_sec = int(item["id_fragmento"].split("_")[-1]) if "_" in item["id_fragmento"] else 1
                com_obj = {
                    "id": item["id_fragmento"],
                    "carrera": item["carrera"],
                    "facultad": item["facultad"],
                    "ciclo": item["ciclo"],
                    "nps_score": item["nps_score"],
                    "sentimiento": item["sentimiento"],
                    "intensidad": item["intensidad"],
                    "categoria": item["aspecto_normalizado"],
                    "categoria_padre": item["categoria_padre"],
                    "fragmento_original": item["texto"],
                    "fragmento_mostrar": item["texto"],
                    "es_valido": True,
                    "motivo_invalidez": None,
                    "comentario_original": item.get("comentario_original", ""),
                    "comentario_id_original": item["id_encuesta"],
                    "fragmento_secuencia": frag_sec,
                    "es_fragmento": True,
                    "aspecto_normalizado": item["aspecto_normalizado"]
                }
                comentarios_detallados.append(com_obj)

                t = item["aspecto_normalizado"]
                if t not in topicos_dict:
                    topicos_dict[t] = {"total": 0, "positivo": 0, "negativo": 0, "neutro": 0}
                topicos_dict[t]["total"] += 1
                topicos_dict[t][item["sentimiento"]] += 1

            topicos_globales = []
            for t, stats in topicos_dict.items():
                topicos_globales.append({
                    "topico": t,
                    "total_comentarios": stats["total"],
                    "positivos": stats["positivo"],
                    "negativos": stats["negativo"],
                    "neutros": stats["neutro"]
                })
            topicos_globales.sort(key=lambda x: x["total_comentarios"], reverse=True)

            # Contadores
            total_con_com = int(len(df_sent))
            valid_comments = comentarios_detallados
            ids_con_comentarios_validos = set([c["comentario_id_original"] for c in valid_comments])
            total_invalidos = total_con_com - len(ids_con_comentarios_validos)
            
            total_analizados = len(valid_comments)
            
            pasivos_con_com = sum(1 for c in valid_comments if 7 <= c["nps_score"] <= 8)
            detractores_con_com = sum(1 for c in valid_comments if c["nps_score"] <= 6)
            
            # Distribución sentiment/intensity
            dist_sent = {"positivo": 0, "neutro": 0, "negativo": 0}
            for c in valid_comments:
                dist_sent[c["sentimiento"]] += 1
                
            dist_int = {"alta": 0, "media": 0, "baja": 0}
            for c in valid_comments:
                val = c["intensidad"]
                if val >= 4.0:
                    dist_int["alta"] += 1
                elif val >= 2.5:
                    dist_int["media"] += 1
                else:
                    dist_int["baja"] += 1

            # Distribución por carrera
            por_carrera: List[Dict[str, any]] = []
            for car, sub in df_sent.groupby("carrera"):
                valid_sub = [c for c in comentarios_detallados if c["carrera"] == car and c["es_valido"]]
                invalid_sub = [c for c in comentarios_detallados if c["carrera"] == car and not c["es_valido"]]
                por_carrera.append({
                    "carrera": car,
                    "facultad": sub["facultad"].iloc[0] if not sub.empty else "",
                    "total": len(valid_sub),
                    "pasivos": sum(1 for c in valid_sub if 7 <= c["nps_score"] <= 8),
                    "detractores": sum(1 for c in valid_sub if c["nps_score"] <= 6),
                    "comentarios_invalidos": len(invalid_sub)
                })
            por_carrera.sort(key=lambda x: x["total"], reverse=True)

            # Distribución por ciclo
            por_ciclo: List[Dict[str, any]] = []
            for cic, sub in df_sent.groupby("ciclo"):
                valid_sub = [c for c in comentarios_detallados if c["ciclo"] == cic and c["es_valido"]]
                por_ciclo.append({
                    "ciclo": cic,
                    "total": len(valid_sub),
                    "pasivos": sum(1 for c in valid_sub if 7 <= c["nps_score"] <= 8),
                    "detractores": sum(1 for c in valid_sub if c["nps_score"] <= 6)
                })
            por_ciclo.sort(key=lambda x: int("".join(filter(str.isdigit, x["ciclo"])) or 0))

            # Generar Insights Narrativos (Fase 8: vía lib/insights_generator.py)
            # Reemplaza templates hardcodeados por heurísticas deterministas.
            # Excluye "Pendiente de Clasificación" de temas relevantes.
            # Cubre las 7 categorías padre oficiales (no 4 como antes).
            from lib.insights_generator import generar_insights_ia
            insights_ia = generar_insights_ia(
                valid_comments=valid_comments,
                topicos_globales=topicos_globales,
                dist_sent=dist_sent,
                total_analizados=total_analizados,
            )

            sentimiento = {
                "version": "3.0",
                "resumen": {
                    "total_respuestas": total_con_com,
                    "total_con_comentario": total_con_com,
                    "total_analizados": total_analizados,
                    "comentarios_invalidos": total_invalidos,
                    "distribucion_sentimiento": dist_sent,
                    "distribucion_intensidad": dist_int,
                    "pasivos": pasivos_con_com,
                    "detractores": detractores_con_com,
                    "nota": "Se analizan y clasifican semánticamente todos los comentarios libres ingresados en la encuesta."
                },
                "insights_ia": insights_ia,
                "topicos": topicos_globales,
                "comentarios": comentarios_detallados,
                "por_carrera": por_carrera,
                "por_ciclo": por_ciclo
            }
        else:
            sentimiento = {
                "version": "3.0",
                "resumen": {
                    "total_respuestas": 0,
                    "total_con_comentario": 0,
                    "total_analizados": 0,
                    "comentarios_invalidos": 0,
                    "distribucion_sentimiento": {"positivo": 0, "neutro": 0, "negativo": 0},
                    "distribucion_intensidad": {"alta": 0, "media": 0, "baja": 0},
                    "pasivos": 0,
                    "detractores": 0,
                    "nota": "No se encontró la columna de comentarios NPS en los datos."
                },
                "insights_ia": {
                    "global": "No hay datos de comentarios disponibles.",
                    "por_categoria_padre": {}
                },
                "topicos": [],
                "comentarios": [],
                "por_carrera": [],
                "por_ciclo": []
            }

        # Guardar únicamente en sentimiento.json (formato v3.0 consolidado y minificado)
        with open(ruta_salida / "sentimiento.json", "w", encoding="utf-8") as f:
            json.dump(sentimiento, f, ensure_ascii=False)

        # Generar CSVs y ZIP (solo si hay datos cualitativos)
        if comentario_col in df.columns and len(comentarios_detallados) > 0:
            try:
                _generar_csvs_y_zip(
                    df=df,
                    comentarios_detallados=comentarios_detallados,
                    ruta_salida=ruta_salida,
                    csv_file=csv_file,
                    nivel=nivel,
                    categoria_dim=categoria_dim,
                    nps_col=nps_col,
                    csat_col=csat_col,
                    comentario_col=comentario_col,
                )
            except Exception as exc:
                logging.warning(f"No se pudieron generar los CSVs de exportación: {exc}")

        logging.info(f"Procesamiento finalizado con éxito para {nivel}/{periodo}.")
        _csv_elapsed = time.perf_counter() - _csv_start
        _timings[f"{nivel}/{periodo}"] = _csv_elapsed
        logging.info(f"⏱️ Tiempo de procesamiento para {nivel}/{periodo}: {_csv_elapsed:.1f}s")

        # Guardar hash del CSV para saltar reprocesamiento en el próximo build
        # si el CSV no cambia. Solo se guarda si el procesamiento fue exitoso.
        _guardar_hash_csv(csv_file, ruta_salida)

    # =========================================================
    # Actualizar periodos.json automáticamente por nivel
    # =========================================================
    _total_elapsed = time.perf_counter() - _build_start
    logging.info(f"⏱️ Build completado en {_total_elapsed:.1f}s | {len(_timings)} archivos procesados")
    for _k, _v in sorted(_timings.items(), key=lambda x: x[1], reverse=True):
        logging.info(f"   {_k}: {_v:.1f}s")

    def clave_periodo(p: str):
        parts = p.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return (int(parts[0]), int(parts[1]))
        return (0, 0)

    for lvl, periodos in periodos_por_nivel.items():
        if not periodos:
            continue
        periodos_ordenados = sorted(list(periodos), key=clave_periodo)
        ultimo_periodo = periodos_ordenados[-1]

        periodos_json = []
        for p in periodos_ordenados:
            periodos_json.append({
                "id": p,
                "label": p,
                "isNew": p == ultimo_periodo
            })

        path_periodos = SURVEY_DIRS[lvl] / "periodos.json"
        try:
            with open(path_periodos, "w", encoding="utf-8") as f:
                json.dump(periodos_json, f, ensure_ascii=False, indent=2)
            logging.info(f"periodos.json actualizado automáticamente para {lvl}.")
        except Exception as e:
            logging.error(f"Error al escribir periodos.json en {path_periodos}: {e}")


if __name__ == "__main__":
    main()
