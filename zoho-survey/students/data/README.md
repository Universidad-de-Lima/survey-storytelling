# students/data

Raw CSV exports from Zoho Survey. These are the source data files consumed by the ETL pipeline (`build_json.py`) to generate JSON contracts for all survey levels.

## Architecture Role

Single source of truth for all survey data. Files placed here trigger the CI build pipeline and are the only manually uploaded data in the system. No other directory receives direct data uploads.

## Key Files

| File                                                          | Period | Level         | Status     |
| ------------------------------------------------------------- | ------ | ------------- | ---------- |
| `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2025-2.csv` | 2025-2 | Undergraduate | Historical |
| `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv` | 2026-1 | Undergraduate | Current    |

## CSV Requirements

### Naming Convention

```
ENCUESTA DE SATISFACCIÓN {LEVEL} - {PERIOD}.csv
```

Where:

- `{LEVEL}` = `PREGRADO` (undergraduate) or `POSGRADO` (postgraduate)
- `{PERIOD}` matches regex `(20\d{2}-[12])`, e.g., `2025-2`, `2026-1`

### Column Requirements

The CSV must contain columns mapped by `build_json.py` `COLUMN_RENAME` dictionary (see `scripts/build_json.py` lines ~20-58). Critical columns:

| Zoho Column Name                         | Internal Name  | Purpose                      |
| ---------------------------------------- | -------------- | ---------------------------- |
| `ID de respuesta`                        | `id_respuesta` | Unique response identifier   |
| `Net Promoter Score (de un total de 10)` | `nps`          | NPS calculation (0-10 scale) |
| `¿Qué carrera profesional estudias?`     | `carrera`      | Career filter and grouping   |
| `¿Qué ciclo es el que cursas?`           | `ciclo`        | Cycle filter and grouping    |

### Encoding

- Preferred: UTF-8 with BOM
- Fallback: Latin-1 (ISO 8859-1)
- No explicit encoding detection — tries UTF-8 first, then Latin-1

## Data Flow

```
CSV upload → CI trigger (build_students.yml)
                  ↓
         build_json.py reads data/*.csv
                  ↓
         Generates JSON contracts per period
                  ↓
         CI commits generated files
```

## CI Trigger

Push to this directory triggers `.github/workflows/build_students.yml` which:

1. Installs Python + pandas
2. Runs `build_json.py`
3. Auto-commits generated JSON files

## Dependencies

- **Source**: Zoho Survey export (manual download)
- **Consumer**: `build_json.py` (scripts/)
- **CI**: GitHub Actions (workflows/)

## Technical Debt

- **Manual upload**: CSVs must be manually exported from Zoho Survey and placed here. No automation for data ingestion.
- **Encoding fragility**: UTF-8/Latin-1 fallback without detection. Files in other encodings (e.g., UTF-16) will fail silently.
- **No schema validation**: CSV structure is validated only at runtime by `build_json.py`. No pre-upload validation exists.
- **No filename validation**: CI will attempt to process any file matching `ENCUESTA*` regardless of naming correctness.

## AI Agent Notes

- Filename must contain `ENCUESTA`, `PREGRADO` (or `POSGRADO`), and a period matching `(20\d{2}-[12])`.
- Only one CSV per period per level. Multiple CSVs for the same period will cause the last-processed to overwrite.
- To add a new period: place CSV here, run `python scripts/build_json.py` from `zoho-survey/students/`.
- Never edit CSV column headers. Zoho Survey export defines the schema.
- The ETL pipeline (`build_json.py`) is the **only** official transformation path. Do not create manual JSON files.
