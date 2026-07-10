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
- **`lib/`** contiene **13 modulos activos** (motor legacy eliminado en v3.2.0):
  - `config.py` — mapeos de columnas y catalogos de negocio.
  - `metrics.py` — `calc_nps`, `calc_csat` (funciones puras).
  - `io_helper.py` — I/O seguro, hash para idempotencia, `enmascarar_pii` (redaccion PII).
  - `csv_exporter.py` — exportacion de CSVs/ZIPs con proteccion formula injection y redaccion PII.
  - `dashboard_builder.py` — ensamblado de `dashboard_data.json`.
  - `periodos_updater.py` — actualizacion de `periodos.json`.
  - `ia_cualitativo.py` — motor IA con DeepSeek (unico motor desde v3.2.0, requiere `DEEPSEEK_API_KEY`).
  - `prompts_cualitativo.py` — prompts Bardin/Braun&Clarke para DeepSeek. Versionados con `PROMPT_VERSION`.
  - `ia_cache.py` — cache persistente con contador de hits thread-safe.
  - `ia_client.py` — cliente HTTP DeepSeek (urllib stdlib) con reintentos.
  - `ia_filtro_ruido.py` — pre-filtro de comentarios ruidosos (15 criterios regex).
  - `ia_validacion.py` — validacion de respuestas DeepSeek + redaccion PII post-LLM.
  - `insights_generator.py` — sintesis determinista de insights (sin LLM).
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

- introducir nuevos `print()` de depuracion en produccion

## Reglas Frontend

- Mantener Vanilla JS e IIFE con APIs `window.Survey*`.
- No introducir frameworks frontend ni dependencias runtime sin decision explicita.
- Sanitizar contenido externo antes de usar `innerHTML` (usar `SurveySanitizer.escapeHTML` o `sanitizeHTML`).
- Mantener compatibilidad con GitHub Pages y navegadores modernos.
- No usar inline event handlers (`onmousemove`, `onmouseleave`, etc.) — usar `addEventListener`.
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
| `zoho-survey/scripts/validate_generated_json.py` | Validacion de contratos. Cambios deben sincronizarse con schemas. |
| `zoho-survey/scripts/schemas/*.schema.json` | Fuente formal de tipos. Cambios deben propagarse a ETL, validador y CONTRACTS.md. |
| `zoho-survey/template/index.html` | IDs HTML son contratos publicos con `dashboard.js` y `filter-controller.js`. |
| `zoho-survey/shared/js/dashboard.js` | Orquestador monolitico (1249 lineas). |
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
3. **Motor legacy eliminado** (v3.2.0): los modulos `nlp.py`, `segmentacion_nps.py`, `aspect_extraction.py`, `sentiment_engine.py` fueron eliminados. `enmascarar_pii` se reubico a `io_helper.py`. `DEEPSEEK_API_KEY` es obligatoria.
4. **`lib/config.py` constantes legacy**: ~~`TOPICOS` y `STOPWORDS` no se usan en modulos activos.~~ **ELIMINADO**.
5. **Sin spaCy desde v3.2.0**: el motor legacy (spaCy + sentence-transformers) fue eliminado. `requirements.txt` ya no incluye `spacy`, `sentence-transformers`, ni `scikit-learn`.
6. **`fragmentos_nps.json` y `dataset_cualitativo.json` no tienen schema formal**: son archivos intermedios del ETL, no contratos publicos. El frontend no los consume.
7. **Trabajo sin commitear**: el repositorio puede tener cambios pendientes. Revisar `git status` antes de modificar.
8. **`periodos.json` por nivel**: debe tener exactamente un item con `isNew: true`. El validador falla si no se cumple.
9. **Tests Python no ejecutados en CI**: ~~los tests en `scripts/tests/` solo corren manualmente.~~ **Fase 6**: workflow `tests.yml` creado, ejecuta unittest + JS tests + sintaxis en cada PR.
10. **Tests JS**: Fase 6: suite reparada, 91/91 tests pasan (59 browser + 32 jsdom). Cobertura: ~6/13 módulos (constants, formatters, sanitizer, dom-helpers, tooltip, sentiment-view tienen tests directos). Pendiente ampliar cobertura.
11. **Calibración del motor de sentimiento (Fase 7)**: `lib/config.py` define `SENTIMENT_CONFIDENCE_THRESHOLD = 0.4`. Cuando la confianza del softmax cae bajo el umbral Y no hay `es_evento_negativo`, el sentimiento se fuerza a 'neutro'. Ajustar este valor requiere recalibrar contra datos reales y regenerar JSONs en CI.
