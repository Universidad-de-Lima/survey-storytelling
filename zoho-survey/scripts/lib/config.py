"""
SURVEY ETL CONFIG — Configuración centralizada del pipeline ETL.

Extraído de build_json.py (v2.0). Centraliza todos los mapeos,
catálogos y configuraciones que antes estaban hardcodeados.

Para añadir soporte a nuevas carreras, dimensiones o tópicos:
1. Editar este archivo
2. build_json.py usará automáticamente los nuevos valores
3. No es necesario modificar la lógica del ETL

@module lib/config
@version 1.0.0
"""

# ============================================================
# 1. RENOMBRADO DE COLUMNAS (Zoho Survey → nombres internos)
# ============================================================
# Dependencia crítica: si Zoho Survey cambia el texto de una
# pregunta, este mapeo debe actualizarse.
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
    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS",
}

# ============================================================
# 2. CATÁLOGO CARRERA → FACULTAD
# ============================================================
CARRERA_FACULTAD = {
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
    "Psicología": "Facultad de Psicología",
}

# ============================================================
# 3. CATÁLOGO DIMENSIÓN → CATEGORÍA
# ============================================================
CATEGORIA_DIMENSION = {
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

# ============================================================
# 4. RESPUESTAS DE TEXTO ESTÁNDAR
# ============================================================
RESPUESTAS_TEXTO = [
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
    "No utilizo",
    "No conozco",
]

# ============================================================
# 5. MAPA DE ETAPAS (ciclo numérico → etapa académica)
# ============================================================
ETAPA_MAP = {
    1: "Inicial", 2: "Inicial",
    3: "Intermedio", 4: "Intermedio", 5: "Intermedio", 6: "Intermedio",
    7: "Avanzado", 8: "Avanzado", 9: "Avanzado", 10: "Avanzado",
    11: "Avanzado", 12: "Avanzado",
}

# ============================================================
# 6. TÓPICOS PARA ANÁLISIS SEMÁNTICO
# ============================================================
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

# ============================================================
# 7. STOPWORDS (español)
# ============================================================
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
    "estar", "poder", "dentro", "debido", "además", "igual", "cuanto",
}

# ============================================================
# 8. DIRECTORIOS DE SALIDA POR TIPO DE ENCUESTA
# ============================================================
# Las rutas base son relativas a zoho-survey/ (BASE_DIR.parent)
# y se resuelven en build_json.py
SURVEY_DIR_KEYS = {
    "undergraduate": "students/undergraduate",
    "graduate": "students/graduate",
    "posgraduate": "students/posgraduate",
    "alumni-ug": "alumni/undergraduate",
    "alumni-pg": "alumni/posgraduate",
    "faculty-ug": "facultyStaff/undergraduate",
    "faculty-pg": "facultyStaff/posgraduate",
    "nonfaculty": "nonfacultyStaff",
    "employers": "employers",
}
