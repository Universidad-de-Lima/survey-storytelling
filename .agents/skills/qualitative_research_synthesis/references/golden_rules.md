# Golden Rules for Qualitative Research Synthesis

This document contains the source of truth for how comments should be chunked and classified based on the user's manual curation. Use this to align your LLM reasoning.

## Taxonomy (Dimensiones Oficiales)
- Académico -> Satisfacción estudiantil
- Académico -> Calidad de la formación académica
- Académico -> Cursos del programa y contenidos
- Académico -> Plan curricular y perfil de egreso
- Académico -> Exigencia académica
- Académico -> Evaluación del aprendizaje
- Académico -> La carrera
- Académico -> Perfil del egreso de la carrera
- Docencia -> Calidad de la enseñanza en la carrera
- Docencia -> Conocimientos actualizados
- Docencia -> Disponibilidad para asesorías
- Docencia -> Retroalimentación
- Infraestructura -> Aulas de clase
- Infraestructura -> Ambientes y salas para estudio
- Infraestructura -> Espacios de alimentación
- Infraestructura -> Equipamiento tecnológico en laboratorios
- Infraestructura -> Ubicación
- Administrativo y Bienestar -> Ayuda financiera
- Administrativo y Bienestar -> Actividades deportivas
- Administrativo y Bienestar -> Servicio de atención psicopedagógica
- Administrativo y Bienestar -> Información sobre el récord académico
- Tecnología -> Conexión Wi-Fi en el campus
- Tecnología -> Soporte técnico del sistema informático

## Chunking & Coding Examples (Golden Dataset)

| Comentario Original | Fragmento Curado | Tema Padre | Tema |
|---|---|---|---|
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | Debido a que me gusta la universidad | Académico | Satisfacción estudiantil |
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | Debido a que me gusta la calidad de enseñanza | Académico | Satisfacción estudiantil |
| Debido a que me gusta la universidad, calidad de enseñanza, y la recomendaría | La recomendaría | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Estoy satisfecha | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Pero aún hay cosas que mejorar | Académico | Satisfacción estudiantil |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Falta de aire en las torres antiguas | Infraestructura | Ambientes y salas para estudio |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Falta de enchufes en las aulas | Infraestructura | Aulas de clase |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Mal funcionamiento de los ascensores de los edificios O | Infraestructura | Ambientes y salas para estudio |
| Estoy satisfecha pero aún hay cosas que mejorar: Falta de aire en las torres antiguas, falta de enchufes en las aulas, mal funcionamiento de las ascensores de O, clases virtuales innecesarias, etc | Clases virtuales innecesarias | Académico | Cursos del programa y contenidos |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Va en buen camino | Académico | Satisfacción estudiantil |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Hay cosas por mejorar | Académico | Satisfacción estudiantil |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Hay muchas construcciones innecesarias | Infraestructura | Ambientes y salas para estudio |
| Va en buen camino pero hay cosas por mejorar, me parece que hay muchas construcciones innecesarias y el servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | El servicio técnico, al menos en mi experiencia, ha sido poco satisfactorio | Tecnología | Soporte técnico del sistema informático |
| Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil, aunque sigue cumpliendo en lo que hace bien | Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil | Académico | Satisfacción estudiantil |
| Es una universidad muy estandarizada en el modo de como hace muy poco para diferenciarse y sigue las mismas tendencias que cualquier otro centro estudiantil, aunque sigue cumpliendo en lo que hace bien | Sigue cumpliendo en lo que hace bien | Académico | Satisfacción estudiantil |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | En general es muy recomendable | Académico | Satisfacción estudiantil |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | Lo único que me incomoda es la organización de los patios de comidas | Infraestructura | Espacios de alimentación |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | Una sola persona por patio atiende a todo la inmensa fila | Infraestructura | Espacios de alimentación |
| En general es muy recomendable, lo único que me incomoda es la organización de los patios de comidas, una sola persona por patio atiende a todo la inmensa fila y no todos logran tener espacio en mesa. | No todos logran tener espacio en mesa | Infraestructura | Espacios de alimentación |
| La universidad si la carrera no | La universidad si | Académico | Satisfacción estudiantil |
| La universidad si la carrera no | La carrera no | Académico | La carrera |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | Tiene muchas cosas buenas | Académico | Satisfacción estudiantil |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | Lo que falla son los espacios para almorzar | Infraestructura | Espacios de alimentación |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | La calidad de profesores | Académico | Calidad de la enseñanza en la carrera |
| Tiene muchas cosas buenas , lo que falla son los espacios para almorzar, la calidad de profesores y la formentacion de amistades dentro de la universidad | La formentacion de amistades dentro de la universidad | Académico | Satisfacción estudiantil |
