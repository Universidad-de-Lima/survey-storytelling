"""
Script para actualizar build_json.py con los mappings de graduados.
Se ejecuta una sola vez para modificar el archivo.
"""
import re

PATH = 'zoho-survey/scripts/build_json.py'

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Renombrar COLUMN_RENAME actual a COLUMN_RENAME_PREGRADO ──
content = content.replace('\nCOLUMN_RENAME = {', '\nCOLUMN_RENAME_PREGRADO = {')

# ── 2. Insertar COLUMN_RENAME_POSGRADO después del bloque de PREGRADO ──
# Buscar el final del diccionario COLUMN_RENAME_PREGRADO (después del comentario y la llave de cierre)
old_end = '''    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS"
}'''

new_end = '''    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS"
}

# ── Mappings específicos para encuesta de GRADUADOS ──
COLUMN_RENAME_POSGRADO = {
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
    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Nube de palabras"
}'''

content = content.replace(old_end, new_end)

# ── 3. Usar COLUMN_RENAME adecuado según nivel ──
content = content.replace(
    'df.rename(columns=COLUMN_RENAME, inplace=True)',
    'COLUMN_RENAME = COLUMN_RENAME_POSGRADO if LEVEL == "graduate" else COLUMN_RENAME_PREGRADO\n    df.rename(columns=COLUMN_RENAME, inplace=True)'
)

# ── 4. Agregar categoria_dim_posgrado después de categoria_dim ──
old_cat_end = '''        "Soporte técnico del sistema informático": "Tecnología",
    }'''

new_cat_end = '''        "Soporte técnico del sistema informático": "Tecnología",
    }

    # ── Catálogo específico para GRADUADOS (incluye Docencia y Desarrollo Profesional) ──
    categoria_dim_posgrado = {
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
        "Información sobre el récord académico": "Administrativo y Bienestar",
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
    }'''

content = content.replace(old_cat_end, new_cat_end)

# ── 5. Usar categoria_dim adecuado según nivel ──
content = content.replace(
    'for dim, cat in categoria_dim.items():',
    'categoria_dim = categoria_dim_posgrado if LEVEL == "graduate" else categoria_dim_pregrado\n        for dim, cat in categoria_dim.items():'
)

# ── 6. Renombrar categoria_dim original a categoria_dim_pregrado ──
content = content.replace('\n    # Catálogo dimensión → categoría\n    # -----------------------\n    categoria_dim = {',
                          '\n    # Catálogo dimensión → categoría (PREGRADO)\n    # -----------------------\n    categoria_dim_pregrado = {')

# ── 7. Renombrar la variable local en el loop (si hay más referencias) ──
# Ya se manejó en el paso 5

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ build_json.py actualizado con mappings para graduados.")
print("Verificar que no haya errores de sintaxis...")
