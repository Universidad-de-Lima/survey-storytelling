# Arquitectura Del Sistema De Encuestas De Satisfaccion

Este documento es la fuente canonica para entender la estructura tecnica de `survey-storytelling`. Los contratos de datos viven en `CONTRACTS.md` y formalmente en `zoho-survey/scripts/schemas/*.schema.json`; las reglas para agentes viven en `AGENTS.md`.

## Mapa De Componentes

```mermaid
graph TD
    CSV[CSV de Zoho Survey] --> ETL[zoho-survey/scripts/build_json.py]
    ETL --> |genera| JSON[Contratos JSON por periodo]
    ETL --> |valida contra| SCHEMA[scripts/schemas/*.schema.json Draft-07]
    SCHEMA --> |cargado por| VAL[validate_generated_json.py]
    JSON --> DASH[zoho-survey/shared/js/dashboard.js]
    LOADER[zoho-survey/index.html + loader.js] --> |iframe| DASH
    CSS[zoho-survey/shared/css] --> HTML[index.html de periodo]
    DASH --> HTML
    CSV --> |hash| CACHE[.csv_hash<br/>detección de cambios]

    subgraph ETL Cualitativo IA [Motor IA — DeepSeek (unico motor desde v3.2.0)]
        IA[lib/ia_cualitativo.py] --> |cache| IACACHE[ia_cache.json]
        IAPROMPT[lib/prompts_cualitativo.py] --> IA
        IA --> |genera| DC2[dataset_cualitativo.json]
        DC2 --> ST2[sentimiento.json v3.0]
        IAGEN[lib/insights_generator.py] --> |síntesis determinista| ST2
    end
    ETL --> |DEEPSEEK_API_KEY obligatoria| IA
```

## Estructura De Directorios

```text
survey-storytelling/
├── .github/workflows/       # Workflows de CI/CD (build_zoho_survey.yml, validate-survey-json.yml, tests.yml).
├── data/                    # CSVs fuente exportados desde Zoho Survey.
├── docs/                    # Documentacion y guias del proyecto.
├── tests/                   # Mini-framework de pruebas unitarias en navegador.
├── zoho-survey/             # Aplicacion estatica principal.
│   ├── index.html           # Loader publicado en GitHub Pages.
│   ├── underconstruction.html # Pagina de mantenimiento.
│   ├── shared/              # Recursos compartidos (CSS, JS, imagenes).
│   │   ├── css/             # Capas CSS (tokens, reset, layout, components, sections, dashboard, loader).
│   │   └── js/              # Modulos JS IIFE expuestos en window.Survey*.
│   ├── template/            # Plantilla HTML para nuevos periodos de encuesta.
│   ├── scripts/             # ETL en Python, validacion de contratos y schemas JSON.
│   │   ├── lib/             # Biblioteca modularizada del ETL (10 modulos:
│   │   │                    # config, metrics, nlp, io_helper, segmentacion_nps,
│   │   │                    # aspect_extraction, sentiment_engine,
│   │   │                    # ia_cualitativo, prompts_cualitativo, insights_generator).
│   │   ├── schemas/         # JSON Schemas Draft-07 (7 schemas formales).
│   │   ├── config/          # Configuracion estatica (stop_aspectos.json, alias_aspectos.json).
│   │   └── tests/           # Tests Python (10 modulos incluyendo test_html_contract, test_alias_aspectos).
│   └── students/            # Dashboards y JSONs generados por nivel y periodo.
├── AGENTS.md                # Reglas y principios operativos para IA.
├── ARCHITECTURE.md          # Arquitectura tecnica global (este documento).
└── CONTRACTS.md             # Contratos CSV/JSON e invariantes de datos.
```

Para mayor detalle de responsabilidades:

| Ruta | Responsabilidad |
| --- | --- |
| `data/` | CSVs fuente exportados desde Zoho Survey. |
| `zoho-survey/scripts/` | Scripts ETL, validacion de contratos y schemas de datos. |
| `zoho-survey/scripts/lib/` | Biblioteca de utilidades modularizadas del ETL. |
| `zoho-survey/scripts/schemas/` | JSON Schemas Draft-07 (fuente formal de tipos). |
| `zoho-survey/shared/js/` | Modulos compartidos del loader y dashboard (IIFE). |
| `zoho-survey/shared/css/` | Capas CSS modulares e imports del dashboard. |
| `zoho-survey/template/` | Template base HTML para la generacion automatica de periodos. |
| `zoho-survey/students/` | Dashboards y datos JSON generados de estudiantes. |
| `tests/` | Infraestructura y tests unitarios de navegador. |
| `.github/workflows/` | Automatizacion de build, validacion y deploy en GitHub Pages. |

## Pipeline De Datos

`zoho-survey/scripts/build_json.py` transforma CSVs en contratos JSON estaticos. Delega en los siguientes submodulos en `scripts/lib/`:

### Modulos ETL

| Modulo | Lineas | Responsabilidad | Estado |
| --- | --- | --- | --- |
| `lib/config.py` | 352 | Mapeos de columnas, catalogos de negocio y umbral de confianza. | Activo. |
| `lib/metrics.py` | 57 | Funciones puras de calculo de NPS (`calc_nps`) y CSAT (`calc_csat`). | Activo. |
| `lib/io_helper.py` | ~160 | I/O seguro con encodings alternativos, formateo de fechas, hash para idempotencia, y redaccion PII (`enmascarar_pii`). | Activo. |
| `lib/ia_cualitativo.py` | ~415 | Motor de analisis cualitativo basado en DeepSeek. **Unico motor desde v3.2.0** (motor legacy eliminado). CacheManager con contador de hits thread-safe. | Activo (requiere `DEEPSEEK_API_KEY` obligatoria). |
| `lib/prompts_cualitativo.py` | 561 | Prompts exactos para DeepSeek (system + user). Fuente de verdad de los prompts usados tanto en el ETL como en el playground Next.js. Versionado con `PROMPT_VERSION` para invalidacion automatica del cache IA. | Activo (Fase IA). |
| `lib/insights_generator.py` | 262 | Generador de insights deterministas (sin LLM). Produce `insights_ia.global` y `insights_ia.por_categoria_padre` a partir de datos ya procesados. | Activo. |
| `lib/csv_exporter.py` | ~155 | Exportacion de CSVs y ZIPs con proteccion formula injection y redaccion PII. ZIPs se guardan en `exports/` (no desplegados en Pages). | Activo. |
| `lib/dashboard_builder.py` | 57 | Ensamblado de `dashboard_data.json` desde metricas pre-calculadas. | Activo. |
| `lib/periodos_updater.py` | 58 | Actualizacion de `periodos.json` por nivel, marcando `isNew: true` en el mas reciente. | Activo. |
| `lib/ia_cache.py` | ~130 | Cache persistente JSON con clave SHA-256(comentario + contexto). Contador de hits thread-safe (fix CC-02). | Activo. |
| `lib/ia_client.py` | 187 | Cliente HTTP DeepSeek (urllib stdlib) con reintentos, backoff exponencial y rate limiting. | Activo. |
| `lib/ia_filtro_ruido.py` | 147 | Pre-filtro de comentarios ruidosos (15 criterios regex) antes de llamar a DeepSeek. | Activo. |
| `lib/ia_validacion.py` | ~135 | Validacion y correccion de respuestas DeepSeek. Redaccion PII post-LLM (SEG-01). | Activo. |

**Modulos eliminados en v3.2.0** (motor legacy): `lib/nlp.py`, `lib/segmentacion_nps.py`, `lib/aspect_extraction.py`, `lib/sentiment_engine.py`, `lib/sentimiento_builder.py`.

### Flujo cualitativo (v3.2.0) — Motor unico IA

Desde v3.2.0, el ETL usa un unico motor cualitativo (DeepSeek IA). El motor legacy
(spaCy + sentence-transformers) fue eliminado. `DEEPSEEK_API_KEY` es obligatoria.

**Motor IA (DeepSeek)** — unico motor desde v3.2.0:
```
Comentario NPS (CSV)
    |  una única llamada a DeepSeek (15 workers concurrentes, rate limit 60 RPM)
    v
ia_cualitativo.py → DeepSeek API
    |  ejecuta 5 tareas en conjunto con coherencia de contexto:
    |  1. Segmentación en Meaning Units (Bardin, 2011)
    |  2. Clasificación de sentimiento con reglas de sesgo por contexto NPS
    |  3. Asignación de intensidad (1-5)
    |  4. Clasificación contra taxonomía oficial (Braun & Clarke, 2006)
    |  5. Triangulación con calificación CSAT por dimensión (cross-reference)
    v
dataset_cualitativo.json + ia_cache.json (hash de comentario + contexto)
    |
    v
sentimiento.json v3.0 + insights_ia (vía insights_generator.py)
```

### Optimización: detección de cambios por hash

`build_json.py` implementa una optimización de skip: antes de procesar un CSV, calcula su hash SHA256 y lo compara con `.csv_hash` (guardado en el directorio de salida del periodo). Si el CSV no cambió desde el último build Y todos los JSONs ya existen, se salta el reprocesamiento completo. Esto ahorra tiempo de CPU, llamadas a DeepSeek (costos), y reescritura de archivos idénticos.

```
Comentario NPS (CSV)
    |
    v
sanitizar_comentario (lib/nlp.py)
    |  valida calidad: vacio, <3 chars, spam de letras, noise patterns
    v
fragmentar_comentario_nps (lib/segmentacion_nps.py)
    |  - normalizar_texto (slang, muletillas)
    |  - proteger_entidades (nombres de facultades, pabellones)
    |  - extraer_unidades_opinion (spaCy: conj dependencies, 4 heuristicas de corte)
    |  - _distribuir_contexto_compartido (Right-Node Raising, Left-Node Raising)
    |  - _limpiar_unidad (quita muletillas, ruido)
    v
fragmentos_nps.json  (v1.0, archivo intermedio)
    |  por cada fragmento:
    v
procesar_opinion_unit (lib/aspect_extraction.py)
    |  - extraer_aspecto_detectado: noun chunks via spaCy
    |  - normalizar_aspecto: cascada alias exacto -> embedding >0.55 -> embedding_fallback >0.45
    |    Retorna: aspecto_normalizado, categoria_padre, metodo
    v
analizar_sentimiento_intensidad (lib/sentiment_engine.py)
    |  - codificar texto (SentenceTransformer paraphrase-multilingual-MiniLM-L12-v2)
    |  - cosine_similarity con 3 anclas (positivo, negativo, neutro)
    |  - softmax con temperatura 10
    |  - calcular_intensidad: intensificadores, atenuantes, severidad, impacto (regex lexicos)
    |  - ajustes: si es_evento_negativo -> fuerza negativo; neutro limita intensidad a max 2
    v
dataset_cualitativo.json  (v1.0, archivo intermedio)
    |  transformacion UI:
    |  - generar comentarios_detallados con categoria, categoria_padre, aspecto_normalizado
    |  - generar topicos_globales (conteo por aspecto_normalizado)
    |  - generar por_carrera, por_ciclo
    |  - generar dist_sent, dist_int (umbrales 4.0 y 2.5)
    |  - generar cat_parent_insights (insights narrativos locales hardcodeados)
    v
sentimiento.json v3.0  (consumido por frontend)
```

### Outputs generados por periodo

El ETL genera 11 archivos por periodo:

1. `dashboard_data.json` (v2.0) — KPIs ejecutivos, hallazgos, distribuciones NPS/CSAT.
2. `dimensiones.json` — agregados por facultad/carrera/ciclo/categoria/dimension.
3. `ids.json` — conteos por facultad/carrera/ciclo.
4. `nps_carrera.json` (legacy) — NPS por carrera.
5. `nps_ciclo_carrera.json` — NPS por carrera y ciclo.
6. `csat_carrera.json` (legacy) — CSAT por carrera.
7. `csat_ciclo_carrera.json` — CSAT por carrera y ciclo.
8. `filtros.json` (v2.0) — opciones de filtros en cascada.
9. `sentimiento.json` (v3.0) — analisis cualitativo completo (consumido por frontend).
10. `fragmentos_nps.json` (intermedio) — Meaning Units extraidas (no consumido por frontend).
11. `dataset_cualitativo.json` (intermedio) — dataset detallado de fragmentos clasificados (no consumido por frontend).

Adicionalmente, por nivel se actualiza `periodos.json` y por periodo se copia el `template/index.html` con `{{SHARED_PATH}}` reemplazado.

### Responsabilidades del ETL

- Normalizar columnas de Zoho Survey a nombres internos definidos en `lib/config.py`.
- Calcular agregados NPS, CSAT y empleabilidad cuando corresponde.
- Generar datos por facultad, carrera, ciclo y dimension.
- Fragmentar comentarios NPS en Meaning Units con spaCy.
- Extraer aspectos y clasificar sentimiento con SentenceTransformer.
- Copiar el template del periodo y actualizar `periodos.json`.
- Mantener idempotencia: correr el script dos veces con la misma entrada debe producir el mismo resultado (con caveat: si el CSV no tiene fechas validas, se usa `pd.Timestamp.now()` como fallback, lo que rompe idempotencia en ese edge case).

Los esquemas, archivos requeridos e invariantes estan definidos en `CONTRACTS.md` y formalmente en `zoho-survey/scripts/schemas/*.schema.json`.

## Validacion

`zoho-survey/scripts/validate_generated_json.py` valida los JSONs generados aplicando:

1. **JSON Schema Draft-07** (fuente formal de tipos): carga cada schema desde `scripts/schemas/` y ejecuta `Draft7Validator.iter_errors()`.
2. **Invariantes de negocio cruzadas** (no expresables en JSON Schema): suma total > 0, `facultad_carrera` cubre todas las facultades, al menos una fila con `total > 0` en `dimensiones.json`, exactamente un `isNew: true` en `periodos.json`.
3. **Validacion de HTML del periodo**: verifica que cada `index.html` contenga los fragmentos requeridos para la seccion cualitativa.

El validador NO debe ser mas permisivo que el schema. Si el schema rechaza, el validador rechaza.

## Frontend

La aplicacion es una SPA estatica en Vanilla JS, sin backend ni dependencias runtime.

### Loader

- `zoho-survey/index.html`: entrada publicada en GitHub Pages.
- `zoho-survey/shared/js/loader.js`: detecta tipos de encuesta, niveles y periodos disponibles via `periodos.json`. Implementa el sistema de overflow "MAS" con ResizeObserver + throttle, manejo de foco y ARIA.
- Carga cada dashboard de periodo en iframe.

### Dashboard

- `zoho-survey/template/index.html`: estructura HTML base de cada periodo.
- `zoho-survey/shared/js/dashboard.js`: orquestador principal (1.015 lineas).
- `zoho-survey/shared/js/config/constants.js`: metas, ciclos y constantes compartidas.
- `zoho-survey/shared/js/utils/formatters.js`: funciones de formateo (es-PE).
- `zoho-survey/shared/js/utils/sanitizer.js`: `escapeHTML` y `sanitizeHTML` (whitelist: `br, strong, em, i, span`).
- `zoho-survey/shared/js/utils/dom-helpers.js`: utilidades DOM compartidas.
- `zoho-survey/shared/js/components/`:
  - `tooltip.js`: Globos interactivos flotantes.
  - `progress-bar.js`: Barra superior de scroll de pagina.
  - `custom-select.js`: Selectores desplegables personalizados.
  - `multiselect.js`: Listas de seleccion multiple.
  - `filter-controller.js`: Coordinacion de filtros en cascada (Facultad/Carrera/Ciclo).
  - `radar-chart.js`: Grafico radar dinamico en SVG nativo (sin librerias externas).
  - `sentiment-view.js`: Renders cualitativos y comentarios NPS (888 lineas, v3.0.0).

Los modulos usan IIFE y exponen APIs globales `window.Survey*`. No usan ES Modules.

### Orden de carga de scripts

El orden de carga en `template/index.html` (12 scripts) es critico y debe respetarse:

1. `config/constants.js` → 2. `utils/formatters.js` → 3. `utils/sanitizer.js` → 4. `utils/dom-helpers.js` → 5. `components/tooltip.js` → 6. `components/progress-bar.js` → 7. `components/custom-select.js` → 8. `components/multiselect.js` → 9. `components/filter-controller.js` → 10. `components/radar-chart.js` → 11. `components/sentiment-view.js` → 12. `dashboard.js`.

> **Advertencia:** `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` para evitar errores `TypeError: window.SurveyDomHelpers is undefined` que bloqueen el loader del portal. El `index.html` del loader carga 3 scripts en orden: `dom-helpers.js` → `custom-select.js` → `loader.js`.

## CSS

`zoho-survey/shared/css/` contiene 7 capas:

- `tokens.css`: design tokens y variables CSS (colores institucionales, tipografia, espaciados, z-index, radios, sombras).
- `reset.css`: reset y utilidades base (`.skip-link`, `.sr-only`).
- `layout.css`: header, navegacion, grid y footer (174 lineas).
- `components.css`: KPIs, filtros, barras, tooltips y tablas (864 lineas, la capa mas grande).
- `sections.css`: secciones, responsive y ajustes visuales (244 lineas).
- `dashboard.css`: entry point con `@import` para la capa dashboard (16 lineas).
- `loader.css`: estilos especificos del navegador de encuestas (636 lineas, tema oscuro institucional).

## Patrones Arquitectonicos

- **Datos precomputados**: el frontend consume JSON, no recalcula agregados que pertenecen al ETL.
- **Separacion de datos y vista**: los JSON no deben depender del layout visual.
- **Delegacion progresiva**: `dashboard.js` delega en modulos compartidos cuando existen; mantiene fallback inline para KPIs, distribuciones y tablas detalladas.
- **Compatibilidad backward**: los contratos legacy se conservan cuando todavia hay consumidores (ej. `nps_carrera.json`/`csat_carrera.json` como fallback para encuestas sin ciclo).
- **Degradacion controlada**: errores de carga JSON opcionales se tratan con `console.warn` sin romper toda la pagina. Endpoints criticos (`dashboard_data`, `filtros`, `dimensiones`) fallan rápido via `Promise.all`.
- **Resolucion de dependencias en runtime**: los modulos IIFE referencian `window.Survey*` al momento de uso, no al de carga. Esto permite que el dashboard funcione aunque falten modulos opcionales.

## Seguridad

- Cualquier contenido externo usado en HTML debe pasar por `escapeHTML()` o `sanitizeHTML()`.
- `sanitizeHTML()` permite solo una lista reducida de etiquetas necesarias para tooltips y textos enriquecidos (`br, strong, em, i, span`).
- No introducir dependencias runtime para sanitizacion sin justificar el costo operacional.


## Deuda Tecnica Vigente

- La logica de ciclos esta externalizada en `SURVEY_CONFIG`, pero todavia no es dinamica por periodo.
- `nps_carrera.json` y `csat_carrera.json` son legacy; el frontend los usa como fallback para encuestas sin ciclo (`has_ciclo=false`, ej. Graduados).
- `posgraduate/` existe como placeholder sin datos procesados.
- El template `zoho-survey/template/index.html` no tiene version de contrato propia.

## Convenciones

- **JavaScript**: camelCase para variables y funciones; APIs compartidas bajo `window.Survey*`.
- **CSS**: kebab-case para clases e IDs; usar tokens antes que valores hardcodeados.
- **Python**: snake_case para funciones y variables; constantes en UPPER_SNAKE_CASE.
- **JSON**: claves NPS en minúsculas (`promotores`, `pasivos`, `detractores`); claves CSAT capitalizadas (`Totalmente satisfecho`, etc.) por provenir del catálogo Zoho.
- **Compatibilidad**: GitHub Pages, navegadores modernos y Python para ETL.
