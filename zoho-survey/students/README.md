# students

Módulo de encuestas estudiantiles. Contiene datos fuente (CSV), scripts ETL, templates, documentación de contratos e instancias de dashboard por nivel académico y periodo.

## Architecture Role

Módulo principal del dominio de encuestas. Implementa el pipeline completo desde los datos crudos de Zoho Survey hasta los dashboards desplegables. Se organiza en dos niveles: `undergraduate/` (pregrado, activo) y `postgraduate/` (posgrado, placeholder).

## Submodules

| Submodule | Path | Status | Responsibility |
|-----------|------|--------|----------------|
| Data | `data/` | Active | Raw CSV exports from Zoho Survey |
| Scripts | `scripts/` | Active | ETL pipeline (build_json.py) + JSON validator (validate_generated_json.py) |
| Template | `template/` | Active | HTML template copied to each new period by ETL |
| Undergraduate | `undergraduate/` | Active | Dashboard instances for undergraduate surveys (2025-2, 2026-1) |
| Postgraduate | `postgraduate/` | Placeholder | Empty structure awaiting postgraduate survey data |

## Key Files

| File | Responsibility |
|------|----------------|
| `data/ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - {periodo}.csv` | Raw survey data from Zoho Survey |
| `scripts/build_json.py` | ETL: transforms CSV → JSON contracts per period |
| `scripts/validate_generated_json.py` | Validates JSON contract compliance |
| `template/index.html` | Scaffold copied to new periods |
| `FILTER_LOGIC.md` | Filter cascade logic specification |
| `JSON_SCHEMA.md` | JSON contract schema documentation |

## Data Flow

```
data/*.csv → build_json.py → undergraduate/{periodo}/json/*.json
                                  → undergraduate/{periodo}/index.html (from template)
                                  → undergraduate/periodos.json (auto-updated)
```

## Dependencies

- **Internal**: Consumes `shared/` CSS, JS and images for rendering
- **Scripts**: `build_json.py` y `validate_generated_json.py` son independientes entre sí

## Configuration

- `periodos.json` por nivel — auto-generado por `build_json.py`. Define orden cronológico y flag `isNew`.
- La detección de nivel se hace por nombre de archivo: `PREGRADO` → `undergraduate/`, `POSGRADO` → `postgraduate/`.

## Technical Debt

- **Postgraduate sin datos**: La estructura `postgraduate/` existe pero no contiene datos procesados. El ETL busca archivos con `POSGRADO` en el nombre.
- **Archivos legado**: `nps.json`, `csat.json`, `nps_carrera.json`, `csat_carrera.json`, `resumen.json` aún se generan pero son legacy. El dashboard moderno no los consume.
- **Template no versionado**: `template/index.html` no tiene control de versiones. Cambios en el template no se reflejan retroactivamente en periodos existentes.

## AI Agent Notes

- Documentación detallada de contratos en `JSON_SCHEMA.md` y lógica de filtros en `FILTER_LOGIC.md`.
- El ETL copia `template/index.html` solo si no existe en el directorio del periodo. Para actualizar periodos existentes, copiar manualmente.
- Validar JSON localmente: `python scripts/validate_generated_json.py {nivel}`.
- Los archivos CSV deben estar en `data/` con prefijo `ENCUESTA` y el periodo en el nombre debe coincidir con el regex `(20\d{2}-[12])`.
