# zoho-survey

Módulo de procesamiento y visualización de encuestas de satisfacción. Contiene toda la lógica ETL, los contratos de datos y la capa de presentación para los dashboards de encuestas estudiantiles.

## Architecture Role

Capa única del sistema que abarca desde la ingesta de datos CSV hasta el renderizado del dashboard. Se subdivide en `shared/` (componentes reutilizables) y `students/` (lógica específica para encuestas estudiantiles).

## Submodules

| Submodule | Path | Responsibility |
|-----------|------|----------------|
| **Shared** | `shared/` | CSS, JS, imágenes reutilizables entre todos los módulos de encuesta |
| **Students** | `students/` | Datos, scripts ETL, templates e instancias de encuestas estudiantiles |

## Key Files

| File | Function |
|------|----------|
| `shared/js/dashboard.js` | Core SPA: 4 secciones (Ejecutivo, Operativo, Detallado, Cualitativo) con filtros en cascada |
| `shared/js/loader.js` | Navegador de periodos académicos con pills (desktop) y select (mobile) |
| `shared/css/dashboard.css` | Sistema de diseño con variables CSS, layout responsivo |
| `shared/css/loader.css` | Estilos del splash screen, topbar y navegador de periodos |
| `students/scripts/build_json.py` | Pipeline ETL: CSV → JSON contracts |
| `students/scripts/validate_generated_json.py` | Validador de contratos JSON |
| `students/template/index.html` | Template HTML copiado a cada nuevo periodo |
| `students/JSON_SCHEMA.md` | Especificación detallada de contratos JSON |
| `students/FILTER_LOGIC.md` | Lógica de filtros en cascada del dashboard |

## Dependencies

- **Internal**: `shared/` es consumido por `students/{level}/{period}/`
- **External**: Ninguna en runtime. Python + pandas para ETL.

## Configuration

- `students/undergraduate/periodos.json` — Lista de periodos de pregrado (auto-generada)
- `students/postgraduate/periodos.json` — Lista de periodos de posgrado (no generada aún)

## Technical Debt

- `students/` y `shared/` son los únicos subdirectorios; el diseño actual solo soporta encuestas estudiantiles. Nuevos tipos de encuesta requerirían módulos adicionales al mismo nivel.
- Las imágenes en `shared/img/` están acopladas a la marca institucional (logos ULIMA). Reutilización externa requiere reemplazo.

## AI Agent Notes

- El HTML de periodo (`index.html`) tiene contratos DOM estrictos documentados en `JSON_SCHEMA.md`.
- No agregar dependencias JS externas al dashboard sin evaluar impacto en despliegue estático (GitHub Pages).
- `dashboard.js` usa IIFE (Immediately Invoked Function Expression) con `'use strict'`.
