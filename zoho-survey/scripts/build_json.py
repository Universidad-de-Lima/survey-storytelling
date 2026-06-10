"""
ETL PIPELINE — Transforma y agrega datos de encuestas de Zoho Survey.

Importa mapeos centralizados, calcula métricas de NPS/CSAT,
clasifica tópicos cualitativos y genera archivos JSON de contratos de datos.
"""

import pandas as pd
import json
import re
import logging
from pathlib import Path
from shutil import copyfile
from collections import defaultdict
from typing import Dict, List, Set

# Importar configuración, métricas, nlp e io_helpers modularizados
from lib.config import (
    COLUMN_RENAME_PREGRADO,
    COLUMN_RENAME_POSGRADO,
    CARRERA_FACULTAD,
    CATEGORIA_DIMENSION_PREGRADO,
    CATEGORIA_DIMENSION_POSGRADO,
    RESPUESTAS_TEXTO,
    ETAPA_MAP,
    EMPLEABILIDAD_CATEGORIAS
)
from lib.metrics import calc_nps, calc_csat
from lib.nlp import agrupar_comentarios_por_topico
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

    for csv_file in csv_files:
        filename = csv_file.name.upper()
        logging.info(f"Iniciando procesamiento de: {csv_file.name}")

        # Detección del nivel de encuesta
        if "NO DOCENTES" in filename:
            nivel = "nonfaculty"
        elif "EMPLEADORES" in filename:
            nivel = "employers"
        elif "EGRESADOS" in filename:
            nivel = "alumni-pg" if "POSGRADO" in filename else "alumni-ug"
        elif "DOCENTES" in filename:
            nivel = "faculty-pg" if "POSGRADO" in filename else "faculty-ug"
        elif "GRADUADOS" in filename:
            nivel = "graduate"
        elif "ESTUDIANTIL" in filename or "ESTUDIANTES" in filename:
            nivel = "posgraduate" if "POSGRADO" in filename else "undergraduate"
        else:
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

        periodo_dir: Path = survey_dir / periodo
        index_file: Path = periodo_dir / "index.html"
        template_index: Path = ZOHO_DIR / "template" / "index.html"
        copyfile(template_index, index_file)
        logging.info(f"Plantilla HTML copiada para {nivel}/{periodo}")

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
        column_rename = COLUMN_RENAME_POSGRADO if nivel == "graduate" else COLUMN_RENAME_PREGRADO
        df.rename(columns=column_rename, inplace=True)

        # Manejo de Ciclo
        tiene_ciclo: bool = "Ciclo" in df.columns
        if not tiene_ciclo:
            df["Ciclo"] = "NA"

        # Asignación de Facultad
        df["Facultad"] = df["Carrera"].map(CARRERA_FACULTAD)
        # Fallback genérico si alguna carrera no tiene mapeo
        df["Facultad"] = df["Facultad"].fillna("Facultad de Estudios Generales" if nivel == "undergraduate" else "Otra")

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
        csat_total = int(serie_csat.isin(RESPUESTAS_TEXTO[:5]).sum())
        csat_score = calc_csat(csat_t3b, csat_total)

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

        # NPS Carrera
        nps_carrera: List[Dict[str, any]] = []
        for carrera, sub in df_nps.groupby("Carrera"):
            p = int((sub[nps_col] >= 9).sum())
            pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
            d = int((sub[nps_col] <= 6).sum())
            nps_carrera.append({
                "carrera": carrera,
                "Promotores": p,
                "Pasivos": pa,
                "Detractores": d,
                "score": calc_nps(p, pa, d)
            })
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
                    "Promotores": p,
                    "Pasivos": pa,
                    "Detractores": d,
                    "score": calc_nps(p, pa, d)
                })
        with open(ruta_salida / "nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_ciclo_carrera, f, ensure_ascii=False, indent=2)

        # CSAT Carrera
        csat_carrera: List[Dict[str, any]] = []
        for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
            serie = sub[csat_col].dropna()
            row = {"carrera": car, "facultad": fac}
            for r in RESPUESTAS_TEXTO:
                row[r] = int((serie == r).sum())
            t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
            total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
            row["score"] = calc_csat(t3b, total)
            csat_carrera.append(row)
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
            json.dump(csat_ciclo_carrera, f, ensure_ascii=False, indent=2)

        # Dimensiones
        rows: List[Dict[str, any]] = []
        categoria_dim = CATEGORIA_DIMENSION_POSGRADO if nivel == "graduate" else CATEGORIA_DIMENSION_PREGRADO
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
            json.dump(rows, f, ensure_ascii=False, indent=2)

        # IDs
        ids_conteo: List[Dict[str, any]] = []
        for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
            ids_conteo.append({
                "facultad": fac,
                "carrera": car,
                "ciclo": cic,
                "count": int(len(sub))
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
                "total": csat_total
            }
        }
        if empleabilidad:
            resumen["empleabilidad"] = empleabilidad

        # Generar dashboard_data.json
        dashboard_data = {
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
                "Promotores": promotores_total,
                "Pasivos": pasivos_total,
                "Detractores": detractores_total,
                "score": nps_score
            },
            "csat": {r: int((serie_csat == r).sum()) for r in RESPUESTAS_TEXTO}
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

        # Análisis Cualitativo (sentimiento.json)
        comentario_col: str = "Comentario NPS"
        if comentario_col in df.columns:
            df_sent = df[[comentario_col, nps_col, "Carrera", "Facultad", "Ciclo"]].copy()
            df_sent.columns = ["comentario", "nps_score", "carrera", "facultad", "ciclo"]
            df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent = df_sent[df_sent["comentario"].str.strip().str.len() > 5]
            df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"])

            df_pasivos_detractores = df_sent[df_sent["nps_score"] < 9]
            total_con_comentario = int(len(df_sent))
            total_analizados = int(len(df_pasivos_detractores))
            detractores_con_com = int((df_pasivos_detractores["nps_score"] <= 6).sum())
            pasivos_con_com = int(df_pasivos_detractores["nps_score"].between(7, 8).sum())

            # Agrupación y clasificación mediante módulo NLP
            topicos_globales = agrupar_comentarios_por_topico(df_pasivos_detractores)

            # Distribución por carrera
            por_carrera: List[Dict[str, any]] = []
            for car, sub in df_pasivos_detractores.groupby("carrera"):
                por_carrera.append({
                    "carrera": car,
                    "facultad": sub["facultad"].iloc[0] if not sub.empty else "",
                    "total": int(len(sub)),
                    "pasivos": int(sub["nps_score"].between(7, 8).sum()),
                    "detractores": int((sub["nps_score"] <= 6).sum())
                })
            por_carrera.sort(key=lambda x: x["total"], reverse=True)

            # Distribución por ciclo
            por_ciclo: List[Dict[str, any]] = []
            for cic, sub in df_pasivos_detractores.groupby("ciclo"):
                por_ciclo.append({
                    "ciclo": cic,
                    "total": int(len(sub)),
                    "pasivos": int(sub["nps_score"].between(7, 8).sum()),
                    "detractores": int((sub["nps_score"] <= 6).sum())
                })
            por_ciclo.sort(key=lambda x: int("".join(filter(str.isdigit, x["ciclo"])) or 0))

            sentimiento = {
                "version": "2.0",
                "resumen": {
                    "total_con_comentario": total_con_comentario,
                    "total_analizados": total_analizados,
                    "pasivos": pasivos_con_com,
                    "detractores": detractores_con_com,
                    "nota": "Solo se analizan comentarios de Pasivos (7-8) y Detractores (0-6). Los Promotores (9-10) no responden esta pregunta."
                },
                "topicos": topicos_globales,
                "por_carrera": por_carrera,
                "por_ciclo": por_ciclo
            }
        else:
            sentimiento = {
                "version": "2.0",
                "resumen": {
                    "total_con_comentario": 0,
                    "total_analizados": 0,
                    "pasivos": 0,
                    "detractores": 0,
                    "nota": "No se encontró la columna de comentarios NPS en los datos."
                },
                "topicos": [],
                "por_carrera": [],
                "por_ciclo": []
            }

        with open(ruta_salida / "sentimiento.json", "w", encoding="utf-8") as f:
            json.dump(sentimiento, f, ensure_ascii=False, indent=2)

        logging.info(f"Procesamiento finalizado con éxito para {nivel}/{periodo}.")

    # =========================================================
    # Actualizar periodos.json automáticamente por nivel
    # =========================================================
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
