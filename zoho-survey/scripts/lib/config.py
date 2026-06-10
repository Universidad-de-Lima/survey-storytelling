"""
SURVEY ETL CONFIG — Configuración centralizada del pipeline ETL.

Centraliza todos los mapeos, catálogos y configuraciones para encuestas
de pregrado y graduados.

Para añadir soporte a nuevas carreras, dimensiones o tópicos:
1. Editar este archivo.
2. Los scripts de procesamiento y validación leerán estos valores automáticamente.
"""

from typing import Dict, List, Set

# ============================================================
# 1. RENOMBRADO DE COLUMNAS (Zoho Survey → nombres internos)
# ============================================================

COLUMN_RENAME_PREGRADO: Dict[str, str] = {
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
    "La claridad, precisión y actualización de los materiales de estudio de tu carrera": "Claridad de los recursos académicos",
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
    "Los ambientes y salas para estudio": "Ambientes y salas para estudio",
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

# ── Mappings específicos para encuesta de GRADUADOS (Posgrado) ──
# BUG SOLVED: "Comentario NPS" unificado con la columna de pregrado
# para asegurar que el motor cualitativo procese el texto libre correctamente.
COLUMN_RENAME_POSGRADO: Dict[str, str] = {
    "ID de respuesta": "ID",
    "Start time": "Inicio",
    "Hora de finalización": "Fin",
    "Net Promoter Score (de un total de 10)": "Recomiendas la Universidad de Lima",
    "¿Qué carrera profesional estudiaste?": "Carrera",
    "¿Cuál es tu situación laboral actual?": "Situación laboral",
    "¿Cuál es el tiempo dedicado a tu trabajo?": "Tiempo laboral",
    "El perfil de egreso de tu carrera": "Perfil del egreso de la carrera",
    "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera": "Plan curricular y perfil de egreso",
    "Los cursos y contenidos de tu carrera": "Cursos del programa y contenidos",
    "La calidad del servicio de enseñanza de tu carrera": "Calidad de la enseñanza en la carrera",
    "La claridad, precisión y actualización de los materiales de estudio de tu carrera": "Claridad de los recursos académicos",
    "La calidad de la formación académica": "Calidad de la formación académica",
    "La exigencia académica de las asignaturas de tu carrera": "Exigencia académica",
    "La evaluación del aprendizaje de tu carrera": "Evaluación del aprendizaje",
    "El proceso de intercambio estudiantil": "Intercambio estudiantil",
    "El dominio de los conocimientos que transmiten": "Transmisión de conocimientos",
    "La capacidad para transmitir el conocimiento y experiencias que complementan la teoría": "Transmisión de experiencias",
    "Las metodologías y herramientas aplicadas para la enseñanza y aprendizaje": "Metodologías",
    "La actualización de los conocimientos transmitidos": "Conocimientos actualizados",
    "El compromiso con el aprendizaje de los alumnos": "Compromiso",
    "La retroalimentación de las tareas, trabajos y desempeño": "Retroalimentación",
    "La disposición y tiempo para asesorar a los alumnos": "Disponibilidad para asesorias",
    "La disciplina en el cumplimiento de las normas y programas": "Cumplimiento de normas y programas",
    "El desarrollo de tus habilidades de trabajo en equipo": "Habilidades para trabajar en equipo",
    "El desarrollo de tus habilidades de comunicación": "Habilidades de comunicación",
    "La capacidad para aportar y explorar nuevas ideas": "Habilidades para aportar nuevas ideas",
    "La mejora de tu perspectiva de empleo": "Mejora en perspectivas de empleo",
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
    "Los ambientes y salas para estudio": "Ambientes y salas para estudio",
    "Los laboratorios en lo referido a equipamiento, tecnología y programas": "Equipamiento tecnológico en laboratorios",
    "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad": "Condiciones ambientales en laboratorios",
    "El software especializado empleado en tu carrera": "Software especializado empleado en la carrera",
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

CARRERA_FACULTAD: Dict[str, str] = {
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

CATEGORIA_DIMENSION_PREGRADO: Dict[str, str] = {
    "Perfil del egreso de la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Claridad de los recursos académicos": "Académico",
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
    "Ambientes y salas para estudio": "Infraestructura",
    "Equipamiento tecnológico en laboratorios": "Infraestructura",
    "Condiciones ambientales en laboratorios": "Infraestructura",
    "Software especializado empleado en la carrera": "Tecnología",
    "Portal web de la Universidad (Mi Ulima)": "Tecnología",
    "Aula virtual": "Tecnología",
    "Conexión Wi-Fi en el campus": "Tecnología",
    "Soporte técnico del sistema informático": "Tecnología",
}

CATEGORIA_DIMENSION_POSGRADO: Dict[str, str] = {
    "Perfil del egreso de la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Claridad de los recursos académicos": "Académico",
    "Calidad de la formación académica": "Académico",
    "Exigencia académica": "Académico",
    "Evaluación del aprendizaje": "Académico",
    "Intercambio estudiantil": "Académico",
    "La carrera": "Académico",
    "Transmisión de conocimientos": "Docencia",
    "Transmisión de experiencias": "Docencia",
    "Metodologías": "Docencia",
    "Conocimientos actualizados": "Docencia",
    "Compromiso": "Docencia",
    "Retroalimentación": "Docencia",
    "Disponibilidad para asesorias": "Docencia",
    "Cumplimiento de normas y programas": "Docencia",
    "Habilidades para trabajar en equipo": "Desarrollo Profesional",
    "Habilidades de comunicación": "Desarrollo Profesional",
    "Habilidades para aportar nuevas ideas": "Desarrollo Profesional",
    "Mejora en perspectivas de empleo": "Desarrollo Profesional",
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
    "Ambientes y salas para estudio": "Infraestructura",
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

RESPUESTAS_TEXTO: List[str] = [
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

ETAPA_MAP: Dict[int, str] = {
    1: "Inicial",
    2: "Inicial",
    3: "Intermedio",
    4: "Intermedio",
    5: "Intermedio",
    6: "Avanzado",
    7: "Avanzado",
    8: "Avanzado",
    9: "Avanzado",
    10: "Avanzado",
    11: "Avanzado",
    12: "Avanzado",
}

# ============================================================
# 6. TÓPICOS PARA ANÁLISIS SEMÁNTICO
# ============================================================

TOPICOS: Dict[str, Dict[str, any]] = {
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

STOPWORDS: Set[str] = {
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
    "menor", "menos", "más", "general", "aspectos", "estar", "poder",
    "debido", "además", "igual", "cuanto",
}

# ============================================================
# 8. CONFIGURACIÓN DE ZOHO SURVEYS POR PERIODO
# ============================================================

EMPLEABILIDAD_CATEGORIAS: List[str] = [
    "Trabajador dependiente",
    "Prácticas profesionales",
    "Trabajador independiente",
    "Prácticas pre - profesionales"
]
