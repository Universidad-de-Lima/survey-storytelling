# shared/js

Módulos JavaScript del dashboard. Implementan la lógica de navegación entre periodos y la visualización interactiva de datos mediante manipulación directa del DOM (Vanilla JS, ES6+).

## Architecture Role

Capa de presentación lógica. No hay framework, bundler ni sistema de módulos. Ambos archivos son IIFEs que se ejecutan al cargarse y dependen del orden de inclusión en el HTML.

## Key Files

### `loader.js` (~200 lines)

**Purpose**: Navegador de periodos académicos. Controla el iframe que contiene cada dashboard de periodo.

**Inputs**: `periodos.json` (vía fetch), clicks del usuario en pills/select

**Outputs**: Setea `iframe.src` al URL del periodo seleccionado, controla overlay de carga

**Key Functions**:
| Function | Visibility | Responsibility |
|----------|-----------|----------------|
| `initPeriods()` | Internal | Fetch periodos.json, normalize periods, render pills and select, load initial period |
| `loadPeriod(id)` | **Global** | Switch active period, update pills/select, reload iframe. Called from HTML inline `onchange` |
| `normalizePeriods(raw)` | Internal | Validate period structure, assign defaults |
| `showLoaderError(msg, err)` | Internal | Display error overlay with message |

**State**:
- `PERIODS[]`: Array de periodos normalizados
- `currentPeriod`: ID del periodo activo

### `dashboard.js` (~1200+ lines)

**Purpose**: Dashboard SPA de 4 secciones con filtros en cascada y visualizaciones SVG/HTML.

**Inputs**: 9 JSON files from `./json/` directory (via fetch on load)

**Outputs**: Renderizado completo del dashboard en el DOM, tooltip updates, insight boxes

**Key Sections**:
| Section | ID | Content |
|---------|-----|---------|
| Ejecutivo | `#ejecutivo` | KPI cards (NPS, CSAT), bar charts, hallazgos |
| Operativo | `#operativo` | Top 3 categorías (bar charts), radar chart, fortalezas |
| Detallado | `#analitico` | Tabla de preguntas, detalle por carrera, visibilidad de servicios |
| Cualitativo | `#sentimiento` | KPIs de sentimiento, tópicos, tabla por carrera |

**Core Architecture**:
- **Cache**: `cache` object — stores fetched JSON data to avoid redundant network requests
- **DOM Registry**: `DOM` object — centralized references via `getElementById`
- **Filter System**: 6 independent filter groups (top3, radar, preguntas, detalle, visibilidad, sent) with cascade logic
- **Format Helpers**: `formatDecimal`, `formatPercent`, `formatDate`, `cortarTexto` — presentation layer utilities
- **Custom Selects**: `createCustomSelectDropdown()` for single-select, `createMultiselectDropdown()` for multi-select

**Key Functions**:
| Function | Responsibility |
|----------|----------------|
| `filtrarDatos(datos, fac, car, cic)` | Multi-dimensional filter (facultad, carrera, ciclo) with Estudios Generales special handling |
| `updateCascade(suffix)` | Repopulate select options and re-render section after filter change |
| `renderTop3(fac, car, cic)` | Render 4 category bar charts for Operativo section |
| `renderRadar(fac, car, cic)` | Render SVG radar chart with 17 dimensions |
| `renderDetalleCarrera(fac, cic)` | Career detail table with NPS/CSAT comparisons vs average |
| `renderSentimiento(fac, car, cic, tipo)` | Qualitative analysis cards, topic tags, career table |
| `getCiclosForFiltro(fac, car)` | Determine available cycles based on career rules |

**Constants**:
- `META_NPS = 50`, `META_CSAT = 93` — Target thresholds for KPI indicators
- `CARRERAS_12_CICLOS = ['Derecho', 'Psicología']` — Careers with 12 cycles
- `FACULTADES_12_CICLOS = ['Facultad de Derecho', 'Facultad de Psicología']` — Faculties with 12 cycles
- `PROGRAMA_ESTUDIOS_GENERALES` — Special handling for General Studies program
- `SAT_KEYS` — 5-level satisfaction scale keys

## Dependencies

- **Runtime**: Zero external dependencies. No jQuery, no Chart.js, no D3.js.
- **Build**: No bundler, no transpiler. ES6+ syntax assumed.
- **Loader Order**: `loader.js` debe cargarse antes que el iframe. `dashboard.js` se carga al final del `index.html` de periodo.
- **DOM**: Ambos archivos dependen de IDs HTML específicos.

## Technical Debt

- **dashboard.js monolithic**: 1200+ lines, single file. All concerns mixed (data fetch, render, events, formatting).
- **Global namespace pollution**: `showTooltip`, `hideTooltip` assigned to `window`. `loadPeriod` is global function.
- **No error boundaries**: JSON fetch failures show no visible error state (only `console.error`).
- **Cascading side effects**: `updateCascade` triggers full re-render of section on any filter change. No dirty checking.
- **No loading states per section**: Single overlay for entire dashboard. Individual sections don't show loading state.
- **Sentimiento limitation**: Topic analysis aggregates by facultad/carrera/ciclo separately, not exact row-level intersection.

## AI Agent Notes

- `dashboard.js` implements the `'use strict'` directive. All variables must be declared.
- The filter suffix convention: IDs follow pattern `filter-{type}-{suffix}` (e.g., `filter-facultad-top3`, `filter-carrera-radar`).
- Custom selects replace the native `<select>` visually but keep the original element hidden for form-like state management.
- The `filtrarDatos` function has special-cased logic for "Programa de Estudios Generales" — only cycles 1° and 2° are included.
- Multiselect cycles: the `render*` functions receive ciclo as either string (single) or array of strings (multi), plus null for "all".
- Changes to cycle range rules must be consistent between `getCiclosForFiltro()` and `getCiclosOptions()`.
