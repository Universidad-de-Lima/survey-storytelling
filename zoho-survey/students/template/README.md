# students/template

Template HTML para los dashboards de periodo. Es copiado por `build_json.py` a cada nuevo directorio de periodo cuando no existe un `index.html`.

## Architecture Role

Scaffold del dashboard de periodo. Define la estructura DOM completa que `dashboard.js` espera para funcionar. Cualquier modificación en este template afecta a todos los periodos futuros.

## Key File

`index.html` — Documento HTML5 que define:

- **4 secciones del dashboard**: Ejecutivo (`#ejecutivo`), Operativo (`#operativo`), Detallado (`#analitico`), Cualitativo (`#sentimiento`)
- **Sistema de filtros**: 6 grupos de filtros con convención de IDs por sufijo (`top3`, `radar`, `preguntas`, `detalle`, `visibilidad`, `sent`)
- **Componentes UI**: KPI cards, contenedores de gráficos (bar-chart, radar-svg), tablas, insight boxes, tooltip, progress bar
- **Footer**: Información de fuente y periodo (actualizado por `dashboard.js`)

## DOM Contract

El template expone IDs que `dashboard.js` consume como contratos públicos:

| ID Prefix | Section | Element Type |
|-----------|---------|--------------|
| `kpi-*` | Ejecutivo | KPIs (NPS, CSAT) |
| `nps-bar`, `csat-bar` | Ejecutivo | Bar charts |
| `chart-{categoria}` | Operativo | Category bar charts (academico, infraestructura, tecnologia, admin-bienestar) |
| `radar-chart` | Operativo | SVG radar |
| `filter-{type}-{sufijo}` | All sections | Filter selects |
| `reset-{sufijo}` | All sections | Reset buttons |
| `tabla-*` | Detallado | Data tables |
| `tbody-*` | Detallado | Table bodies |
| `insight-*` | All sections | Insight text containers |
| `sentimiento` | Cualitativo | Section ID (técnico, aunque etiqueta visible sea "Cualitativo") |
| `progress-fill` | Global | Scroll progress bar |
| `tooltip` | Global | Floating tooltip |

## Dependencies

- **CSS**: `../../../shared/css/dashboard.css` (relative path from period directory)
- **JS**: `../../../shared/js/dashboard.js` (loaded at end of body)
- **Images**: `../../../shared/img/logo-isotipo.png` (footer logo)

## Copy Behavior

`build_json.py` ejecuta:
```python
if not INDEX_FILE.exists():
    copyfile(TEMPLATE_INDEX, INDEX_FILE)
```

Esto significa que periodos existentes **no** se actualizan automáticamente con cambios del template. Para propagar cambios a periodos existentes, copiar manualmente.

## Technical Debt

- **Rutas relativas**: Las rutas `../../../shared/` asumen 3 niveles de profundidad (`undergraduate/{periodo}/`). Nuevos niveles con diferente profundidad romperían las rutas.
- **Sin versionado de template**: No hay mecanismo para detectar que un periodo fue generado con una versión anterior del template.
- **IDs hardcoded**: Todos los IDs de filtro están hardcoded en lugar de generarse dinámicamente.
- **Textos visibles vs técnicos**: El ID `sentimiento` contrasta con la etiqueta visible "Cualitativo", lo que puede causar confusiones.

## AI Agent Notes

- El sufijo `sent` en filtros de la sección cualitativa es obligatorio (convención documentada en `FILTER_LOGIC.md`).
- Los selects con `data-multiselect="true"` activan el dropdown multiselect en `dashboard.js`.
- El atributo `onchange="loadPeriod(this.value)"` en `#period-select` es requerido por `loader.js`.
- No cambiar el orden de carga de scripts: `loader.js` antes de cerrar `</body>` en el loader, `dashboard.js` al final del template de periodo.
