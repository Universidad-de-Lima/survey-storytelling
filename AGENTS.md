# Reglas Para Agentes IA

Este archivo define reglas operativas obligatorias para agentes que inspeccionan o modifican el repositorio.

## Fuentes Canonicas

- `README.md`: entrada general y mapa documental.
- `ARCHITECTURE.md`: arquitectura tecnica, capas, modulos y deuda vigente.
- `CONTRACTS.md`: contratos CSV/JSON e invariantes de datos (version humana).
- `zoho-survey/scripts/schemas/*.schema.json`: contratos formales JSON Schema Draft-07 (fuente de tipos).
- `docs/developer-guide.md`: guia operativa corta para cambios comunes.
- `tests/README.md`: ejecucion y extension de tests.

No duplicar estas fuentes en nuevos documentos.

## Arquitectura Real (leer antes de modificar)

Antes de tocar codigo, comprender la arquitectura real (no la documentacion previa a v3.0):

### ETL Python (`zoho-survey/scripts/`)

- **`build_json.py`** (~820 lineas): orquestador del pipeline CSV → JSON.
- **`lib/`** contiene **7 modulos activos** (no 4 como en documentacion previa):
  - `config.py` — mapeos de columnas y catalogos de negocio.
  - `metrics.py` — `calc_nps`, `calc_csat` (funciones puras).
  - `io_helper.py` — `load_json`, `read_csv_robust`, `normalize_dates`.
  - `nlp.py` — `sanitizar_comentario` (activo); `agrupar_comentarios_por_topico` (267 lineas, **MUERTO**, no invocar).
  - `segmentacion_nps.py` — fragmentacion NPS con spaCy (Meaning Units).
  - `aspect_extraction.py` — extraccion de aspectos con spaCy + embeddings.
  - `sentiment_engine.py` — clasificacion hibrida sentimiento + intensidad.
- **`schemas/`** contiene **7 JSON Schemas Draft-07** que son la fuente formal de tipos.

### Frontend JS (`zoho-survey/shared/js/`)

- **13 modulos IIFE** expuestos via `window.Survey*`.
- **`dashboard.js`** (1015 lineas): orquestador principal.
- **Orden de carga critico**: ver `shared/README.md`. `dom-helpers.js` debe cargarse antes que `custom-select.js`.
- Las funciones globales son `window.SurveyTooltip.show/hide` (NO `window.showTooltip/hideTooltip`).

## Principios Del Proyecto

Priorizar:

- delegacion de eventos
- reutilizacion de componentes
- separacion entre datos y renderizado
- separacion entre configuracion y logica
- cambios incrementales y verificables

Evitar:

- reescrituras completas sin necesidad critica
- breaking changes innecesarios
- abstracciones prematuras
- sobreingenieria
- documentos nuevos si uno existente puede actualizarse

## Reglas JSON

Los JSON generados deben:

- permanecer compactos
- minimizar redundancia
- evitar anidamientos innecesarios
- mantener compatibilidad backward
- mantener contratos consistentes con los schemas Draft-07 en `scripts/schemas/`
- estar desacoplados del layout visual

Nunca:

- modificar manualmente JSON generados
- generar payloads innecesariamente grandes
- duplicar metadata repetitiva
- acoplar JSON a implementaciones visuales especificas
- agregar campos no declarados en el schema correspondiente (usar `additionalProperties: false`)

### Convencion de claves

- **NPS**: minusculas (`promotores`, `pasivos`, `detractores`). El frontend acepta ambos casings via `??` por compatibilidad backward, pero el ETL siempre produce minusculas.
- **CSAT**: capitalizado (`Totalmente satisfecho`, `Muy satisfecho`, etc.) porque proviene del catalogo Zoho Survey `RESPUESTAS_TEXTO`.
- **`año`**: entero (ej. `2026`), no string.
- **`periodo`**: string identificador (`"2026-1"` o `"2026"`).

## Reglas ETL

`zoho-survey/scripts/build_json.py` es la unica fuente oficial de transformacion.

Debe:

- permanecer idempotente (con caveat: si el CSV no tiene fechas validas, se usa `pd.Timestamp.now()` como fallback, lo que rompe idempotencia en ese edge case)
- validar columnas esperadas
- fallar explicitamente ante CSV invalidos
- minimizar procesamiento redundante
- generar estructuras consistentes con los schemas en `scripts/schemas/`

No debe:

- invocar `lib.nlp.agrupar_comentarios_por_topico` (codigo muerto, importado pero no usado)
- modificar el comportamiento de `lib.config.TOPICOS` o `lib.config.STOPWORDS` (legacy, no usados en modulos activos)
- introducir nuevos `print()` de depuracion en produccion

## Reglas Frontend

- Mantener Vanilla JS e IIFE con APIs `window.Survey*`.
- No introducir frameworks frontend ni dependencias runtime sin decision explicita.
- Sanitizar contenido externo antes de usar `innerHTML` (usar `SurveySanitizer.escapeHTML` o `sanitizeHTML`).
- Mantener compatibilidad con GitHub Pages y navegadores modernos.
- No usar inline event handlers (`onmousemove`, `onmouseleave`, etc.) — usar `addEventListener`. Excepcion conocida: `radar-chart.js` (pendiente de migracion).
- No referenciar `window.cache` (es privada en el IIFE de `dashboard.js`, siempre undefined).
- No invocar `SurveyTooltip.move` (no existe; pendiente implementacion o eliminacion de llamadas).

## Reglas GitHub Actions

Los workflows deben:

- minimizar commits innecesarios
- evitar loops automaticos
- evitar regeneraciones redundantes
- validar paths antes de commit
- minimizar tiempo de ejecucion y uso de runners

## Modulos Criticos (no modificar sin validacion)

Los siguientes archivos son single points of failure. Modificarlos requiere actualizar capas relacionadas en el mismo PR:

| Archivo | Impacto si se rompe |
| --- | --- |
| `zoho-survey/scripts/build_json.py` | ETL completo falla. |
| `zoho-survey/scripts/lib/config.py` | Mapeos de columnas y catalogos de negocio. Cambios requieren CSV fuente compatible. |
| `zoho-survey/scripts/lib/aspect_extraction.py` | `ALIAS_DICT_MANUAL` define normalizacion de aspectos. Cambios afectan `sentimiento.json`. |
| `zoho-survey/scripts/validate_generated_json.py` | Validacion de contratos. Cambios deben sincronizarse con schemas. |
| `zoho-survey/scripts/schemas/*.schema.json` | Fuente formal de tipos. Cambios deben propagarse a ETL, validador y CONTRACTS.md. |
| `zoho-survey/template/index.html` | IDs HTML son contratos publicos con `dashboard.js` y `filter-controller.js`. |
| `zoho-survey/shared/js/dashboard.js` | Orquestador monolitico (1015 lineas). |
| `zoho-survey/shared/js/config/constants.js` | Metas y reglas de negocio consumidas por 4 modulos. |

## Respuestas Tecnicas

Antes de recomendar cambios, inspeccionar el repositorio cuando sea posible.

Toda respuesta tecnica debe incluir, cuando aplique:

- diagnostico
- causa raiz
- impacto tecnico
- riesgos
- archivos afectados
- compatibilidad backward
- solucion concreta
- rutas reales
- validacion de que los schemas y el validador siguen siendo consistentes

## Checklist Antes de Modificar JSON Contracts

Si se modifica la estructura de cualquier JSON generado:

- [ ] Actualizar el schema correspondiente en `scripts/schemas/`.
- [ ] Actualizar `validate_generated_json.py` si hay nuevas invariantes de negocio.
- [ ] Actualizar `CONTRACTS.md` con el nuevo contrato.
- [ ] Actualizar `build_json.py` para producir la nueva estructura.
- [ ] Actualizar el frontend (`dashboard.js` o componente relevante) para consumir la nueva estructura.
- [ ] Ejecutar `npm run validate:json` y verificar que pasa.
- [ ] Verificar que los JSONs existentes siguen siendo validos (o regenerarlos).

## Advertencias Importantes Para Agentes IA

1. **No confiar en `scripts/README.md` previo a v3.0**: describia keyword matching, ya obsoleto. La version actual esta actualizada.
2. **No confiar en `shared/README.md` previo a v3.0**: decia `window.showTooltip/hideTooltip` (incorrecto, es `window.SurveyTooltip.show/hide`).
3. **`lib/nlp.py` tiene codigo muerto**: la funcion `agrupar_comentarios_por_topico` (267 lineas) esta importada por `build_json.py` pero NO se invoca. El motor cualitativo moderno usa `aspect_extraction` + `sentiment_engine`.
4. **`lib/config.py` tiene constantes legacy sin uso**: `TOPICOS` y `STOPWORDS` no se usan en modulos activos.
5. **Auto-download de spaCy**: ~~`aspect_extraction.py` y `sentiment_engine.py` llaman `spacy.cli.download("es_core_news_sm")` si el modelo no esta.~~ **ELIMINADO en Fase 6**: ahora fallan explícitamente con `OSError`. El modelo debe instalarse en CI/requirements.txt.
6. **`fragmentos_nps.json` y `dataset_cualitativo.json` no tienen schema formal**: son archivos intermedios del ETL, no contratos publicos. El frontend no los consume.
7. **Trabajo sin commitear**: el repositorio puede tener cambios pendientes. Revisar `git status` antes de modificar.
8. **`periodos.json` por nivel**: debe tener exactamente un item con `isNew: true`. El validador falla si no se cumple.
9. **Tests Python no ejecutados en CI**: ~~los tests en `scripts/tests/` solo corren manualmente.~~ **Fase 6**: workflow `tests.yml` creado, ejecuta unittest + JS tests + sintaxis en cada PR.
10. **Tests JS limitados**: ~~solo cubren `constants.js`, `formatters.js`, `sanitizer.js` (3 de 13 modulos).~~ **Fase 6**: suite reparada, 55/55 tests pasan. Cobertura sigue en 3/13 módulos (pendiente ampliar con jsdom en Fase 8).
11. **Calibración del motor de sentimiento (Fase 7)**: `lib/config.py` define `SENTIMENT_CONFIDENCE_THRESHOLD = 0.4`. Cuando la confianza del softmax cae bajo el umbral Y no hay `es_evento_negativo`, el sentimiento se fuerza a 'neutro'. Ajustar este valor requiere recalibrar contra datos reales y regenerar JSONs en CI.
