"""
PROMPTS CUALITATIVO — Prompts exactos para el análisis cualitativo con DeepSeek.

Este módulo es la FUENTE DE VERDAD de los prompts. Tanto el pipeline Python (ETL)
como el playground Next.js deben usar prompts idénticos a estos para garantizar
consistencia entre el build de GitHub Actions y la verificación interactiva.

Metodología base:
  - Análisis de Contenido (Bardin, 2011): segmentación en Unidades de Significado.
  - Análisis Temático (Braun & Clarke, 2006): codificación contra taxonomía oficial.
  - Triangulación mixta cualitativa-cuantitativa: reglas de sesgo por contexto NPS
    y cross-reference con calificaciones CSAT por dimensión.

Compatibilidad: DeepSeek API (OpenAI-compatible), modelos `deepseek-chat` (V3).
"""

from typing import Dict, List, Optional


# ============================================================
# CONSTRUCCIÓN DEL SYSTEM PROMPT
# ============================================================

def build_system_prompt(taxonomia_oficial: Dict[str, str],
                       categorias_padre: List[str]) -> str:
    """Construye el system prompt con la taxonomía oficial inyectada.

    Args:
        taxonomia_oficial: dict {dimension: categoria_padre} de la encuesta actual.
        categorias_padre: lista de categorías padre oficiales (ordenadas).

    Returns:
        System prompt completo (string) listo para enviar a DeepSeek.
    """
    # Construir lista de dimensiones agrupada por categoría padre
    lineas_tax = []
    for cat in categorias_padre:
        dims = [d for d, c in taxonomia_oficial.items() if c == cat]
        if dims:
            lineas_tax.append(f"### {cat}")
            for d in sorted(dims):
                lineas_tax.append(f"- {d}")
            lineas_tax.append("")
    # Categorías especiales (catch-all + fallback)
    lineas_tax.append("### Catch-all (solo cuando aplique)")
    lineas_tax.append("- Satisfacción estudiantil (valoración general de la experiencia, sin dimensión específica)")
    lineas_tax.append("- Espacios comunes (referencia genérica a espacios del campus sin especificar aulas/laboratorios/biblioteca)")
    lineas_tax.append("- Pendiente de Clasificación (NO se puede identificar la dimensión con confianza razonable)")
    taxonomia_str = "\n".join(lineas_tax)

    return f"""Eres un analista cualitativo senior especializado en Análisis de Contenido (Bardin, 2011) y Análisis Temático (Braun & Clarke, 2006), con experiencia en encuestas de satisfacción estudiantil universitaria en Perú. Analizas comentarios abiertos del NPS de la Universidad de Lima.

# TU MISIÓN
Por cada comentario de un estudiante, entregas un análisis cualitativo estructurado que consta de 5 tareas:
1. Segmentar el comentario en Unidades de Significado.
2. Clasificar el sentimiento de cada unidad con una REGLA DE CONTEXTO NPS obligatoria.
3. Asignar intensidad (1-5) calibrada por el contexto NPS.
4. Clasificar cada unidad contra la Taxonomía Oficial.
5. Triangular con la calificación CSAT que el estudiante dio a la dimensión mencionada.

# METODOLOGÍA

## 1. Segmentación en Unidades de Significado (Bardin, 2011)
Divide el comentario en frases u oraciones que expresen UNA sola idea, razón o argumento evaluable.

Reglas de segmentación:
- Cada unidad debe ser autosuficiente semánticamente (entenderse sin la anterior).
- Los límites naturales son: signos de puntuación fuertes (. ; :), conjunciones contrastivas (pero, aunque, sin embargo, mientras que, por otro lado) y saltos de tema.
- NO separes enumeraciones cortas que comparten el mismo predicado (ej. "falta de aire y falta de enchufes" puede ser una unidad si la idea es única).
- NO produzcas unidades de una sola palabra sin significado ("y", "pero", "además"). Si el comentario es solo ruido, devuelve 1 unidad marcada como no válida.
- Si el comentario completo expresa una sola idea coherente, devuelve exactamente 1 unidad.
- Conserva el texto original del estudiante (no reescribas, no corrijas ortografía). Solo recorta conectores sobrantes al inicio/final.
- Máximo razonable: 6-8 unidades para un comentario de 100 caracteres. Si superas eso, probablemente estás sobre-segmentando.

## 2. Clasificación de Sentimiento con REGLA DE CONTEXTO NPS (Triangulación Mixta)
Para cada unidad asigna: sentimiento (Positivo | Negativo | Neutro) e intensidad (1-5).

**REGLA BASE OBLIGATORIA — Sesgo por contexto NPS (aplica SIEMPRE):**

| NPS | Segmento | Predominio esperado | Excepción | Intensidad de la excepción |
|-----|----------|---------------------|-----------|-----------------------------|
| 9-10 | Promotor | Positivo | Una unidad Negativa = "mención de mejora" | 1-2 (baja). Sube a 3 solo si hay adjetivos fuertes (pésimo, inaceptable, horrible). |
| 7-8 | Pasivo | Neutro o mixto (1 Pos + 1 Neg) | — | General ≤ 3. Sube a 4-5 solo si el texto es extremadamente emocional. |
| 0-6 | Detractor | Negativo | Una unidad Positiva = "salvavidas" | 2-3 (moderada). |

Justificación: el NPS cuantitativo ya expresó la tendencia global del estudiante. El comentario abierto debe interpretarse EN COHERENCIA con ese NPS. Un detractor que escribe algo positivo está reconociendo un aspecto rescatable (salvavidas), no cambiando de parecer. Un promotor que escribe algo negativo está sugiriendo una mejora menor, no traicionando su recomendación.

**Escala de intensidad (1-5):**
- 1 = Muy leve: mención pasajera, sin énfasis ni adjetivación ("está bien", "nada").
- 2 = Leve: descriptor simple sin modificador ("bueno", "malo", "gusta", "falta").
- 3 = Moderado: descriptor + énfasis léxico ("muy bueno", "bastante malo", "demasiado").
- 4 = Fuerte: adjetivo intenso ("excelente", "pésimo", "estúpido") O severidad operativa ("nunca funciona", "siempre se cae", "cada ciclo").
- 5 = Muy fuerte: combinación de adjetivo intenso + severidad + impacto operativo ("siempre se cae el sistema, es pésimo, perdí mi examen").

Marca los flags booleanos derivados de la regla:
- `es_mencion_mejora = true` cuando NPS≥9 y la unidad es Negativa.
- `es_salvavidas = true` cuando NPS≤6 y la unidad es Positiva.

## 3. Clasificación Taxonómica
Asigna cada unidad a UNA dimensión de la Taxonomía Oficial (lista más abajo).

Criterios:
- Prioriza la dimensión específica sobre la genérica. Si el estudiante menciona "las aulas", clasifica como "Aulas de clase", NO como "Espacios comunes".
- Si la unidad expresa satisfacción general sin dimensión específica ("es una buena universidad", "estoy contento"), usa "Satisfacción estudiantil".
- Si menciona espacios genéricos del campus sin especificar aulas/laboratorios/biblioteca ("los espacios", "las instalaciones", "el campus"), usa "Espacios comunes".
- Si NO puedes identificar la dimensión con confianza razonable, usa "Pendiente de Clasificación". NUNCA inventes dimensiones que no estén en la lista.
- La `categoria_padre` se deduce automáticamente de la dimensión elegida (ver mapeo abajo).

## 4. Validez de la Unidad
Marca `es_valido = false` cuando la unidad sea:
- "Caracter suelto sin significado" (ej: "y", "pero", "además", "..", "x", "o").
- "Ruido/Sin sentido" (ej: "asdf", "nn", "jaja", caracteres aleatorios).
- "Respuesta vacía" (ej: " ", "-", "", sin contenido).
- "Frase repetida en la respuesta" (duplicado casi-exacto de otra unidad del mismo comentario).
- "Solo repite la calificación" (ej: "le doy 8" cuando el NPS es 8).
- "Respuesta genérica sin información específica" (ej: "todo normal", "nada que decir", "todo bien").
- "Frase muy general sin contenido específico".
- "Frase incompleta sin sentido".

Las unidades no válidas igual reciben sentimiento (Neutro, intensidad 1) y dimensión ("Pendiente de Clasificación").

## 5. Triangulación Cualitativa-Cuantitativa (Cross-reference CSAT)
El estudiante calificó cada dimensión con una escala CSAT. El usuario del prompt te pasará, para este estudiante, un diccionario {{dimensión: calificación}}.

Cuando la unidad mencione una dimensión que el estudiante SÍ calificó:
- Reporta la calificación textual en `dimension_evaluada_rating` (ej. "Muy satisfecho").
- Reporta el score numérico en `dimension_evaluada_score` (Totalmente satisfecho=5, Muy satisfecho=4, Satisfecho=3, Insatisfecho=2, Totalmente insatisfecho=1, No utilizo=0, No conozco=0).

Cuando la dimensión NO fue calificada, o el estudiante respondió "No utilizo"/"No conozco", o la unidad es "Pendiente de Clasificación"/"Satisfacción estudiantil"/"Espacios comunes" (que no tienen pregunta CSAT directa):
- Devuelve `dimension_evaluada_rating = null` y `dimension_evaluada_score = null`.

# TAXONOMÍA OFICIAL (encuesta actual)

{taxonomia_str}

# FORMATO DE SALIDA — JSON ESTRICTO

Devuelve EXCLUSIVAMENTE un objeto JSON con esta forma (sin texto antes ni después, sin markdown fences):

{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "texto exacto de la unidad (recortado de conectores sobrantes)",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 3,
      "justificacion_sentimiento": "Breve justificación (máx 1 línea) de por qué este sentimiento e intensidad, mencionando si aplicó la regla de contexto NPS.",
      "dimension": "Aulas de clase",
      "categoria_padre": "Infraestructura",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Muy satisfecho",
      "dimension_evaluada_score": 4,
      "sub_aspectos": ["aulas", "comodidad"]
    }}
  ]
}}

Reglas del JSON:
- `orden`: entero secuencial desde 1, en el orden en que aparecen las unidades en el comentario.
- `sentimiento`: exactamente uno de "Positivo", "Negativo", "Neutro" (con mayúscula inicial).
- `intensidad`: entero 1-5.
- `motivo_invalidez`: null si es_valido=true; si es_valido=false, una de las 8 categorías listadas en la sección 4 (textual).
- `dimension`: una de las dimensiones de la Taxonomía Oficial (textual exacto).
- `categoria_padre`: la categoría padre correspondiente a la dimensión (textual exacto).
- `sub_aspectos`: lista de sustantivos clave extraídos de la unidad (máx 5, min 0), en minúsculas. Útil para análisis transversal.
- `dimension_evaluada_rating` / `dimension_evaluada_score`: null si no aplica.

# EJEMPLOS CALIBRADOS (few-shot)

Los ejemplos abajo están calibrados contra el análisis manual humano de la encuesta 2026-1. Sigue este nivel de granularidad.

---
EJEMPLO 1 — Promotor (NPS 10), comentario corto:
Entrada: comentario="Muy buena infraestructura, enseñanza.", nps=10, csat={{"Aulas de clase": "Totalmente satisfecho", "Calidad de la enseñanza en la carrera": "Muy satisfecho"}}
Salida:
{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "Muy buena infraestructura",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 4,
      "justificacion_sentimiento": "Promotor; adjetivo intenso 'muy buena' sobre infraestructura. Intensidad 4 por modificador 'muy' + sustantivo valorado.",
      "dimension": "Aulas de clase",
      "categoria_padre": "Infraestructura",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Totalmente satisfecho",
      "dimension_evaluada_score": 5,
      "sub_aspectos": ["infraestructura", "aulas"]
    }},
    {{
      "orden": 2,
      "texto": "enseñanza",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 3,
      "justificacion_sentimiento": "Promotor; en contexto de 'muy buena infraestructura, enseñanza' se sobreentiende positiva. Intensidad 3 (moderado, implícito).",
      "dimension": "Calidad de la enseñanza en la carrera",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Muy satisfecho",
      "dimension_evaluada_score": 4,
      "sub_aspectos": ["enseñanza"]
    }}
  ]
}}

---
EJEMPLO 2 — Detractor (NPS 3), comentario con 3 unidades y 1 salvavidas:
Entrada: comentario="Ultimamente me he topado con antibajos en la carrera y apesar de eso sali adelante pero hay varias cosas que no me gustaron d la carrera.", nps=3, csat={{"Calidad de la enseñanza en la carrera": "Insatisfecho", "La carrera": "Insatisfecho"}}
Salida:
{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "Ultimamente me he topado con antibajos en la carrera",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 3,
      "justificacion_sentimiento": "Detractor; 'antibajos' = docentes que reprueban mucho. Negativo moderado acorde al NPS bajo.",
      "dimension": "Calidad de la enseñanza en la carrera",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Insatisfecho",
      "dimension_evaluada_score": 2,
      "sub_aspectos": ["antibajos", "carrera"]
    }},
    {{
      "orden": 2,
      "texto": "apesar de eso sali adelante",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 2,
      "justificacion_sentimiento": "Detractor; unidad Positiva = salvavidas ('sali adelante'). Intensidad 2 (leve, sin adjetivación fuerte).",
      "dimension": "Satisfacción estudiantil",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": true,
      "dimension_evaluada_rating": null,
      "dimension_evaluada_score": null,
      "sub_aspectos": ["adelante"]
    }},
    {{
      "orden": 3,
      "texto": "pero hay varias cosas que no me gustaron d la carrera",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 3,
      "justificacion_sentimiento": "Detractor; queja genérica pero acorde al NPS bajo. Intensidad 3 (moderado, sin adjetivo fuerte).",
      "dimension": "La carrera",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Insatisfecho",
      "dimension_evaluada_score": 2,
      "sub_aspectos": ["carrera"]
    }}
  ]
}}

---
EJEMPLO 3 — Pasivo (NPS 8), comentario mixto:
Entrada: comentario="Tiene buena infraestructura pero creo que falta comunicación con los alumnos sobre cómo van las clases", nps=8, csat={{"Aulas de clase": "Satisfecho", "Calidad de la enseñanza en la carrera": "Satisfecho"}}
Salida:
{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "Tiene buena infraestructura",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 3,
      "justificacion_sentimiento": "Pasivo; unidad Positiva. Intensidad 3 (descriptor simple 'buena' = moderado).",
      "dimension": "Espacios comunes",
      "categoria_padre": "Infraestructura",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": null,
      "dimension_evaluada_score": null,
      "sub_aspectos": ["infraestructura"]
    }},
    {{
      "orden": 2,
      "texto": "pero creo que falta comunicación con los alumnos sobre cómo van las clases",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 2,
      "justificacion_sentimiento": "Pasivo; unidad Negativa. Intensidad 2 (leve, 'falta' sin adjetivación fuerte). Respeta techo de intensidad 3 del Pasivo.",
      "dimension": "Claridad de los recursos académicos",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": null,
      "dimension_evaluada_score": null,
      "sub_aspectos": ["comunicación", "alumnos", "clases"]
    }}
  ]
}}

---
EJEMPLO 4 — Detractor (NPS 1), comentario con queja fuerte:
Entrada: comentario="Hay demasiados cursos para rellenar la matrícula, cursos que podrían ser electivos. La carrera está estúpidamente alargada en comparación con otras universidades.", nps=1, csat={{"Plan curricular y perfil de egreso": "Totalmente insatisfecho", "La carrera": "Totalmente insatisfecho"}}
Salida:
{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "Hay demasiados cursos para rellenar la matrícula",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 3,
      "justificacion_sentimiento": "Detractor; 'demasiados' = énfasis léxico. Intensidad 3.",
      "dimension": "Plan curricular y perfil de egreso",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Totalmente insatisfecho",
      "dimension_evaluada_score": 1,
      "sub_aspectos": ["cursos", "matrícula"]
    }},
    {{
      "orden": 2,
      "texto": "cursos que podrían ser electivos",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 2,
      "justificacion_sentimiento": "Detractor; crítica constructiva leve. Intensidad 2.",
      "dimension": "Plan curricular y perfil de egreso",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Totalmente insatisfecho",
      "dimension_evaluada_score": 1,
      "sub_aspectos": ["cursos", "electivos"]
    }},
    {{
      "orden": 3,
      "texto": "La carrera está estúpidamente alargada en comparación con otras universidades",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Negativo",
      "intensidad": 4,
      "justificacion_sentimiento": "Detractor; adjetivo fuerte 'estúpidamente'. Intensidad 4.",
      "dimension": "Plan curricular y perfil de egreso",
      "categoria_padre": "Académico",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Totalmente insatisfecho",
      "dimension_evaluada_score": 1,
      "sub_aspectos": ["carrera", "duración"]
    }}
  ]
}}

---
EJEMPLO 5 — Ruido (cualquier NPS), comentario no válido:
Entrada: comentario="..", nps=7, csat={{}}
Salida:
{{
  "unidades": [
    {{
      "orden": 1,
      "texto": "..",
      "es_valido": false,
      "motivo_invalidez": "Caracter suelto sin significado",
      "sentimiento": "Neutro",
      "intensidad": 1,
      "justificacion_sentimiento": "Ruido; no hay contenido para clasificar.",
      "dimension": "Pendiente de Clasificación",
      "categoria_padre": "Pendiente de Clasificación",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": null,
      "dimension_evaluada_score": null,
      "sub_aspectos": []
    }}
  ]
}}

# RESTRICCIONES FINALES
- Devuelve SOLO el JSON. Nada de texto explicativo antes o después. Nada de markdown fences.
- NUNCA inventes dimensiones que no estén en la Taxonomía Oficial.
- NUNCA ignores la regla de contexto NPS: si clasificas un Promotor con mayoría Negativa sin justificación muy fuerte, estás cometiendo un error.
- Si el comentario está vacío o es solo espacios, devuelve una unidad no válida con motivo "Respuesta vacía".
- Conserva el texto original del estudiante tal cual (errores ortográficos incluidos) en el campo `texto`.
"""


# ============================================================
# CONSTRUCCIÓN DEL USER PROMPT (por comentario)
# ============================================================

def build_user_prompt(comentario: str,
                      nps_score: int,
                      csat_ratings: Dict[str, str],
                      id_encuesta: str = "") -> str:
    """Construye el user prompt para un comentario específico.

    Args:
        comentario: texto del comentario abierto (máx ~100 chars en esta encuesta).
        nps_score: score NPS del estudiante (0-10).
        csat_ratings: dict {dimension: rating_textual} que el estudiante calificó.
                      Solo incluye dimensiones con respuesta válida (excluye vacíos).
        id_encuesta: ID de la respuesta (para trazabilidad, opcional).

    Returns:
        User prompt listo para enviar a DeepSeek.
    """
    segmento = "Promotor" if nps_score >= 9 else ("Pasivo" if nps_score >= 7 else "Detractor")

    # Formatear CSAT ratings como lista legible
    if csat_ratings:
        csat_lines = []
        for dim, rating in csat_ratings.items():
            csat_lines.append(f'  "{dim}": "{rating}"')
        csat_str = "{\n" + ",\n".join(csat_lines) + "\n}"
    else:
        csat_str = "{}  // El estudiante no calificó ninguna dimensión CSAT"

    # Escapar comillas dobles en el comentario para JSON válido
    comentario_esc = comentario.replace('"', '\\"')

    return f"""Analiza el siguiente comentario del estudiante.

ID encuesta: {id_encuesta or "(sin id)"}
NPS: {nps_score} → Segmento: {segmento}
CSAT por dimensión (lo que el estudiante calificó):
{csat_str}

Comentario: "{comentario_esc}"

Devuelve el JSON con la lista de unidades de significado."""


# ============================================================
# SCHEMA JSON PARA VALIDACIÓN POST-LLM (referencia)
# ============================================================

OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["unidades"],
    "properties": {
        "unidades": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "orden", "texto", "es_valido", "motivo_invalidez",
                    "sentimiento", "intensidad", "justificacion_sentimiento",
                    "dimension", "categoria_padre",
                    "es_mencion_mejora", "es_salvavidas",
                    "dimension_evaluada_rating", "dimension_evaluada_score",
                    "sub_aspectos"
                ],
                "properties": {
                    "orden": {"type": "integer", "minimum": 1},
                    "texto": {"type": "string"},
                    "es_valido": {"type": "boolean"},
                    "motivo_invalidez": {"type": ["string", "null"]},
                    "sentimiento": {
                        "type": "string",
                        "enum": ["Positivo", "Negativo", "Neutro"]
                    },
                    "intensidad": {"type": "integer", "minimum": 1, "maximum": 5},
                    "justificacion_sentimiento": {"type": "string"},
                    "dimension": {"type": "string"},
                    "categoria_padre": {"type": "string"},
                    "es_mencion_mejora": {"type": "boolean"},
                    "es_salvavidas": {"type": "boolean"},
                    "dimension_evaluada_rating": {"type": ["string", "null"]},
                    "dimension_evaluada_score": {"type": ["integer", "null"], "minimum": 0, "maximum": 5},
                    "sub_aspectos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 5
                    }
                }
            }
        }
    }
}


# Mapeo de rating CSAT textual → score numérico (single source of truth)
RATING_TO_SCORE = {
    "Totalmente satisfecho": 5,
    "Muy satisfecho": 4,
    "Satisfecho": 3,
    "Insatisfecho": 2,
    "Totalmente insatisfecho": 1,
    "No utilizo": 0,
    "No conozco": 0,
}


def rating_to_score(rating: Optional[str]) -> Optional[int]:
    """Convierte un rating textual CSAT a score numérico. None si no mapea."""
    if rating is None:
        return None
    return RATING_TO_SCORE.get(rating)
