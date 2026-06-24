# Taxonomy Mapping: ETL ↔ Skill (v1.0)

Este documento establece el mapeo oficial entre la taxonomía del ETL y la Skill de Análisis Cualitativo. **El ETL es la fuente de verdad.** Cualquier divergencia se resuelve a favor del ETL.

## Fuente de verdad

| Componente | Archivo | Responsabilidad |
|------------|---------|-----------------|
| Taxonomía oficial | `zoho-survey/scripts/lib/config.py` → `CATEGORIA_DIMENSION_PREGRADO`, `CATEGORIA_DIMENSION_GRADUADO` | Define las dimensiones y categorías padre válidas. |
| Alias de normalización | `zoho-survey/scripts/lib/aspect_extraction.py` → `ALIAS_DICT_MANUAL` | Define cómo se normalizan términos a dimensiones. |
| Skill (esta) | `.agents/skills/qualitative_research_synthesis/` | Síntesis e interpretación. NO reclasifica. |

## Decisiones de divergencia resueltas

### Divergencia 1: "Calidad de la enseñanza en la carrera"

| Aspecto | Skill antigua (pre-Fase 8) | ETL (fuente de verdad) | Decisión |
|---------|---------------------------|------------------------|----------|
| Categoría padre | Docencia | Académico | **Usar Académico** |

**Justificación**: `CATEGORIA_DIMENSION_PREGRADO` en `config.py` mapea "Calidad de la enseñanza en la carrera" → "Académico". La categoría "Docencia" solo existe en `CATEGORIA_DIMENSION_GRADUADO` y contiene dimensiones distintas (Transmisión de conocimientos, Metodologías, etc.). La Skill antigua confundía ambas.

### Divergencia 2: Mapeo de "ascensores" / "elevador"

| Aspecto | Skill antigua (pre-Fase 8) | ETL (fuente de verdad) | Decisión |
|---------|---------------------------|------------------------|----------|
| Bucket | Ambientes y salas para estudio | Aulas de clase | **Usar Aulas de clase** |

**Justificación**: En Fase 6 se agregaron los alias `ascensor`, `ascensores`, `elevador`, `elevadores` al bucket `Aulas de clase` en `ALIAS_DICT_MANUAL` (porque este bucket agrupa "instalaciones" incluyendo enchufes, mobiliario, etc.). El Golden Dataset de la Skill antigua los ponía en "Ambientes y salas para estudio", pero esa decisión fue revisada y el ETL es ahora la fuente de verdad.

### Divergencia 3: "Valoración General" (legacy)

| Aspecto | Skill antigua (pre-Fase 8) | ETL (fuente de verdad) | Decisión |
|---------|---------------------------|------------------------|----------|
| Existencia | Existía como categoría | NO existe en `CATEGORIA_DIMENSION_*` | **Eliminar** |

**Justificación**: "Valoración General" es residuo legacy de `nlp.py` (función deprecated `agrupar_comentarios_por_topico`). No existe en la taxonomía oficial. La Skill antigua la incluía en el loop de insights, pero el ETL nunca la produce. En Fase 8 se elimina del loop de `insights_generator.py`.

### Divergencia 4: Dimensiones de Docencia y Desarrollo Profesional

| Aspecto | Skill antigua (pre-Fase 8) | ETL (fuente de verdad) | Decisión |
|---------|---------------------------|------------------------|----------|
| Cobertura | No mencionaba estas categorías | Existen en `CATEGORIA_DIMENSION_GRADUADO` y el ETL las permite vía unión de mapas | **Incluir en insights** |

**Justificación**: `CATEGORIA_PADRE_MAP` en `aspect_extraction.py` es la unión de pregrado + graduado. Por eso, los comentarios de pregrado pueden clasificarse en "Docencia" (57 comentarios en undergraduate 2026-1) o "Desarrollo Profesional" (11 comentarios). La Skill antigua no los contemplaba. En Fase 8, `insights_generator.py` incluye estas categorías en el loop de insights por categoría padre.

## Mapeo de alias comunes (extracto de ALIAS_DICT_MANUAL)

Estos son los alias más comunes y su dimensión oficial. La Skill debe respetar este mapeo al clasificar manualmente.

### Académico
| Alias | Dimensión oficial |
|-------|-------------------|
| profesor, profesores, docente, docentes, profe, profes, enseñanza, pedagogia, trato, explicacion, metodologia | Calidad de la enseñanza en la carrera |
| curso, cursos, electivo, electivos, temas, contenido, clases virtuales | Cursos del programa y contenidos |
| malla, curricula, plan de estudios, silabo | Plan curricular y perfil de egreso |
| formacion, calidad, educacion, nivel educativo, prestigio, academico, aprendizaje, preparacion | Calidad de la formación académica |
| exigencia, dificultad, nivel, exigente, facil, dificil | Exigencia académica |
| examen, examenes, evaluacion, evaluaciones, practica, practicas, nota, notas, calificacion, rubrica, evaluar | Evaluación del aprendizaje |
| intercambio, viaje, extranjero, convenio, convenios | Intercambio estudiantil |
| carrera, facultad | La carrera |
| satisfecho, satisfecha, recomiendo, recomendaria, buena, bien, genial, excelente, me gusta, conforme, estandarizada, universidad si, buen camino, cosas buenas | Satisfacción estudiantil |
| perfil, egreso, egresado, perfil del egresado | Perfil del egreso de la carrera |
| recursos, materiales, diapositivas, lecturas | Claridad de los recursos académicos |

### Administrativo y Bienestar
| Alias | Dimensión oficial |
|-------|-------------------|
| record, notas, promedio, ponderado, quinto, tercio, rendimiento | Información sobre el récord académico |
| libro, libros, bibliografia, revista, revistas, base de datos | Material bibliográfico en la biblioteca |
| atencion, personal, administrativo, secretaria, orientacion, trato | Atención del personal administrativo |
| matricula, inscripcion, cupo, cupos, turno, turnos, sistema de matricula, tramites, burocracia, organización, organizado | Procedimientos administrativos |
| pension, pensiones, pago, pagos, beca, becas, economia, economico, recategorizacion, categorizacion, boleta, asequibilidad | Ayuda financiera |
| medico, topico, salud, enfermeria, emergencia | Servicio médico y su infraestructura |
| psicologo, psicologia, psicopedagogico, psicologica, salud mental, terapia | Servicio de atención psicopedagógica |
| taller, talleres, arte, cultura, danza, musica, teatro | Talleres de actividades artísticas y culturales |
| deporte, deportes, cancha, canchas, gimnasio, gym, entrenamiento, seleccion, variedad deportiva | Actividades deportivas |
| empleabilidad, trabajo, practicas, bolsa de trabajo, alumni, egresados, contacto con empresas, oportunidades, empleo, laboral | Empleabilidad, vinculación y ALUMNI |

### Infraestructura
| Alias | Dimensión oficial |
|-------|-------------------|
| aula, aulas, salon, salones, carpeta, carpetas, silla, sillas, comodidad, mobiliario, pizarra, pizarras, aire acondicionado, ventilacion, enchufe, enchufes, instalaciones, **ascensor, ascensores, elevador, elevadores** | Aulas de clase |
| espacio de estudio, espacios de estudio, cubiculo, cubiculos, biblioteca, mesas, mesas libres, zona de estudio, áreas, construcciones, construccion, aire | Ambientes y salas para estudio |
| laboratorio, laboratorios, pc, pcs, computadora, computadoras, mac, macs, impresora, impresoras, equipo, equipos, tecnología | Equipamiento tecnológico en laboratorios |
| condiciones del laboratorio, ruido en laboratorio, iluminacion, seguridad | Condiciones ambientales en laboratorios |
| ubicacion, lejos, lejania, distancia, trafico, llegar, transporte, bus | Ubicación |
| comida, comedor, cafeteria, cafeterias, kiosko, kioskos, precio, almuerzo, menu, patio de comidas, patio, colas, microondas, sobrepoblacion | Espacios de alimentación |

### Tecnología
| Alias | Dimensión oficial |
|-------|-------------------|
| software, programa, licencia, licencias, aplicacion | Software especializado empleado en la carrera |
| miulima, portal, sistema | Portal web de la Universidad (Mi Ulima) |
| blackboard, correo, zoom, intranet, clases virtuales, virtual | Aula virtual |
| wifi, wi-fi, internet, red, señal, conexion, conectividad, datos | Conexión Wi-Fi en el campus |
| soporte, tecnico, ayuda tecnica, fallas, mesa de ayuda | Soporte técnico del sistema informático |

### Docencia (solo graduado formalmente, pero ETL permite en pregrado)
| Alias | Dimensión oficial |
|-------|-------------------|
| conocimiento, conocimientos, sabe, saben, dominio | Transmisión de conocimientos |
| experiencia, experiencias, casos, vida real | Transmisión de experiencias |
| metodologia, didactica, forma de enseñar, metodo | Metodologías |
| actualizado, actualizados, moderno, modernos, vanguardia, obsoleto | Conocimientos actualizados |
| compromiso, interes, dedicacion, se preocupa | Compromiso |
| feedback, retroalimentacion, correccion, correcciones | Retroalimentación |
| asesoria, asesorias, consulta, consultas, dudas, tiempo, disponibilidad | Disponibilidad para asesorías |
| puntualidad, tarde, normas, reglas, programa, silabo | Cumplimiento de normas y programas |

### Desarrollo Profesional (solo graduado formalmente, pero ETL permite en pregrado)
| Alias | Dimensión oficial |
|-------|-------------------|
| trabajo grupal, trabajos grupales, grupo, grupos, equipo, compañeros, compañeros, amistades | Habilidades para trabajar en equipo |
| comunicacion, hablar, exposicion, exposiciones, expresion | Habilidades de comunicación |
| ideas, innovacion, creatividad, aporte | Habilidades para aportar nuevas ideas |
| perspectiva, futuro, oportunidad laboral | Mejora en perspectivas de empleo |

## Cómo usar este mapeo

1. **Al clasificar manualmente**: buscar el término en la tabla de alias y usar la dimensión oficial indicada.
2. **Al validar clasificaciones del ETL**: comparar la clasificación del ETL con el mapeo de alias. Si difieren, el ETL tiene prioridad (puede usar embeddings que produjeron mejor match).
3. **Al generar síntesis**: usar los nombres oficiales de dimensiones y categorías padre, no alias informales.
4. **Cuando un término no está en la tabla**: clasificar como `Pendiente de Clasificación` (igual que el ETL). No inventar mapeos.

## Mantenimiento

Este mapeo debe actualizarse cuando:
- Se agreguen nuevos alias a `ALIAS_DICT_MANUAL` en `aspect_extraction.py`.
- Se agreguen nuevas dimensiones a `CATEGORIA_DIMENSION_*` en `config.py`.
- Se resuelvan nuevas divergencias entre Skill y ETL.

La fuente de verdad siempre es el código del ETL (`lib/config.py` y `lib/aspect_extraction.py`). Este documento es un espejo para referencia de agentes IA y analistas humanos.
