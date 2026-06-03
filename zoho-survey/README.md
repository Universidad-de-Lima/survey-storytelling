# zoho-survey

Aplicación principal del sistema. Contiene el entry point (loader), assets compartidos, scripts ETL, templates y datos de encuestas por nivel académico y periodo.

## Estructura

```
zoho-survey/
├── index.html              ← Entry point: navegador de encuestas (loader)
├── underconstruction.html  ← Página placeholder
├── shared/                 ← CSS, JS, imágenes compartidos entre todos los dashboards
├── template/               ← Template HTML para nuevos periodos
├── scripts/                ← Pipeline ETL y validación
│   ├── build_json.py       ← CSV → 9 JSONs por periodo
│   ├── validate_generated_json.py ← Validador de contratos
│   ├── lib/config.py       ← Configuración externalizada (COLUMN_RENAME, mappings, TOPICOS)
│   └── schemas/            ← 3 JSON Schemas (draft-07)
└── students/               ← Encuestas estudiantiles
    ├── undergraduate/      ← Pregrado (2025-2, 2026-1)
    ├── graduate/           ← Graduados (2026)
    └── posgraduate/        ← Placeholder
```

## Pipeline ETL

### `build_json.py` (~770 líneas)

Transforma CSVs en `data/` a contratos JSON por periodo.

**Pipeline**: 9 pasos → 9 archivos JSON generados por periodo.

| Paso | Archivo | Descripción |
|------|---------|-------------|
| 1 | `dashboard_data.json` | KPIs agregados, NPS/CSAT, hallazgos, tendencias |
| 2 | `dimensiones.json` | Satisfacción por facultad/carrera/ciclo/dimensión |
| 3 | `ids.json` | Conteos de respuestas por segmento |
| 4 | `nps_ciclo_carrera.json` | NPS por carrera + ciclo |
| 5 | `csat_ciclo_carrera.json` | CSAT por carrera + ciclo |
| 6 | `nps_carrera.json` | NPS por carrera (legacy) |
| 7 | `csat_carrera.json` | CSAT por carrera (legacy) |
| 8 | `filtros.json` | Metadatos para cascada de filtros |
| 9 | `sentimiento.json` | Análisis semántico por tópicos |

**Análisis semántico**: solo procesa NPS < 9 (Pasivos 7-8, Detractores 0-6). Usa 8 tópicos predefinidos con palabras clave + stopwords en español.

### `validate_generated_json.py`

Verifica integridad estructural de los JSONs generados. Uso: `python validate_generated_json.py undergraduate`

## Flujo de ejecución

1. Colocar CSV en `data/` con naming: `ENCUESTA DE SATISFACCIÓN {TIPO} - {PERIODO}.csv`
2. Ejecutar `python scripts/build_json.py` desde `zoho-survey/`
3. El script detecta tipo y periodo, genera JSONs, copia template, actualiza `periodos.json`
4. El dashboard carga los JSONs vía `loader.js` → iframe → `dashboard.js`

## Detección de nivel por nombre de archivo

Prioridad: `NO DOCENTES` → `EMPLEADORES` → `EGRESADOS` → `DOCENTES` → `GRADUADOS` → `ESTUDIANTIL/ESTUDIANTES`

## Deuda técnica

- `nps_carrera.json` y `csat_carrera.json` son legacy (el frontend usa las versiones `_ciclo_carrera`)
- `posgraduate/` sin datos procesados
- Template `index.html` no tiene control de versiones
