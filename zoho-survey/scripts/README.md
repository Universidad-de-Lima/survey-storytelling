# students/scripts

Pipeline ETL y herramientas de validación para la transformación de datos de encuestas desde CSV de Zoho Survey a contratos JSON.

## Architecture Role

Capa de transformación de datos. Es el único punto de generación de datos en el sistema. Opera offline (no en runtime del dashboard) y produce archivos JSON estáticos que son consumidos por el frontend.

## Key Files

### `build_json.py` (~850 lines)

**Purpose**: Transforma archivos CSV exportados de Zoho Survey en contratos JSON para cada periodo académico.

**Input**: CSV en `data/` con columnas específicas mapeadas en `COLUMN_RENAME`

**Output**: 12+ archivos JSON por periodo en `{level}/{period}/json/`

**Pipeline Steps**:

| Step                        | Output File                                                                    | Description                                                                |
| --------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| 1. Column mapping           | —                                                                              | Renombra columnas Zoho → nombres internos via `COLUMN_RENAME`              |
| 2. Faculty assignment       | —                                                                              | Mapea carrera → facultad via `carrera_facultad` dictionary                 |
| 3. Dimension categorization | —                                                                              | Mapea dimensión → categoría via `categoria_dim` dictionary                 |
| 4. NPS calculation          | `nps_carrera.json`, `nps_ciclo_carrera.json`                                 | NPS score per dimension (career, cross)                                    |
| 5. CSAT calculation         | `csat_carrera.json`, `csat_ciclo_carrera.json`                               | CSAT score per dimension (career, cross)                                   |
| 6. Dimension breakdown      | `dimensiones.json`                                                             | Satisfaction by facultad/carrera/ciclo/dimension                           |
| 7. ID counts                | `ids.json`                                                                     | Response counts per facultad/carrera/ciclo                                 |
| 8. Dashboard data           | `dashboard_data.json`                                                          | Aggregated KPIs, hallazgos, NPS/CSAT distributions                         |
| 9. Filter options           | `filtros.json`                                                                 | facultades, carreras, ciclos, facultad_carrera mapping                     |
| 10. Sentiment analysis      | `sentimiento.json`                                                             | Topic-based semantic analysis of NPS comments (Pasivos + Detractores only) |
| 11. Period manifest         | `periodos.json` (per level)                                                    | Auto-generated chronological period list with `isNew` flag                 |

**Semantic Analysis** (`agrupar_comentarios_por_topico`):

- Only processes NPS scores < 9 (Pasivos: 7-8, Detractores: 0-6)
- Uses keyword matching against 8 predefined topics (calidad docente, malla curricular, infraestructura, etc.)
- Stopwords filtering via `STOPWORDS` set (extended Spanish stopwords)
- Topic classification via `clasificar_en_topico()` with minimum threshold of 0.5 matches
- Extracts representative phrases (top 3 longest, >20 chars)
- Generates distribution per career, faculty, and cycle

**Faculty Catalog** (hardcoded):

```python
carrera_facultad = {
    "Arquitectura": "Facultad de Arquitectura",
    "Administración": "Facultad de Ciencias Empresariales",
    "Derecho": "Facultad de Derecho",
    # ... 14 career→faculty mappings total
}
```

**Cycle Stage Mapping**:

```python
etapa_map = {1-2: "Inicial", 3-6: "Intermedio", 7-12: "Avanzado"}
```

### `validate_generated_json.py` (~250 lines)

**Purpose**: Verifica que los archivos JSON generados cumplan con los contratos definidos.

**Input**: Nivel académico como argumento CLI (`undergraduate` o `postgraduate`)

**Validation Rules**:

- File existence: 7 required files, 5 legacy files (warning only)
- Structural: JSON type checks (object vs array), non-empty validation
- Schema: Required keys per file (e.g., `dashboard_data.json` requires `resumen`, `hallazgos`, `nps`, `csat`)
- Numeric: Score fields must be numeric
- Referential: `filtros.facultad_carrera` must cover all listed faculties
- Sentiment: Topic types restricted to `negativo`, `mejora`, `positivo`

## Dependencies

- **Runtime**: Python 3.11+, `pandas`
- **CI**: GitHub Actions (`.github/workflows/build_students.yml`, `.github/workflows/validate-survey-json.yml`)

## Execution

```bash
# Generate all JSON files for all detected CSVs
cd zoho-survey/students
python ../scripts/build_json.py

# Validate a specific level
python ../scripts/validate_generated_json.py undergraduate
python ../scripts/validate_generated_json.py postgraduate
```

## Configuration (build_json.py)

| Constant           | Location       | Description                                     |
| ------------------ | -------------- | ----------------------------------------------- |
| `COLUMN_RENAME`    | Lines ~20-58   | Zoho Survey column name → internal name mapping |
| `carrera_facultad` | Lines ~270-286 | Career → Faculty catalog                        |
| `categoria_dim`    | Lines ~290-326 | Dimension → Category mapping                    |
| `TOPICOS`          | Lines ~80-145  | Topic definitions with keywords, type, icon     |
| `STOPWORDS`        | Lines ~148-175 | Spanish stopwords for text normalization        |

## Technical Debt

- **Hardcoded catalogs**: `carrera_facultad` and `categoria_dim` are hardcoded dictionaries. Changes to faculty/career structure require code modification.
- **CSV encoding fallback**: Tries UTF-8 first, then Latin-1. No explicit encoding detection.
- **Column name coupling**: Any change in Zoho Survey column names breaks the pipeline. No early validation step.
- **Legacy file generation**: Generates 5 files (`nps.json`, `csat.json`, etc.) that are no longer consumed by the frontend. Increases build time and repo size.
- **No incremental processing**: Rebuilds all periods on every run, even if only one CSV changed.
- **Sentiment analysis simplicity**: Keyword-based topic classification with no ML/NLP. Co-occurrence scoring is heuristic (exact match = 1, substring = 0.5).
- **No type safety**: `validate_generated_json.py` has extensive runtime checks that should be compile-time guarantees via typed contracts.

## AI Agent Notes

- **Idempotency**: `build_json.py` must always produce identical output for identical input. Never modify generated JSON manually — regenerate instead.
- **CSV filename format**: Must contain `ENCUESTA` and a period pattern `(20\d{2}-[12])`. Level detected by `PREGRADO` or `POSGRADO` substring.
- **New period template**: If `index.html` doesn't exist for a period, `build_json.py` copies it from `template/`. To update all periods, delete and regenerate.
- **Automatic periodos.json**: The script auto-updates `periodos.json` after processing, marking the latest chronological period as `isNew: true`.
- The `COLUMN_RENAME` dictionary has a documented fix (CORRECCIÓN #1) for the NPS comment column naming.
- When adding new topics to `TOPICOS`, ensure `tipo` is one of: `negativo`, `mejora`, `positivo`.
