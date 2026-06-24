# Golden Rules for Qualitative Research Synthesis (v2.0)

This document contains the source of truth for how comments should be chunked and classified. Use this to align your LLM reasoning with the ETL pipeline.

## Principio fundamental

**El ETL es la fuente de verdad.** Esta Skill no crea categorías nuevas, no reinterpretar sentimiento, no duplica el pipeline automático. Su rol es de síntesis, interpretación y validación humana.

## Taxonomía oficial (fuente: `lib/config.py`)

La taxonomía oficial vive en `CATEGORIA_DIMENSION_PREGRADO` (32 dimensiones) y `CATEGORIA_DIMENSION_GRADUADO` (39 dimensiones). Ver `taxonomy_mapping.md` para el mapeo completo con decisiones de divergencia resueltas.

### Categorías padre oficiales (7 total)

| Categoría padre | Dimensiones (pregrado) | Dimensiones (graduado) | Notas |
|-----------------|-------------------------|------------------------|-------|
| Académico | 11 | 11 | Incluye "Calidad de la enseñanza en la carrera" |
| Administrativo y Bienestar | 10 | 10 | Incluye empleabilidad y ALUMNI |
| Infraestructura | 6 | 6 | Incluye "Aulas de clase" (ascensores van aquí) |
| Tecnología | 5 | 5 | Incluye Wi-Fi, soporte técnico, aula virtual |
| Docencia | 0 (solo graduado) | 8 | NO existe en pregrado; el ETL la permite vía unión de mapas |
| Desarrollo Profesional | 0 (solo graduado) | 4 | NO existe en pregrado; el ETL la permite vía unión de mapas |
| Pendiente de Clasificación | — | — | Pseudo-categoría para comentarios sin clasificación |

### Categorías NO oficiales (legacy, eliminar de análisis)

- **"Valoración General"**: NO existe en `CATEGORIA_DIMENSION_*`. Es residuo legacy de `nlp.py`. **Nunca usar**.

## Reglas de oro

### Regla 1: ETL como fuente de verdad
El pipeline ETL (`build_json.py` + `lib/*.py`) es la única fuente oficial de:
- Segmentación en Meaning Units.
- Clasificación Tema Padre + Tema.
- Sentimiento + intensidad.
- Insights automáticos (`lib/insights_generator.py` Fase 8).

La Skill no reclasifica, no resegmenta, no reasigna sentimiento. Solo sintetiza e interpreta.

### Regla 2: No crear categorías nuevas
Si un comentario no encaja en ninguna dimensión oficial, clasificar como `Pendiente de Clasificación`. No inventar categorías como "Servicios", "Otros", "General".

### Regla 3: No reinterpretar sentimiento
El sentimiento es asignado por `sentiment_engine.py` con calibración Fase 7. La confianza < 0.4 fuerza `neutro`. La Skill no debe deshacer esta calibración. Si hay desacuerdo, marcar como `Revisar` en tabla de validación.

### Regla 4: Excluir "Pendiente de Clasificación" de insights
Al generar síntesis narrativa o identificar temas relevantes, SIEMPRE excluir "Pendiente de Clasificación" del cálculo. Esta pseudo-categoría representa fallas del clasificador, no un tema real.

### Regla 5: Trazabilidad con datos origen
Toda afirmación debe incluir datos cuantitativos: conteos, porcentajes, distribución. Evitar frases genéricas sin respaldo numérico.

### Regla 6: Usar mapeo oficial de alias
Algunos términos tienen mapeo no intuitivo pero oficial (ver `taxonomy_mapping.md` para detalle):
- "ascensores" / "elevador" → `Aulas de clase` (Infraestructura) — NO "Ambientes y salas para estudio".
- "internet" / "wifi" → `Conexión Wi-Fi en el campus` (Tecnología).
- "profes" / "docentes" → `Calidad de la enseñanza en la carrera` (Académico) — NO "Docencia".
- "matrícula" / "inscripción" → `Procedimientos administrativos` (Administrativo y Bienestar).

## Golden Dataset (ejemplos curados)

Estos ejemplos representan la "verdad humana" para validación del ETL. Use para alinear razonamiento del LLM con clasificaciones esperadas.

| Comentario Original | Fragmento Curado | Tema Padre | Tema |
|---|---|---|---|
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | Debido a que me gusta la universidad | Académico | Satisfacción estudiantil |
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | Debido a que me gusta la calidad de enseñanza | Académico | Satisfacción estudiantil |
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | La recomendaría | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Estoy satisfecha | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Pero aún hay cosas que mejorar | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Falta de aire en las torres antiguas | Infraestructura | Ambientes y salas para estudio |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Falta de enchufes en las aulas | Infraestructura | Aulas de clase |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Mal funcionamiento de los ascensores de los edificios O | Infraestructura | Aulas de clase |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Clases virtuales innecesarias | Académico | Cursos del programa y contenidos |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Va en buen camino | Académico | Satisfacción estudiantil |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Hay cosas por mejorar | Académico | Satisfacción estudiantil |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Hay muchas construcciones innecesarias | Infraestructura | Ambientes y salas para estudio |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | El servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Tecnología | Soporte técnico del sistema informático |
| Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil, aunque sigue cumpliendo en lo que hace bien | Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil | Académico | Satisfacción estudiantil |
| Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil, aunque sigue cumpliendo en lo que hace bien | Sigue cumpliendo en lo que hace bien | Académico | Satisfacción estudiantil |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | En general es muy recomendable | Académico | Satisfacción estudiantil |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atende a todo la inmensa fila y no todos logran tener espacio en mesa. | Lo único que me incomoda es la organización de los patios de comidas | Infraestructura | Espacios de alimentación |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | Una sola persona por patio atiende a todo la inmensa fila | Infraestructura | Espacios de alimentación |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | No todos logran tener espacio en mesa | Infraestructura | Espacios de alimentación |
| La universidad si la carrera no | La universidad si | Académico | Satisfacción estudiantil |
| La universidad si la carrera no | La carrera no | Académico | La carrera |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | Tiene muchas cosas buenas | Académico | Satisfacción estudiantil |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | Lo que falla son los espacios para almorzar | Infraestructura | Espacios de alimentación |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | La calidad de profesores | Académico | Calidad de la enseñanza en la carrera |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | La formentacion de amistades dentro de la universidad | Académico | Satisfacción estudiantil |

## Nota sobre divergencias con versiones anteriores

La versión anterior de este archivo (pre-Fase 8) tenía 23 dimensiones con 2 mapeos divergentes del ETL:
1. `Calidad de la enseñanza en la carrera` estaba en `Docencia` (incorrecto); el ETL la clasifica en `Académico`.
2. `Mal funcionamiento de los ascensores` estaba en `Ambientes y salas para estudio` (incorrecto); el ETL (Fase 6) la clasifica en `Aulas de clase` vía alias.

Estas divergencias fueron resueltas en Fase 8 alineando este archivo con el ETL. Ver `taxonomy_mapping.md` para el detalle de cada decisión.
