# scripts

Pipeline ETL y herramientas de validación para la transformación de datos de encuestas desde CSV de Zoho Survey a contratos JSON.

## Architecture Role

Capa de transformación de datos. Opera offline (no en runtime del dashboard) y produce archivos JSON estáticos que son consumidos por la API y el frontend.

## Scripts

### `build_json.py` (Python 3.11 + pandas)

**Location**: `zoho-survey/students/scripts/build_json.py`

Transforma archivos CSV exportados de Zoho Survey en contratos JSON para cada periodo académico.

### `validate_generated_json.py` (Python 3.11)

**Location**: `zoho-survey/students/scripts/validate_generated_json.py`

Verifica que los archivos JSON generados cumplan con los contratos definidos.

## Usage

```bash
# Generate all JSON files
cd zoho-survey/students
python scripts/build_json.py

# Validate a specific level
python scripts/validate_generated_json.py undergraduate
python scripts/validate_generated_json.py postgraduate

# Or via pnpm (from root)
pnpm build:json
pnpm validate:json undergraduate
```

## Documentation

Para documentación detallada del pipeline ETL, ver:
- `zoho-survey/students/scripts/README.md` — Documentación completa de scripts
- `zoho-survey/students/JSON_SCHEMA.md` — Esquemas de contratos JSON
- `zoho-survey/students/FILTER_LOGIC.md` — Lógica de filtros en cascada
