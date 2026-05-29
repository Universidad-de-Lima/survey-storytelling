# shared

Componentes reutilizables compartidos entre todos los módulos de encuesta del sistema. Contiene estilos, JavaScript e imágenes utilizados por los dashboards de todos los niveles académicos.

## Purpose

Proveer la capa de presentación base (CSS, JS, imágenes) que consume cada instancia de dashboard de periodo, garantizando consistencia visual y comportamental sin duplicación de código.

## Architecture Role

Capa de presentación base. Proporciona el sistema de diseño (CSS), la lógica de visualización (JS) y los assets gráficos que consumen las páginas de periodo individuales.

## Key Files

| File                | Responsibility                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `css/dashboard.css` | Sistema de diseño completo: variables CSS, layout (Grid/Flexbox), tipografía, componentes (KPIs, tablas, filtros, radar, tooltips) |
| `css/loader.css`    | Estilos del splash screen, topbar, navegador de periodos (pills/select) y overlay de carga                                         |
| `js/dashboard.js`   | Lógica central del dashboard SPA. 4 secciones, filtros en cascada, renderizado de gráficos SVG, tooltips                           |
| `js/loader.js`      | Lógica del navegador de periodos: carga de `periodos.json`, inicialización de pills/select, control del iframe                     |
| `img/`              | Assets gráficos institucionales (logos ULIMA, favicon)                                                                             |

## Data Flow

```
loader.js → fetch periodos.json → render pills/select → set iframe src
                                                              ↓
                                              dashboard.js → fetch JSON files from ./json/
                                                              ↓
                                              render 4 sections (Ejecutivo, Operativo, Detallado, Cualitativo)
```

## Execution Flow

1. `{level}/index.html` loads → `loader.js` executes (IIFE)
2. `loader.js` fetches `periodos.json` → builds pills (desktop) and `<select>` (mobile)
3. User picks period → `loadPeriod()` sets `iframe.src` to `{period}/index.html`
4. Iframe loads → `dashboard.js` executes (IIFE)
5. `dashboard.js` fetches 7 JSON files from `./json/` → stores in `cache` object
6. Registers DOM references in `DOM` object (centralized `getElementById`)
7. Initializes 6 filter groups with cascade logic
8. Renders 4 sections in order: Ejecutivo → Operativo → Detallado → Cualitativo

## Dependencies

- **dashboard.js** ← consumes `dashboard.css` (class names, CSS variables)
- **loader.js** ← consumes `loader.css` (splash, topbar, pills, overlay)
- **dashboard.js** runtime: fetches JSON from `./json/` relative path; depends on exact DOM IDs in `index.html`
- **loader.js** runtime: fetches `./periodos.json`; controls iframe `dashboard-frame`

## Configuration

Variables CSS en `dashboard.css`:

- `--ulima-orange`, `--ulima-red`, `--ulima-blue`: Colores institucionales
- `--font-family-primary`: 'Roboto', sans-serif
- `--font-family-display`: 'Lusitana', Georgia, serif
- Escala de grises `--gray-900` a `--gray-50`
- Colores semánticos: `--success-pastel`, `--warning-pastel`, `--danger-pastel`

Constantes en `dashboard.js`:

- `META_NPS = 50` — umbral target NPS
- `META_CSAT = 93` — umbral target CSAT
- `CARRERAS_12_CICLOS = ['Derecho', 'Psicología']` — carreras con 12 ciclos
- `FACULTADES_12_CICLOS` — facultades con 12 ciclos

## Technical Debt

- **dashboard.js** (1200+ lines): Monolítico. Toda la lógica de negocio, renderizado y eventos en un solo archivo. Dificulta testing y mantenimiento.
- **No hay sistema de módulos**: Usa IIFE + closures en lugar de ES modules o bundler. El orden de carga es crítico.
- **Custom select dropdowns**: Implementación manual de custom selects y multiselects con código ad-hoc (~200 líneas). Posible fuente de bugs cross-browser.
- **Sin tests**: No hay pruebas unitarias ni de integración para la lógica del dashboard.
- **Tooltip positioning**: `showTooltip` usa coordenadas de evento sin boundary detection (puede desbordar viewport).
- **Console.error patterns**: Algunos catch blocks usan `console.error` sin manejo de errores visible para el usuario.

## Improvement Opportunities

- Dividir `dashboard.js` en módulos: `data-loader.js`, `render-engine.js`, `filter-system.js`, `ui-utils.js`.
- Migrar a ES modules (`<script type="module">`) para eliminar dependencia de orden de carga.
- Agregar boundary detection en `showTooltip` para prevenir desbordamiento del viewport.
- Implementar carga lazy de JSON por sección (solo fetchear datos cuando el usuario navega a esa sección).
- Agregar pruebas unitarias con Vitest o similar (el proyecto `survey-tracker` ya usa Vitest).

## AI Agent Notes

- `dashboard.js` espera que los `<select>` tengan atributo `data-multiselect="true"` para activar el dropdown multiselect.
- Los IDs HTML son contratos públicos. Lista completa en `JSON_SCHEMA.md` (sección "HTML de periodo").
- La sección cualitativa usa `id="sentimiento"` y `id="sentimiento-heading"` como IDs técnicos aunque la etiqueta visible sea "Cualitativo" y "ANÁLISIS CUALITATIVO".
- `#progress-fill` es requerido para la barra de progreso de scroll.
- No cambiar el nombre de la función `loadPeriod` — es llamada desde HTML inline (`onchange="loadPeriod(this.value)"`).
- `showTooltip` y `hideTooltip` están expuestas globalmente como `window.showTooltip` y `window.hideTooltip` para uso desde eventos inline SVG.
- El orden de carga de scripts es crítico: `dashboard.js` debe cargarse al final del `<body>` del period `index.html`, después de que todos los elementos DOM existen.
