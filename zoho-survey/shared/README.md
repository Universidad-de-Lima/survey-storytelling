# shared

Componentes reutilizables compartidos entre todos los módulos de encuesta del sistema. Contiene estilos, JavaScript e imágenes utilizados por los dashboards de todos los niveles académicos.

## Architecture Role

Capa de presentación base. Proporciona el sistema de diseño (CSS), la lógica de visualización (JS) y los assets gráficos que consumen las páginas de periodo individuales.

## Key Files

| File | Responsibility |
|------|----------------|
| `css/dashboard.css` | Sistema de diseño completo: variables CSS, layout (Grid/Flexbox), tipografía, componentes (KPIs, tablas, filtros, radar, tooltips) |
| `css/loader.css` | Estilos del splash screen, topbar, navegador de periodos (pills/select) y overlay de carga |
| `js/dashboard.js` | Lógica central del dashboard SPA. 4 secciones, filtros en cascada, renderizado de gráficos SVG, tooltips |
| `js/loader.js` | Lógica del navegador de periodos: carga de `periodos.json`, inicialización de pills/select, control del iframe |
| `img/logo-horizontal.png` | Logo horizontal usado en topbar del loader |
| `img/logo-vertical.png` | Logo vertical usado en splash screen |
| `img/logo-isotipo.png` | Isotipo usado en footer del dashboard |
| `img/favicon.png` | Favicon del dashboard |

## Data Flow

```
loader.js → fetch periodos.json → render pills/select → set iframe src
                                                              ↓
                                              dashboard.js → fetch JSON files from ./json/
                                                              ↓
                                              render 4 sections (Ejecutivo, Operativo, Detallado, Cualitativo)
```

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

## Technical Debt

- **dashboard.js** (1200+ lines): Monolítico. Toda la lógica de negocio, renderizado y eventos en un solo archivo. Dificulta testing y mantenimiento.
- **No hay sistema de módulos**: Usa IIFE + closures en lugar de ES modules o bundler. El orden de carga es crítico.
- **Custom select dropdowns**: Implementación manual de custom selects y multiselects con código ad-hoc (~200 líneas). Posible fuente de bugs cross-browser.
- **Sin tests**: No hay pruebas unitarias ni de integración para la lógica del dashboard.
- **Tooltip positioning**: `showTooltip` usa coordenadas de evento sin boundary detection (puede desbordar viewport).
- **Console.error patterns**: Algunos catch blocks usan `console.error` sin manejo de errores visible para el usuario.

## AI Agent Notes

- `dashboard.js` espera que los `<select>` tengan atributo `data-multiselect="true"` para activar el dropdown multiselect.
- Los IDs HTML son contratos públicos. Lista completa en `JSON_SCHEMA.md` (sección "HTML de periodo").
- La sección cualitativa usa `id="sentimiento"` y `id="sentimiento-heading"` como IDs técnicos aunque la etiqueta visible sea "Cualitativo" y "ANÁLISIS CUALITATIVO".
- `#progress-fill` es requerido para la barra de progreso de scroll.
- No cambiar el nombre de la función `loadPeriod` — es llamada desde HTML inline (`onchange="loadPeriod(this.value)"`).
- `showTooltip` y `hideTooltip` están expuestas globalmente como `window.showTooltip` y `window.hideTooltip` para uso desde eventos inline SVG.
