# shared

Componentes reutilizables compartidos entre todos los modulos de encuesta del sistema. Contiene estilos, JavaScript e imagenes utilizados por los dashboards de todos los niveles academicos.

## Purpose

Proveer la capa de presentacion base (CSS, JS, imagenes) que consume cada instancia de dashboard de periodo, garantizando consistencia visual y comportamental sin duplicacion de codigo.

## Architecture Role

Capa de presentacion base. Proporciona el sistema de diseno (CSS), la logica de visualizacion (JS) y los assets graficos que consumen las paginas de periodo individuales.

## Key Files

| File | Lines | Responsibility |
| --- | --- | --- |
| `css/tokens.css` | 118 | Design tokens: 13 colores institucionales, tipografia (Roboto), z-index (8 niveles), espaciados (9), radios (8), sombras (3). |
| `css/reset.css` | 69 | Reset universal + utilidades base (`.skip-link`, `.sr-only`, `.text-center`, `.mt-4`, `.software-italic`). |
| `css/layout.css` | 174 | Sticky header, nav links, progress bar, main-content grid, footer. |
| `css/components.css` | 864 | KPI cards, distribution bars, filter system, custom select/multiselect, bar charts, radar SVG, tables (sticky header), heatmap, tooltip. |
| `css/sections.css` | 244 | Selectores especificos de tabla + 3 media queries (1100/768/480px). |
| `css/dashboard.css` | 16 | Entry point con `@import` de las 5 capas modulares. |
| `css/loader.css` | 636 | Tema oscuro institucional del loader: splash, topbar, survey-tabs, period-bar, pills, overlay, frame-wrap, custom select dark, overflow "MAS". |
| `js/loader.js` | 420 | Navegador de encuestas: fetch `periodos.json`, pills/select, control del iframe, sistema de overflow MAS con ResizeObserver + throttle. |
| `js/dashboard.js` | 1015 | Orquestador principal del dashboard SPA. 4 secciones, filtros en cascada, rendering SVG, tooltips, KPIs, tablas. |
| `js/config/constants.js` | 58 | `window.SURVEY_CONFIG`: metas, carreras/facultades 12 ciclos, SAT_KEYS, umbrales visuales, configuracion radar. |
| `js/utils/formatters.js` | 83 | `window.SurveyFormatters`: formateo es-PE (integer, decimal, percent, date, ciclo text, dimension name). |
| `js/utils/metrics.js` | ~60 | `window.SurveyMetrics`: `calcBoxScore`, `calcPromedioPonderado`, `deriveT2B`, `derivePonderado`. Gemelo JS de `lib/metrics.py`. |
| `js/utils/sanitizer.js` | 55 | `window.SurveySanitizer`: `escapeHTML`, `sanitizeHTML` (whitelist: `br, strong, em, i, span`). |
| `js/utils/dom-helpers.js` | 95 | `window.SurveyDOMHelpers`: `$`, `esEstudiosGen`, `sumKeys`, `getSelectedValues`, `setSelectedValues`, `formatMultiselectLabel`, placeholders. |
| `js/components/tooltip.js` | 97 | `window.SurveyTooltip`: `show`, `hide`, `move`, `bindToSegments`. |
| `js/components/progress-bar.js` | 77 | `window.SurveyProgressBar.init(options)`: barra de scroll con IntersectionObserver. |
| `js/components/custom-select.js` | 157 | `window.SurveyCustomSelect.create(sel, onChange)`: selectores desplegables personalizados con ARIA. |
| `js/components/multiselect.js` | 161 | `window.SurveyMultiselect.create(selCic, onChange, defaultLabel, itemName)`: listas de seleccion multiple. |
| `js/components/filter-controller.js` | 181 | `window.SurveyFilterController.{setup, esEstudiosGen, getCiclosForFiltro}`: filtros en cascada. |
| `js/components/radar-chart.js` | 331 | `window.SurveyRadarChart.{render, dimensionAplica}`: radar SVG nativo con animaciones SMIL. |
| `js/components/sentiment-view.js` | 888 | `window.SurveySentimentView.{init, updateMacro, updateAspectos, updateNpsCarrera, updateDetalle, applyExploradorFilters}`: visual cualitativo v3.0.0. |
| `img/` | — | `logo-horizontal.png`, `logo-vertical.png`, `logo-isotipo.png`, `favicon.png`, `todo-posible.webp`. |

## Data Flow

```
loader.js → fetch periodos.json → render pills/select → set iframe.src
                                                            ↓
                                          dashboard.js → fetch 9 JSON files from ./json/
                                                            ↓
                                          render 4 secciones (Ejecutivo, Operativo, Detallado, Cualitativo)
```

## Design Tokens (CSS)

Variables CSS en `tokens.css` (`:root`):

- Colores institucionales: `--ulima-orange: #FF5117`, `--ulima-red: #FF0000`, escala de grises `--gray-50` a `--gray-900`.
- Estados semanticos: `--success-pastel/text`, `--warning-pastel/text`, `--danger-pastel/text`.
- Tipografia: `--font-family-primary: 'Roboto'`, pesos 300/400/500/700/900.
- Accesibilidad: `--focus-outline`, `--focus-outline-offset`.
- Z-index: 8 niveles (`--z-base: 1` a `--z-splash: 99999`).
- Espaciados: 9 escalas (`--space-xs: 4px` a `--space-5xl: 68px`).
- Radios: 8 niveles (`--radius-xs: 2px` a `--radius-full: 9999px`).
- Splash bg: `--splash-bg: #F37021`.

## APIs globales (`window.Survey*`)

| Modulo | API publica | Dependencias internas |
| --- | --- | --- |
| `constants.js` | `window.SURVEY_CONFIG` (objeto plano) | Ninguna. |
| `formatters.js` | `window.SurveyFormatters.{formatInteger, formatDecimal, formatPercent, formatPctSimple, formatPctDecimal, formatDate, formatCicloText, cortarTexto, formatDimensionName, formatDimensionNameSVG, formatDimensionNameForAttr}` | Ninguna. Funciones puras. |
| `sanitizer.js` | `window.SurveySanitizer.{escapeHTML, sanitizeHTML}` | Ninguna. |
| `dom-helpers.js` | `window.SurveyDOMHelpers.{$, esEstudiosGen, sumKeys, getSelectedValues, setSelectedValues, getPlaceholderText, formatCustomLabel, formatMultiselectLabel}` | Ninguna. Helpers de negocio acceden a `SURVEY_CONFIG` internamente. |
| `tooltip.js` | `window.SurveyTooltip.{show, hide, move, bindToSegments}` | `SurveySanitizer` (opcional, fallback a escape manual). |
| `progress-bar.js` | `window.SurveyProgressBar.init(options)` | Ninguna. |
| `custom-select.js` | `window.SurveyCustomSelect.create(sel, onChange)` → `{update, close, button, wrapper}` | `SurveyDOMHelpers` (requerida). |
| `multiselect.js` | `window.SurveyMultiselect.create(selCic, onChange, defaultLabel, itemName)` → wrapper HTMLElement con `.update()` | `SurveyDOMHelpers` (requerida). |
| `filter-controller.js` | `window.SurveyFilterController.{setup, esEstudiosGen, getCiclosForFiltro}` | `SurveyCustomSelect`, `SurveyMultiselect`, `SurveyDOMHelpers`. |
| `radar-chart.js` | `window.SurveyRadarChart.{render, dimensionAplica}` | `SurveyFormatters`, `SurveySanitizer`, `SurveyMultiselect`, `SurveyDOMHelpers`, `SURVEY_CONFIG`, `SurveyTooltip` (via `addEventListener`). |
| `sentiment-view.js` | `window.SurveySentimentView.{init, updateMacro, updateAspectos, updateNpsCarrera, updateDetalle, applyExploradorFilters, renderInsightsIA}` | `SurveyFormatters`, `SurveyDOMHelpers`, `SurveySanitizer`, `SurveyTooltip`, `SurveyCustomSelect`, `SURVEY_CONFIG`. |
| `dashboard.js` | (privado, ejecuta `init()` automaticamente) | Todos los anteriores. |
| `loader.js` | `window.selectSurvey(id)`, `window.loadPeriod(id)` | `SurveyCustomSelect` (opcional). |

## Execution Flow

1. `zoho-survey/index.html` loads → `loader.js` executes (IIFE).
2. `loader.js` inicializa el sistema de overflow MAS, restaura seleccion de `localStorage` (`ulima_selected_survey`, `ulima_selected_period_<survey_id>`).
3. `loader.js` fetchea `periodos.json` de la encuesta persistida → renderiza pills (desktop) y `<select>` (mobile).
4. Usuario (o auto-seleccion) elige periodo → `loadPeriod()` setea `iframe.src` a `{period}/index.html`.
5. Iframe carga → `dashboard.js` ejecuta en `DOMContentLoaded`.
6. `dashboard.js` fetchea 9 JSON files desde `./json/` (3 criticos via `Promise.all`, 6 opcionales con tolerancia a fallos).
7. Registra 22 referencias DOM en un objeto precargado.
8. Inicializa 5 grupos de filtros en cascada via `SurveyFilterController.setup()`.
9. Configura la barra de progreso via `SurveyProgressBar.init()`.
10. Renderiza 4 secciones en orden: Ejecutivo → Operativo → Detallado → Cualitativo.

## Order of Script Loading (Critical)

En `template/index.html` y todos los `index.html` de periodo, los scripts deben cargarse en este orden:

```html
<!-- 1. Config primero -->
<script src=".../config/constants.js"></script>
<!-- 2. Utils (sin dependencias internas) -->
<script src=".../utils/formatters.js"></script>
<script src=".../utils/metrics.js"></script>
<script src=".../utils/sanitizer.js"></script>
<script src=".../utils/dom-helpers.js"></script>
<!-- 3. Components simples -->
<script src=".../components/tooltip.js"></script>
<script src=".../components/progress-bar.js"></script>
<!-- 4. Components con dependencias -->
<script src=".../components/custom-select.js"></script>
<script src=".../components/multiselect.js"></script>
<script src=".../components/filter-controller.js"></script>
<script src=".../components/radar-chart.js"></script>
<script src=".../components/sentiment-view.js"></script>
<!-- 5. Orquestador al final -->
<script src=".../dashboard.js"></script>
```

> **Orden de carga:** 13 scripts en total (1 config + 4 utils + 2 components simples + 5 components con dependencias + 1 orquestador).

> **Advertencia critica:** `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` y `multiselect.js`. Sin esto, `window.SurveyDOMHelpers` es undefined al evaluar el IIFE de custom-select y cualquier interaccion falla con `TypeError`.

En el `index.html` del loader (zoho-survey/index.html), el orden es:
1. `utils/dom-helpers.js` → 2. `components/custom-select.js` → 3. `loader.js`.

## Configuration

Constantes en `config/constants.js` (`window.SURVEY_CONFIG`):

- `META_NPS = 50` — umbral target NPS.
- `META_CSAT = 93` — umbral target CSAT.
- `META_EMPLEABILIDAD = 85` — umbral target empleabilidad.
- `CARRERAS_12_CICLOS = ['Derecho', 'Psicología']` — carreras con 12 ciclos.
- `FACULTADES_12_CICLOS` — facultades con 12 ciclos.
- `CICLOS_ESTUDIOS_GENERALES = ['1° Ciclo', '2° Ciclo']` — ciclos limitados para Estudios Generales.
- `SAT_KEYS` — 5 niveles Zoho Survey (`Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho`).
- Umbrales visuales: `>= META_CSAT (93) → high`, `>= 80 → medium`, `< 80 → low`.
- Visibilidad: `>= 50% → critico`, `25-50% → moderado`.

`dashboard.js` mantiene constantes duplicadas con fallback `??` a `SURVEY_CONFIG` por compatibilidad backward.

## Technical Debt

- **6 de 14 modulos JS sin tests**: tienen cobertura `constants.js`, `formatters.js`, `metrics.js`, `sanitizer.js`, `dom-helpers.js`, `sentiment-view.js` (parcial), `filter-controller.js` y `loader.js` (142 tests en 9 archivos, ampliado desde v3.1.0). Pendientes: `tooltip.js`, `progress-bar.js`, `custom-select.js`, `multiselect.js`, `radar-chart.js`, `dashboard.js`.
- **No hay sistema de modulos**: usa IIFE + closures en lugar de ES modules o bundler. El orden de carga es critico.
- **Custom select dropdowns**: implementacion manual (~200 lineas entre custom-select.js y multiselect.js). Posible fuente de bugs cross-browser.
- **`window.cache`** (investigado): se revisó la referencia reportada en `sentiment-view.js` y se confirmó que **no existe tal referencia muerta**. Lo que sí existe es un parámetro muerto (`cache`) en `renderMetricCards`, ya documentado en su firma. `cache` es una variable local privada en el IIFE de `dashboard.js` (no expuesta en `window`).
- **CSS muerto**: ~50 lineas en `components.css` (`.doughnut-segment`, `.category-row`, `.cualitativo-layout`) no referenciadas en JS actual.
- **Dashboard sin tests**: `dashboard.js` (1015 líneas) y `sentiment-view.js` (888 líneas) no tienen tests unitarios.

## Improvement Opportunities

- Migrar a ES modules (`<script type="module">`) para eliminar dependencia de orden de carga.
- Implementar carga lazy de JSON por seccion.

## AI Agent Notes

- Los **IDs HTML son contratos publicos** con `dashboard.js` y `filter-controller.js`. No renombrar sin actualizar simultaneamente el JS.
- IDs criticos del template: `kpi-csat-value/bar/meta`, `kpi-nps-value/bar/meta`, `csat-bar`, `nps-bar`, `radar-chart`, `filter-facultad-{top3,radar,preguntas,detalle,visibilidad}`, `filter-carrera-{...}`, `filter-ciclo-{...}`, `reset-{...}`, `tabla-explorador-comentarios`, `intensidad-positivos-container`, etc.
- Las funciones globales son `window.SurveyTooltip.show` / `window.SurveyTooltip.hide` (NO `window.showTooltip` / `window.hideTooltip` como decia la documentacion anterior).
- `dashboard.js` espera que los `<select>` tengan atributo `data-multiselect="true"` para activar el dropdown multiselect.
- La seccion cualitativa usa `id="cualitativo"` y `id="cualitativo-heading"` como IDs tecnicos aunque la etiqueta visible sea "Cualitativo" y "ANALISIS CUALITATIVO".
- `#progress-fill` es requerido para la barra de progreso de scroll.
- No cambiar el nombre de las funciones `window.selectSurvey` y `window.loadPeriod` — son invocadas desde `loader.js` vía `addEventListener` (no hay inline handlers en el HTML).
- `showTooltip` y `hideTooltip` NO existen como funciones globales; usar `window.SurveyTooltip.show(event, content, raw)` y `window.SurveyTooltip.hide()`.
