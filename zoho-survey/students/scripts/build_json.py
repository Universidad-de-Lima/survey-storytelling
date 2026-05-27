import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "data"

respuestas_texto = [
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
    "No utilizo",
    "No conozco"
]

COLUMN_RENAME = {
    "ID de respuesta": "ID",
    "Start time": "Inicio",
    "Hora de finalización": "Fin",
    "Net Promoter Score (de un total de 10)": "Recomiendas la Universidad de Lima",
    "¿Qué carrera profesional estudias?": "Carrera",
    "¿Qué ciclo es el que cursas?; considera el ciclo donde más cursos llevas": "Ciclo",
    "El perfil de egreso de tu carrera": "Perfil del egreso de la carrera",
    "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera": "Plan curricular y perfil de egreso",
    "Los cursos y contenidos de tu carrera": "Cursos del programa y contenidos",
    "La calidad del servicio de enseñanza en tu carrera": "Calidad de la enseñanza en la carrera",
    "La claridad, precisión y actualización de los materiales de estudio de tu carrera": "Calidad de los recursos académicos",
    "La calidad de la formación académica": "Calidad de la formación académica",
    "La evaluación del aprendizaje en tu carrera": "Evaluación del aprendizaje",
    "El proceso de intercambio estudiantil": "Intercambio estudiantil",
    "La información sobre tu récord académico": "Información sobre el récord académico",
    "El material bibliográfico físico o digital disponible en la biblioteca": "Material bibliográfico en la biblioteca",
    "El servicio recibido por el personal administrativo de tu carrera": "Atención del personal administrativo",
    "Los procedimientos de los servicios administrativos de tu carrera": "Procedimientos administrativos",
    "El servicio social: ayuda financiera": "Ayuda financiera",
    "El servicio médico y su infraestructura": "Servicio médico y su infraestructura",
    "El servicio de atención psicopedagógica": "Servicio de atención psicopedagógica",
    "Los talleres de actividades artísticas y culturales": "Talleres de actividades artísticas y culturales",
    "Las actividades deportivas": "Actividades deportivas",
    "Empleabilidad, vinculación profesional y ALUMNI": "Empleabilidad, vinculación y ALUMNI",
    "Las aulas de clase": "Aulas de clase",
    "Los ambientes y salas para estudio": "Ambientes y aulas para estudio",
    "Los laboratorios en lo referido a equipamiento, tecnología y programas": "Equipamiento tecnológico en laboratorios",
    "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad": "Condiciones ambientales en laboratorios",
    "El software especializado empleado en la carrera": "Software especializado empleado en la carrera",
    "El portal web de la universidad: Mi Ulima": "Portal web de la Universidad (Mi Ulima)",
    "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)": "Aula virtual",
    "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual": "Conexión Wi-Fi en el campus",
    "El soporte técnico brindado ante las fallas del sistema informático": "Soporte técnico del sistema informático",
    "Tu carrera": "La carrera",
    "La Universidad de Lima": "La Universidad de Lima",
    # -------------------------------------------------------------------
    # CORRECCIÓN #1: La columna de comentarios libres NPS se renombra a
    # "Comentario NPS" (no "Nube de palabras") para reflejar su función
    # real: es texto libre asociado al score NPS (0–10), no una nube.
    # El nombre anterior era ambiguo y no distinguía su dependencia del NPS.
    # -------------------------------------------------------------------
    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS"
}

# -----------------------
# Leer data
# -----------------------
SUPPORTED_EXTENSIONS = [".csv"]

files = [
    f for f in DATA_DIR.iterdir()
    if f.is_file()
    and f.suffix.lower() in SUPPORTED_EXTENSIONS
    and "ENCUESTA" in f.name.upper()
]

# =========================================================
# NUEVO: Análisis semántico por tópicos
# =========================================================
# Diccionario de tópicos con palabras clave asociadas.
# Cada tópico agrupa términos semánticamente relacionados
# para producir insights accionables en lugar de palabras aisladas.
# REGLA: solo se procesa si NPS < 9 (Pasivos 7-8 y Detractores 0-6).
TOPICOS = {
    "Calidad docente": {
        "palabras": [
            "profesores", "profes", "docentes", "profesor", "enseñanza",
            "enseñan", "enseñar", "clases", "clase", "metodología",
            "didáctica", "explican", "explica", "dictado", "catedráticos"
        ],
        "tipo": "mejora",
        "icono": "📚"
    },
    "Malla curricular y cursos": {
        "palabras": [
            "cursos", "curso", "malla", "curricular", "temas", "contenido",
            "contenidos", "plan", "relleno", "general", "generales",
            "electivos", "electivo", "asignaturas", "materias"
        ],
        "tipo": "mejora",
        "icono": "📋"
    },
    "Infraestructura y espacios": {
        "palabras": [
            "infraestructura", "campus", "aulas", "salones", "ambientes",
            "espacios", "espacio", "laboratorios", "biblioteca",
            "instalaciones", "edificios", "edificio", "salas"
        ],
        "tipo": "mejora",
        "icono": "🏛️"
    },
    "Servicios administrativos": {
        "palabras": [
            "administrativo", "administrativos", "procedimientos",
            "tramites", "trámites", "sistema", "demora", "lento",
            "lenta", "burocracia", "atención", "servicio", "servicios",
            "horarios", "horario"
        ],
        "tipo": "negativo",
        "icono": "⚙️"
    },
    "Tecnología y plataformas": {
        "palabras": [
            "wifi", "wi-fi", "internet", "blackboard", "zoom",
            "plataforma", "virtual", "sistema", "software",
            "tecnología", "tecnologías", "aula virtual", "soporte"
        ],
        "tipo": "mejora",
        "icono": "💻"
    },
    "Oportunidades laborales": {
        "palabras": [
            "empleabilidad", "trabajo", "empleo", "prácticas", "práctica",
            "alumni", "egresados", "vinculación", "empresas",
            "convenios", "mercado laboral", "bolsa"
        ],
        "tipo": "mejora",
        "icono": "💼"
    },
    "Bienestar y servicios al estudiante": {
        "palabras": [
            "psicología", "médico", "salud", "bienestar", "deporte",
            "actividades", "artísticas", "culturales", "talleres",
            "apoyo", "ayuda", "financiera", "beca", "becas"
        ],
        "tipo": "mejora",
        "icono": "🌱"
    },
    "Valoración positiva general": {
        "palabras": [
            "excelente", "satisfecho", "satisfecha", "recomendaría",
            "recomiendo", "buena", "buen", "increíble", "orgulloso",
            "contento", "feliz", "agradecido", "calidad", "prestigio"
        ],
        "tipo": "positivo",
        "icono": "✅"
    },
}

# Palabras irrelevantes (stopwords extendidas en español)
# Se eliminan antes del análisis para reducir ruido.
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "que", "los", "las", "un", "una",
    "por", "con", "es", "se", "del", "al", "lo", "como", "más", "pero",
    "sus", "le", "ya", "o", "este", "sí", "porque", "si", "fue", "hay",
    "no", "me", "mi", "para", "su", "muy", "sin", "sobre", "también",
    "entre", "así", "cuando", "todo", "esta", "ser", "tiene", "son",
    "una", "están", "han", "ha", "nos", "tu", "te", "era", "ni",
    "parece", "embargo", "aunque", "dentro", "fuera", "mismo", "misma",
    "tanto", "bien", "sería", "vez", "algo", "nada", "luego", "desde",
    "hacia", "durante", "podría", "podrían", "debería", "deberían",
    "cuenta", "puede", "pueden", "tener", "haber", "estar", "hacer",
    "dar", "ver", "ir", "querer", "creo", "creer", "gustar", "gusta",
    "gustaría", "depende", "manera", "forma", "parte", "lado", "vez",
    "veces", "respecto", "bastante", "demasiado", "demasiada", "mayor",
    "menor", "menos", "más", "general", "aspectos", "aspectos",
    "estar", "poder", "dentro", "debido", "además", "igual", "cuanto"
}


def normalizar_texto(texto):
    """Limpia y normaliza texto en español para análisis."""
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = texto.lower().strip()
    # Normalizar tildes comunes para matching más flexible
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n"
    }
    for orig, rep in reemplazos.items():
        texto = texto.replace(orig, rep)
    # Eliminar caracteres especiales excepto espacios y letras
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def clasificar_en_topico(comentario_norm):
    """
    Devuelve el nombre del tópico que más coincidencias tiene con el comentario.
    Retorna None si ningún tópico alcanza el umbral mínimo.
    """
    mejor_topico = None
    mejor_score = 0
    palabras_comentario = set(comentario_norm.split())

    for topico, config in TOPICOS.items():
        palabras_clave_norm = [normalizar_texto(p) for p in config["palabras"]]
        coincidencias = 0
        for pk in palabras_clave_norm:
            # Coincidencia exacta de palabra o como subcadena de palabra compuesta
            if pk in palabras_comentario:
                coincidencias += 1
            elif any(pk in palabra for palabra in palabras_comentario if len(pk) > 4):
                coincidencias += 0.5
        if coincidencias > mejor_score:
            mejor_score = coincidencias
            mejor_topico = topico

    return mejor_topico if mejor_score >= 0.5 else None


def agrupar_comentarios_por_topico(df_comentarios):
    """
    Toma un DataFrame con columnas [comentario, nps_score, carrera, facultad, ciclo]
    y agrupa los comentarios en tópicos semánticos.
    Solo procesa comentarios de Pasivos (7-8) y Detractores (0-6).
    Retorna lista de tópicos con frases representativas e insights.
    """
    # REGLA CRÍTICA: Solo Pasivos y Detractores (NPS < 9)
    df_filtrado = df_comentarios[
        df_comentarios["nps_score"] < 9
    ].copy()

    if df_filtrado.empty:
        return []

    df_filtrado["comentario_norm"] = df_filtrado["comentario"].apply(normalizar_texto)
    df_filtrado = df_filtrado[df_filtrado["comentario_norm"].str.len() > 10]

    # Asignar tópico a cada comentario
    df_filtrado["topico"] = df_filtrado["comentario_norm"].apply(clasificar_en_topico)

    topicos_resultado = []

    for topico_nombre, config in TOPICOS.items():
        subset = df_filtrado[df_filtrado["topico"] == topico_nombre]
        if len(subset) < 2:  # Umbral mínimo para considerar un tópico significativo
            continue

        # Seleccionar frases representativas: las más largas y completas
        frases_candidatas = subset["comentario"].dropna().tolist()
        frases_candidatas = [f.strip() for f in frases_candidatas if len(f.strip()) > 20]
        frases_candidatas.sort(key=len, reverse=True)
        frases_representativas = frases_candidatas[:3]  # Top 3 más informativas

        # Distribución por tipo NPS
        detractores = int((subset["nps_score"] <= 6).sum())
        pasivos = int((subset["nps_score"].between(7, 8)).sum())

        # Distribución por carrera (para filtrado posterior)
        por_carrera = subset.groupby("carrera").size().to_dict()
        por_facultad = subset.groupby("facultad").size().to_dict()
        por_ciclo = subset.groupby("ciclo").size().to_dict()

        topicos_resultado.append({
            "topico": topico_nombre,
            "tipo": config["tipo"],
            "icono": config["icono"],
            "total_comentarios": int(len(subset)),
            "detractores": detractores,
            "pasivos": pasivos,
            "frases_representativas": frases_representativas,
            "por_carrera": {k: int(v) for k, v in sorted(por_carrera.items(), key=lambda x: x[1], reverse=True)},
            "por_facultad": {k: int(v) for k, v in sorted(por_facultad.items(), key=lambda x: x[1], reverse=True)},
            "por_ciclo": {k: int(v) for k, v in sorted(por_ciclo.items(), key=lambda x: x[1], reverse=True)}
        })

    # Ordenar por cantidad de comentarios (más relevante primero)
    topicos_resultado.sort(key=lambda x: x["total_comentarios"], reverse=True)
    return topicos_resultado


# Recolectar periodos procesados para actualizar periodos.json automáticamente
periodos_por_nivel = defaultdict(set)


for INPUT_FILE in files:
    filename = INPUT_FILE.name.upper()
    if "PREGRADO" in filename:
        LEVEL = "undergraduate"
    elif "POSGRADO" in filename:
        LEVEL = "postgraduate"
    else:
        continue

    match = re.search(r"(20\d{2}-[12])", filename)
    if not match:
        continue

    YEAR = match.group()
    periodos_por_nivel[LEVEL].add(YEAR)
    OUT = ROOT_DIR / LEVEL / YEAR / "json"
    OUT.mkdir(parents=True, exist_ok=True)

    YEAR_DIR = ROOT_DIR / LEVEL / YEAR
    INDEX_FILE = YEAR_DIR / "index.html"
    TEMPLATE_INDEX = ROOT_DIR / "template" / "index.html"
    if not INDEX_FILE.exists():
        copyfile(TEMPLATE_INDEX, INDEX_FILE)

    try:
        df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    except Exception:
        df = pd.read_csv(INPUT_FILE, encoding="latin-1")

    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
    df.rename(columns=COLUMN_RENAME, inplace=True)

    # -----------------------
    # Catálogo Carrera → Facultad
    # -----------------------
    carrera_facultad = {
        "Arquitectura": "Facultad de Arquitectura",
        "Administración": "Facultad de Ciencias Empresariales",
        "Contabilidad y Finanzas": "Facultad de Ciencias Empresariales",
        "Marketing": "Facultad de Ciencias Empresariales",
        "Negocios Internacionales": "Facultad de Ciencias Empresariales",
        "Comunicación": "Facultad de Comunicación",
        "Derecho": "Facultad de Derecho",
        "Economía": "Facultad de Economía",
        "Ingeniería Ambiental": "Facultad de Ingeniería",
        "Ingeniería Civil": "Facultad de Ingeniería",
        "Ingeniería de Sistemas": "Facultad de Ingeniería",
        "Ingeniería Industrial": "Facultad de Ingeniería",
        "Ingeniería Mecatrónica": "Facultad de Ingeniería",
        "Psicología": "Facultad de Psicología"
    }
    df["Facultad"] = df["Carrera"].map(carrera_facultad)

    # -----------------------
    # Catálogo dimensión → categoría
    # -----------------------
    categoria_dim = {
        "Perfil del egreso de la carrera": "Académico",
        "Plan curricular y perfil de egreso": "Académico",
        "Cursos del programa y contenidos": "Académico",
        "Calidad de la enseñanza en la carrera": "Académico",
        "Calidad de los recursos académicos": "Académico",
        "Calidad de la formación académica": "Académico",
        "Evaluación del aprendizaje": "Académico",
        "Intercambio estudiantil": "Académico",
        "La carrera": "Académico",
        "Información sobre tu récord académico": "Administrativo y Bienestar",
        "Material bibliográfico en la biblioteca": "Administrativo y Bienestar",
        "Atención del personal administrativo": "Administrativo y Bienestar",
        "Procedimientos administrativos": "Administrativo y Bienestar",
        "Ayuda financiera": "Administrativo y Bienestar",
        "Servicio médico y su infraestructura": "Administrativo y Bienestar",
        "Servicio de atención psicopedagógica": "Administrativo y Bienestar",
        "Talleres de actividades artísticas y culturales": "Administrativo y Bienestar",
        "Actividades deportivas": "Administrativo y Bienestar",
        "Empleabilidad, vinculación y ALUMNI": "Administrativo y Bienestar",
        "Aulas de clase": "Infraestructura",
        "Ambientes y aulas para estudio": "Infraestructura",
        "Equipamiento tecnológico en laboratorios": "Infraestructura",
        "Condiciones ambientales en laboratorios": "Infraestructura",
        "Software especializado empleado en la carrera": "Tecnología",
        "Portal web de la Universidad (Mi Ulima)": "Tecnología",
        "Aula virtual": "Tecnología",
        "Conexión Wi-Fi en el campus": "Tecnología",
        "Soporte técnico del sistema informático": "Tecnología",
    }

    # -----------------------
    # Funciones auxiliares
    # -----------------------
    def calc_nps(promotores, pasivos, detractores):
        total = promotores + pasivos + detractores
        if total == 0:
            return 0.0
        return round(((promotores - detractores) / total) * 100, 2)

    def calc_csat(t3b, total):
        if total == 0:
            return 0.0
        return round((t3b / total) * 100, 2)

    def get_t3b(row):
        return (row.get("Totalmente satisfecho", 0) +
                row.get("Muy satisfecho", 0) +
                row.get("Satisfecho", 0))

    # =========================================================
    # 1. resumen.json
    # =========================================================
    df["Inicio"] = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce")
    df["Fin"]    = pd.to_datetime(df["Fin"],    dayfirst=True, errors="coerce")

    inicio = df["Inicio"].min()
    fin    = df["Fin"].max()
    anio_encuesta  = df["Inicio"].dt.year.mode()[0]
    fechas_unicas  = df["Inicio"].dt.date.nunique()

    nps_col = "Recomiendas la Universidad de Lima"
    df_nps  = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna()
    promotores_total  = int(df_nps[df_nps[nps_col] >= 9].shape[0])
    pasivos_total     = int(df_nps[(df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)].shape[0])
    detractores_total = int(df_nps[df_nps[nps_col] <= 6].shape[0])
    nps_score = calc_nps(promotores_total, pasivos_total, detractores_total)

    csat_col  = "La Universidad de Lima"
    serie_csat = df[csat_col].dropna()
    csat_t3b  = int((serie_csat.isin(["Totalmente satisfecho", "Muy satisfecho", "Satisfecho"])).sum())
    csat_total = int(serie_csat.isin(respuestas_texto[:5]).sum())
    csat_score = calc_csat(csat_t3b, csat_total)

    resumen = {
        "encuestas": int(len(df)),
        "carreras": int(df["Carrera"].nunique()),
        "facultades": int(df["Facultad"].nunique()),
        "fecha_inicio": inicio.strftime("%Y-%m-%d"),
        "fecha_fin": fin.strftime("%Y-%m-%d"),
        "dias": int((fin - inicio).days + 1),
        "dias_recoleccion": fechas_unicas,
        "año": int(anio_encuesta),
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

    with open(OUT / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 2. NPS (global, carrera, ciclo, ciclo_carrera)
    # =========================================================
    nps_total = {
        "Promotores": promotores_total,
        "Pasivos": pasivos_total,
        "Detractores": detractores_total,
        "score": nps_score
    }
    with open(OUT / "nps.json", "w", encoding="utf-8") as f:
        json.dump(nps_total, f, ensure_ascii=False, indent=2)

    nps_carrera = []
    for carrera, sub in df_nps.groupby("Carrera"):
        p  = int((sub[nps_col] >= 9).sum())
        pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
        d  = int((sub[nps_col] <= 6).sum())
        nps_carrera.append({"carrera": carrera, "Promotores": p, "Pasivos": pa, "Detractores": d, "score": calc_nps(p, pa, d)})
    with open(OUT / "nps_carrera.json", "w", encoding="utf-8") as f:
        json.dump(nps_carrera, f, ensure_ascii=False, indent=2)

    nps_ciclo = []
    for ciclo, sub in df_nps.groupby("Ciclo"):
        p  = int((sub[nps_col] >= 9).sum())
        pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
        d  = int((sub[nps_col] <= 6).sum())
        nps_ciclo.append({"ciclo": ciclo, "Promotores": p, "Pasivos": pa, "Detractores": d, "score": calc_nps(p, pa, d)})
    with open(OUT / "nps_ciclo.json", "w", encoding="utf-8") as f:
        json.dump(nps_ciclo, f, ensure_ascii=False, indent=2)

    nps_ciclo_carrera = []
    for (fac, car, cic), sub in df_nps.groupby(["Facultad", "Carrera", "Ciclo"]):
        p  = int((sub[nps_col] >= 9).sum())
        pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
        d  = int((sub[nps_col] <= 6).sum())
        nps_ciclo_carrera.append({"facultad": fac, "carrera": car, "ciclo": cic,
                                   "Promotores": p, "Pasivos": pa, "Detractores": d,
                                   "score": calc_nps(p, pa, d)})
    with open(OUT / "nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
        json.dump(nps_ciclo_carrera, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 3. CSAT (global, carrera, ciclo, ciclo_carrera)
    # =========================================================
    csat_conteos = {r: int((serie_csat == r).sum()) for r in respuestas_texto}
    csat_conteos["score"] = csat_score
    with open(OUT / "csat.json", "w", encoding="utf-8") as f:
        json.dump(csat_conteos, f, ensure_ascii=False, indent=2)

    csat_carrera = []
    for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
        serie = sub[csat_col].dropna()
        row = {"carrera": car, "facultad": fac}
        for r in respuestas_texto:
            row[r] = int((serie == r).sum())
        t3b   = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
        total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
        row["score"] = calc_csat(t3b, total)
        csat_carrera.append(row)
    with open(OUT / "csat_carrera.json", "w", encoding="utf-8") as f:
        json.dump(csat_carrera, f, ensure_ascii=False, indent=2)

    csat_ciclo = []
    for cic, sub in df.groupby("Ciclo"):
        serie = sub[csat_col].dropna()
        row = {"ciclo": cic}
        for r in respuestas_texto:
            row[r] = int((serie == r).sum())
        t3b   = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
        total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
        row["score"] = calc_csat(t3b, total)
        csat_ciclo.append(row)
    with open(OUT / "csat_ciclo.json", "w", encoding="utf-8") as f:
        json.dump(csat_ciclo, f, ensure_ascii=False, indent=2)

    csat_ciclo_carrera = []
    for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
        serie = sub[csat_col].dropna()
        row = {"facultad": fac, "carrera": car, "ciclo": cic}
        for r in respuestas_texto:
            row[r] = int((serie == r).sum())
        t3b   = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
        total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
        row["score"] = calc_csat(t3b, total)
        csat_ciclo_carrera.append(row)
    with open(OUT / "csat_ciclo_carrera.json", "w", encoding="utf-8") as f:
        json.dump(csat_ciclo_carrera, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 4. dimensiones.json
    # =========================================================
    rows = []
    for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
        for dim, cat in categoria_dim.items():
            if dim not in sub.columns:
                continue
            serie    = sub[dim].dropna()
            conteos  = {r: int((serie == r).sum()) for r in respuestas_texto}
            t3b      = conteos["Totalmente satisfecho"] + conteos["Muy satisfecho"] + conteos["Satisfecho"]
            b2b      = conteos["Insatisfecho"] + conteos["Totalmente insatisfecho"]
            total    = t3b + b2b
            rows.append({
                "facultad": fac, "carrera": car, "ciclo": cic,
                "categoria": cat, "dimension": dim,
                "t3b": t3b, "b2b": b2b, "total": total,
                "t3b_pct": calc_csat(t3b, total),
                "no_utilizo": conteos["No utilizo"],
                "no_conozco": conteos["No conozco"],
                **conteos
            })
    with open(OUT / "dimensiones.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 5. evolucion_temporal.json - ELIMINADO (ya no se genera)
    # =========================================================

    # =========================================================
    # 6. ids.json (el índice cambia porque ya no hay 5)
    # =========================================================
    ids_conteo = []
    for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
        ids_conteo.append({"facultad": fac, "carrera": car, "ciclo": cic, "count": int(len(sub))})
    with open(OUT / "ids.json", "w", encoding="utf-8") as f:
        json.dump(ids_conteo, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 7. dashboard_data.json (sin evolucion)
    # =========================================================
    etapa_map = {
        1: "Inicial", 2: "Inicial",
        3: "Intermedio", 4: "Intermedio", 5: "Intermedio", 6: "Intermedio",
        7: "Avanzado", 8: "Avanzado", 9: "Avanzado", 10: "Avanzado",
        11: "Avanzado", 12: "Avanzado"
    }
    etapas = {}
    for item in nps_ciclo:
        ciclo_num = int("".join(filter(str.isdigit, item["ciclo"])) or 0)
        etapa = etapa_map.get(ciclo_num, "Otro")
        if etapa not in etapas:
            etapas[etapa] = {"p": 0, "pa": 0, "d": 0}
        etapas[etapa]["p"]  += item["Promotores"]
        etapas[etapa]["pa"] += item["Pasivos"]
        etapas[etapa]["d"]  += item["Detractores"]

    nps_etapas = {etapa: calc_nps(v["p"], v["pa"], v["d"]) for etapa, v in etapas.items()}

    dim_agg = {}
    for r in rows:
        if r["dimension"] not in dim_agg:
            dim_agg[r["dimension"]] = {"t3b": 0, "total": 0}
        dim_agg[r["dimension"]]["t3b"]   += r["t3b"]
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
        t3b   = item["Totalmente satisfecho"] + item["Muy satisfecho"] + item["Satisfecho"]
        total = t3b + item["Insatisfecho"] + item["Totalmente insatisfecho"]
        fac_agg[fac]["t3b"]   += t3b
        fac_agg[fac]["total"] += total

    top_facs = sorted(
        [{"name": k, "score": calc_csat(v["t3b"], v["total"])} for k, v in fac_agg.items()],
        key=lambda x: x["score"], reverse=True
    )[:2]

    dashboard_data = {
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
        "nps": nps_total,
        "csat": csat_conteos
        # "evolucion": evol   ← ELIMINADO
    }
    with open(OUT / "dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 8. filtros.json
    # =========================================================
    filtros = {
        "facultades": sorted(df["Facultad"].dropna().unique().tolist()),
        "carreras": sorted(df["Carrera"].dropna().unique().tolist()),
        "ciclos": sorted(df["Ciclo"].dropna().unique().tolist(),
                         key=lambda x: int("".join(filter(str.isdigit, x)) or 0)),
        "facultad_carrera": {
            fac: sorted(df[df["Facultad"] == fac]["Carrera"].unique().tolist())
            for fac in df["Facultad"].dropna().unique()
        }
    }
    with open(OUT / "filtros.json", "w", encoding="utf-8") as f:
        json.dump(filtros, f, ensure_ascii=False, indent=2)

    # =========================================================
    # 9. NUEVO: sentimiento.json — Análisis semántico por tópicos
    # =========================================================
    comentario_col = "Comentario NPS"

    if comentario_col in df.columns:
        df_sent = df[[comentario_col, nps_col, "Carrera", "Facultad", "Ciclo"]].copy()
        df_sent.columns = ["comentario", "nps_score", "carrera", "facultad", "ciclo"]
        df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
        df_sent["comentario"] = (
            df_sent["comentario"]
            .fillna("")
            .astype(str)
        )
        df_sent = df_sent[
            df_sent["comentario"]
            .str.strip()
            .str.len() > 5
        ]
        df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
        df_sent = df_sent.dropna(subset=["nps_score"])

        # Solo Pasivos (7-8) y Detractores (0-6)
        df_pasivos_detractores = df_sent[df_sent["nps_score"] < 9]

        total_con_comentario = int(len(df_sent))
        total_analizados     = int(len(df_pasivos_detractores))
        detractores_con_com  = int((df_pasivos_detractores["nps_score"] <= 6).sum())
        pasivos_con_com      = int((df_pasivos_detractores["nps_score"].between(7, 8)).sum())

        # Análisis semántico (se pasa directamente el DF filtrado)
        topicos_globales = agrupar_comentarios_por_topico(df_pasivos_detractores)

        # Distribución por carrera
        por_carrera = []
        for car, sub in df_pasivos_detractores.groupby("carrera"):
            por_carrera.append({
                "carrera": car,
                "facultad": sub["facultad"].iloc[0] if not sub.empty else "",
                "total": int(len(sub)),
                "pasivos": int((sub["nps_score"].between(7, 8)).sum()),
                "detractores": int((sub["nps_score"] <= 6).sum())
            })
        por_carrera.sort(key=lambda x: x["total"], reverse=True)

        # Distribución por ciclo
        por_ciclo = []
        for cic, sub in df_pasivos_detractores.groupby("ciclo"):
            por_ciclo.append({
                "ciclo": cic,
                "total": int(len(sub)),
                "pasivos": int((sub["nps_score"].between(7, 8)).sum()),
                "detractores": int((sub["nps_score"] <= 6).sum())
            })
        por_ciclo.sort(key=lambda x: int("".join(filter(str.isdigit, x["ciclo"])) or 0))

        sentimiento = {
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

    with open(OUT / "sentimiento.json", "w", encoding="utf-8") as f:
        json.dump(sentimiento, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Archivos generados para {LEVEL}/{YEAR}:")
    print(f"   resumen.json · nps*.json · csat*.json")
    print(f"   dimensiones.json · evolucion_temporal.json")
    print(f"   ids.json · dashboard_data.json · filtros.json")
    print(f"   sentimiento.json (análisis semántico por tópicos)")


# =========================================================
# Actualizar periodos.json automáticamente por nivel
# =========================================================
def clave_periodo(p):
    parts = p.split('-')
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return (int(parts[0]), int(parts[1]))
    return (0, 0)


for lvl, periodos in periodos_por_nivel.items():
    if not periodos:
        continue
    # Ordenar periodos de forma cronológica (ej: 2025-2 < 2026-1)
    periodos_ordenados = sorted(list(periodos), key=clave_periodo)
    ultimo_periodo = periodos_ordenados[-1]

    periodos_json = []
    for p in periodos_ordenados:
        periodos_json.append({
            "id": p,
            "label": p,
            "isNew": p == ultimo_periodo
        })

    path_periodos = ROOT_DIR / lvl / "periodos.json"
    try:
        with open(path_periodos, "w", encoding="utf-8") as f:
            json.dump(periodos_json, f, ensure_ascii=False, indent=2)
        print(f"\n✨ periodos.json actualizado automáticamente para {lvl}:")
        for p in periodos_json:
            status = "NUEVO 🆕" if p["isNew"] else "anterior"
            print(f"   - {p['id']} ({status})")
    except Exception as e:
        print(f"❌ Error al escribir periodos.json en {path_periodos}: {e}")
