# shared/css

Sistema de diseño del dashboard. Define la identidad visual, el layout responsivo y todos los componentes de UI mediante CSS vanilla con custom properties.

## Architecture Role

Capa de presentación pura. No contiene lógica de negocio. Todos los estilos son consumidos por `index.html` de cada periodo y complementan la estructura DOM generada por `dashboard.js`.

## Key Files

| File | Lines | Responsibility |
|------|-------|----------------|
| `dashboard.css` | ~800+ | Sistema de diseño completo: variables CSS, reset, tipografía, layout (sticky header, grid cards, tablas), componentes (KPIs, barras, filtros, tabs, tooltips, radar), animaciones, responsive |
| `loader.css` | ~300+ | Splash screen animado, topbar fija con logo y selector de periodos, pills, overlay de carga, iframe container, estilos mobile |

## Design Tokens (dashboard.css)

```css
:root {
  --ulima-orange: #FF5117;       /* Primary brand color */
  --ulima-red: #FF0000;           /* Danger / low scores */
  --ulima-blue: #2563EB;          /* Accent */
  --font-family-primary: 'Roboto', sans-serif;
  --font-family-display: 'Lusitana', Georgia, serif;
  --focus-outline: 2px solid #FF5117;
}
```

## Responsive Breakpoints

- **Desktop**: Layout grid de 4 columnas para tarjetas Top 3
- **Mobile**: Tablas con scroll horizontal, filtros en columna, navegación mediante select en lugar de pills
- **Radar SVG**: Escalado mediante `viewBox="-40 -40 600 600"` con `preserveAspectRatio`

## Components (dashboard.css)

| Component | Selector Pattern | Behavior |
|-----------|-----------------|----------|
| KPI Cards | `.kpi-card` | Valor grande + barra de progreso + meta |
| Bar Charts | `.bar-chart`, `.bar-segment` | Segmentos apilados con tooltips |
| Radar Chart | `.radar-svg` | SVG inline con polígonos y ejes |
| Filter Selects | `.filter-select`, `.filter-custom-select` | Custom dropdown con panel |
| Multiselect | `.filter-multiselect`, `.filter-multiselect-panel` | Checkbox panel multi-selección |
| Tables | `.visibility-table` | Datos con barras de distribución inline |
| Insight Boxes | `.insight-box.info`, `.insight-box.success`, `.insight-box.warning`, `.insight-box.pink` | Alertas contextuales con 4 variantes |
| Progress Bar | `.progress-bar`, `.progress-fill` | Indicador de scroll vertical |
| Tooltip | `#tooltip` | Flotante absoluto para barras y segmentos |

## Dependencies

- **External**: Google Fonts (Roboto + Lusitana) cargadas vía `<link>` en el HTML
- **Internal**: `dashboard.css` asume estructura DOM generada por `dashboard.js`

## Technical Debt

- **Sin prefijos**: No incluye prefijos vendor (`-webkit-`, `-moz-`). Asume navegadores modernos.
- **Unidades mixtas**: Mezcla `px`, `rem` y `%` sin sistema consistente de espaciado.
- **Sin CSS custom properties para espaciado**: Las únicas variables CSS son colores y fonts. Espaciados y tamaños son valores literales.
- **Sin modo oscuro**: No hay `prefers-color-scheme` ni tema alternativo.

## AI Agent Notes

- `loader.css` se carga en el `index.html` raíz de cada nivel. `dashboard.css` se carga en el template de periodo.
- `loader.css` usa `overflow: hidden` en `body` para evitar scroll durante el splash.
- La clase `visible` en `.main-wrapper` controla la aparición del dashboard después de la carga de datos.
- Los estilos de tooltip usan `z-index: 99999` para asegurar visibilidad sobre cualquier otro elemento.
