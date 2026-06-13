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
from lib.nlp import agrupar_comentarios_por_topico, sanitizar_comentario
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
        
        # Inyección dinámica de la ruta a la carpeta shared según la profundidad (H-01)
        try:
            rel_parent = periodo_dir.relative_to(ZOHO_DIR)
            depth = len(rel_parent.parts)
            shared_path = "/".join([".."] * depth) + "/shared"
            
            html_content = template_index.read_text(encoding="utf-8")
            html_content = html_content.replace("{{SHARED_PATH}}", shared_path)
            index_file.write_text(html_content, encoding="utf-8")
            logging.info(f"Plantilla HTML copiada e inyectada con shared_path '{shared_path}' para {nivel}/{periodo}")
        except Exception as html_err:
            logging.error(f"Error al escribir index.html con shared_path para {nivel}/{periodo}: {html_err}")
            copyfile(template_index, index_file)

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
                "promotores": p,
                "pasivos": pa,
                "detractores": d,
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
                    "promotores": p,
                    "pasivos": pa,
                    "detractores": d,
                    "score": calc_nps(p, pa, d)
                })
        with open(ruta_salida / "nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_ciclo_carrera, f, ensure_ascii=False)

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
            json.dump(csat_ciclo_carrera, f, ensure_ascii=False)

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
                "promotores": promotores_total,
                "pasivos": pasivos_total,
                "detractores": detractores_total,
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

        # Análisis Cualitativo (sentimiento.json v3.0)
        comentario_col: str = "Comentario NPS"
        if comentario_col in df.columns:
            df_sent = df[[comentario_col, nps_col, "Carrera", "Facultad", "Ciclo"]].copy()
            df_sent.columns = ["comentario", "nps_score", "carrera", "facultad", "ciclo"]
            
            # Si la columna ID de respuesta existe, agregarla
            if "ID de respuesta" in df.columns:
                df_sent["ID"] = df["ID de respuesta"]
            elif "ID" in df.columns:
                df_sent["ID"] = df["ID"]

            df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"])

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
            # -------------------------------------

            # Agrupación y clasificación mediante módulo NLP local
            topicos_globales, comentarios_detallados = agrupar_comentarios_por_topico(df_sent)

            # Contadores
            total_con_com = int(len(df_sent))
            valid_comments = [c for c in comentarios_detallados if c["es_valido"]]
            invalid_comments = [c for c in comentarios_detallados if not c["es_valido"]]
            
            total_analizados = len(valid_comments)
            total_invalidos = len(invalid_comments)
            
            pasivos_con_com = sum(1 for c in valid_comments if 7 <= c["nps_score"] <= 8)
            detractores_con_com = sum(1 for c in valid_comments if c["nps_score"] <= 6)
            
            # Distribución sentiment/intensity
            dist_sent = {"positivo": 0, "neutro": 0, "negativo": 0}
            for c in valid_comments:
                dist_sent[c["sentimiento"]] += 1
                
            dist_int = {"alta": 0, "media": 0, "baja": 0}
            for c in valid_comments:
                val = c["intensidad"]
                if val >= 0.70:
                    dist_int["alta"] += 1
                elif val >= 0.40:
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

            # Generar Insights Narrativos Dinámicos locales (Fase de Fallback local)
            top_t = topicos_globales[0]["topico"] if topicos_globales else "Calidad docente"
            
            # Cálculo dinámico de insights por categoría padre (H-04)
            cat_parent_insights = {}
            for cat_padre in ["Académico", "Administrativo y Bienestar", "Infraestructura", "Valoración General"]:
                cat_coms = [c for c in valid_comments if c["categoria_padre"] == cat_padre]
                total_cat = len(cat_coms)
                
                if total_cat > 0:
                    pos_cat = sum(1 for c in cat_coms if c["sentimiento"] == "positivo")
                    neg_cat = sum(1 for c in cat_coms if c["sentimiento"] == "negativo")
                    
                    # Encontrar el sub-tópico específico más mencionado en esta categoría padre
                    topico_freq_dict = defaultdict(int)
                    for c in cat_coms:
                        topico_freq_dict[c["categoria"]] += 1
                    sub_topico_top = max(topico_freq_dict, key=topico_freq_dict.get)
                    
                    if cat_padre == "Académico":
                        if neg_cat > pos_cat:
                            acad_desc = f"Se registran {total_cat} menciones enfocadas principalmente en '{sub_topico_top}'. Se observa un volumen de opiniones críticas ({neg_cat} comentarios negativos) sobre la didáctica docente o el contenido de la malla curricular."
                        else:
                            acad_desc = f"Aspectos académicos concentran {total_cat} menciones, con predominancia de opiniones favorables ({pos_cat} positivas). El tema más comentado es '{sub_topico_top}'."
                        cat_parent_insights[cat_padre] = acad_desc
                    elif cat_padre == "Administrativo y Bienestar":
                        if neg_cat > 0:
                            adm_desc = f"Los servicios administrativos y de bienestar registran {total_cat} opiniones, con foco en '{sub_topico_top}'. Se reportan {neg_cat} quejas asociadas a la agilidad de los trámites o la atención brindada."
                        else:
                            adm_desc = f"Se registran {total_cat} comentarios sobre servicios administrativos, principalmente relacionados a '{sub_topico_top}' con una opinión mayormente balanceada o positiva."
                        cat_parent_insights[cat_padre] = adm_desc
                    elif cat_padre == "Infraestructura":
                        if neg_cat > pos_cat:
                            inf_desc = f"Se registran {total_cat} solicitudes en infraestructura, centradas en '{sub_topico_top}'. Se identifican {neg_cat} quejas puntuales sobre mantenimiento, equipamiento o conexión inalámbrica."
                        else:
                            inf_desc = f"La infraestructura recibe {total_cat} comentarios, enfocados en '{sub_topico_top}'. Predominan opiniones positivas o sugerencias de mejora ({pos_cat} menciones positivas)."
                        cat_parent_insights[cat_padre] = inf_desc
                    elif cat_padre == "Valoración General":
                        val_desc = f"La valoración general de la institución cuenta con {total_cat} opiniones (con {pos_cat} valoraciones positivas), reflejando un sólido prestigio institucional y recomendación de calidad."
                        cat_parent_insights[cat_padre] = val_desc
                else:
                    # Fallback si no hay comentarios para esa categoría en el periodo
                    if cat_padre == "Académico":
                        cat_parent_insights[cat_padre] = "No se registraron comentarios significativos sobre aspectos académicos en este período."
                    elif cat_padre == "Administrativo y Bienestar":
                        cat_parent_insights[cat_padre] = "No se reportan incidencias ni comentarios sobre procesos administrativos en este período."
                    elif cat_padre == "Infraestructura":
                        cat_parent_insights[cat_padre] = "La infraestructura física y tecnológica no registra menciones en las respuestas libres de este período."
                    elif cat_padre == "Valoración General":
                        cat_parent_insights[cat_padre] = "No se registran comentarios de valoración institucional general en este período."

            insights_ia = {
                "global": f"El análisis cualitativo revela que el tema más relevante en este período es '{top_t}' con un total de {topicos_globales[0]['total_comentarios'] if topicos_globales else 0} menciones. La distribución general muestra {dist_sent['positivo']} comentarios positivos y {dist_sent['negativo']} comentarios negativos.",
                "por_categoria_padre": cat_parent_insights
            }

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
