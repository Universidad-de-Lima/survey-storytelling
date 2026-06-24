# students

Módulo de encuestas estudiantiles. Contiene scripts ETL, documentación de contratos e instancias de dashboard por nivel académico y periodo.

> ⚠️ **Los CSVs ahora residen en `../../data/` (raíz del proyecto).**  
> El template HTML está en `../template/` (compartido con todos los tipos de encuesta).

## Purpose

Implementar el pipeline de datos para encuestas estudiantiles: desde la ingesta de CSV hasta la generación de dashboards autónomos por nivel académico (pregrado, posgrado, graduados) y periodo.

## Architecture Role

Módulo del dominio de encuestas estudiantiles. Implementa el pipeline desde los datos crudos hasta los dashboards. Se organiza en tres niveles activos: `undergraduate/`, `graduate/` y `posgraduate/`.

## Submodules

| Submodule     | Path             | Status      | Responsibility                                                             |
| ------------- | ---------------- | ----------- | -------------------------------------------------------------------------- |
| Scripts       | `../scripts/`    | Active      | ETL pipeline (build_json.py) + JSON validator (validate_generated_json.py) |
| Undergraduate | `undergraduate/` | Active      | Dashboard instances for undergraduate surveys (2025-2, 2026-1)             |
| Graduate      | `graduate/`      | Active      | Dashboard instances for graduate surveys (2026)                            |
| Postgraduate  | `posgraduate/`   | Placeholder | Empty structure awaiting posgraduate survey data                           |

## Key Files

| File                                                            | Responsibility                                  |
| --------------------------------------------------------------- | ----------------------------------------------- |
| `../../data/*.csv`                                              | Raw survey data from Zoho Survey (project root) |
| `../scripts/build_json.py`                                      | ETL: transforms CSV → JSON contracts per period |
| `../scripts/validate_generated_json.py`                         | Validates JSON contract compliance              |
| `../template/index.html`                                        | Scaffold copied to new periods                  |
| `FILTER_LOGIC.md`                                               | Filter cascade logic specification              |
| `JSON_SCHEMA.md`                                                | JSON contract schema documentation              |

## Data Flow

```
../../data/*.csv → build_json.py → {level}/{periodo}/json/*.json
                                       → {level}/{periodo}/index.html (from ../template/)
                                       → {level}/periodos.json (auto-updated)
```

## Execution Flow

1. User places CSV file in `../../data/` (project root) with naming convention `ENCUESTA DE SATISFACCIÓN {LEVEL} - {PERIOD}.csv`
2. User runs `python ../scripts/build_json.py` from `zoho-survey/students/` or `python scripts/build_json.py` from project root
3. Script detects level from filename keywords (GRADUADOS, PREGRADO, POSGRADO, etc.)
4. Extracts period from filename via regex `(20\d{2}(?:-[12])?)`
5. Transforms CSV data through 11 pipeline steps (column mapping, aggregation, topic analysis)
6. Writes 12+ JSON files to `{level}/{period}/json/`
7. Copies `../template/index.html` if period `/index.html` doesn't exist
8. Updates `{level}/periodos.json` with new period entry

## Dependencies

- **Internal**: Consumes `shared/` CSS, JS and images for rendering
- **Scripts**: `build_json.py` y `validate_generated_json.py` son independientes entre sí
- **CSV source**: `../../data/` (project root)

## Configuration

- `periodos.json` por nivel — auto-generado por `build_json.py`. Define orden cronológico y flag `isNew`.
- La detección de nivel se hace por nombre de archivo. Orden de prioridad: `NO DOCENTES` → `EMPLEADORES` → `EGRESADOS` → `DOCENTES` → `GRADUADOS` → `ESTUDIANTIL/ESTUDIANTES`.

## Technical Debt

- **Posgrado sin datos**: La estructura `posgraduate/` existe pero no contiene datos procesados.
- **Archivos legado**: `nps.json`, `csat.json`, `nps_carrera.json`, `csat_carrera.json`, `resumen.json` aún se generan pero son legacy. El dashboard moderno no los consume.
- **Template no versionado**: `../template/index.html` no tiene control de versiones. Cambios no se reflejan retroactivamente.
- **CSV filename validation**: No hay validación pre-ETL del formato de nombre de archivo.

## Improvement Opportunities

- Agregar flag `--level` a `build_json.py` para procesar un nivel específico sin scanear todos los CSVs.
- Migrar legacy JSON generation a un flag `--legacy` o eliminarlo.
- Agregar version metadata a `../template/index.html` para detectar templates desactualizados.

## AI Agent Notes

- Documentación detallada de contratos en `JSON_SCHEMA.md` y lógica de filtros en `FILTER_LOGIC.md`.
- El ETL copia `../template/index.html` solo si no existe en el directorio del periodo.
- Validar JSON localmente: `python ../scripts/validate_generated_json.py {nivel}` desde `zoho-survey/students/` o `python scripts/validate_generated_json.py {nivel}` desde la raíz.
- Los archivos CSV deben estar en `../../data/` con prefijo `ENCUESTA` en el nombre.
- El entry point del navegador es `zoho-survey/index.html` (no `students/undergraduate/index.html`).
