# zoho-survey/scripts

Pipeline ETL y herramientas de validacion para la transformacion de datos de encuestas desde CSV de Zoho Survey a contratos JSON.

## Architecture Role

Capa de transformacion de datos. Es el unico punto de generacion de datos en el sistema. Opera offline (no en runtime del dashboard) y produce archivos JSON estaticos que son consumidos por el frontend.

Los contratos formales de tipos viven en `schemas/*.schema.json` (JSON Schema Draft-07) y estan documentados en lenguaje humano en `CONTRACTS.md` (raiz del repositorio).

## Key Files

### `build_json.py` (~820 lineas)

**Purpose**: Transforma archivos CSV exportados de Zoho Survey en contratos JSON para cada periodo academico.

**Input**: CSVs en `data/` con columnas especificas mapeadas en `COLUMN_RENAME_PREGRADO` / `COLUMN_RENAME_GRADUADO` (`lib/config.py`).

**Output**: 11 archivos JSON por periodo en `{level}/{period}/json/` + `periodos.json` actualizado por nivel + `index.html` copiado desde `template/`.

**Pipeline Steps**:

| Step | Output File(s) | Description |
| --- | --- | --- |
| 1. Deteccion nivel + periodo | — | Substring matching en filename (NO DOCENTES, EMPLEADORES, EGRESADOS, DOCENTES, GRADUADOS, ESTUDIANTIL) + regex `(20\d{2}(?:-[12])?)`. |
| 2. Inyeccion HTML | `index.html` | Lee `template/index.html` y reemplaza `{{SHARED_PATH}}` por la ruta relativa correcta. |
| 3. Lectura CSV | — | `read_csv_robust` (UTF-8 con fallback latin-1) + limpieza BOM en headers. |
| 4. Validacion columnas criticas | — | `["ID de respuesta", "Net Promoter Score (de un total de 10)", "La Universidad de Lima"]` + columna carrera especifica. |
| 5. Renombrado de columnas | — | `COLUMN_RENAME_PREGRADO` (37 mapeos) o `COLUMN_RENAME_GRADUADO` (48 mapeos). |
| 6. Asignacion de facultad | — | `df["Carrera"].map(CARRERA_FACULTAD)` con fallback a "Programa de Estudios Generales" u "Otra". |
| 7. Normalizacion de fechas | — | `normalize_dates`: meses español→ingles, AM/PM de Zoho. |
| 8. Metricas NPS globales | `dashboard_data.json` (nps top-level) | Clasifica en promotores (>=9), pasivos (7-8), detractores (<=6). `calc_nps(p, pa, d)`. |
| 9. Metricas CSAT globales | `dashboard_data.json` (csat top-level) | Usa `RESPUESTAS_TEXTO[:3]` (T3B) sobre `RESPUESTAS_TEXTO[:5]`. `calc_csat(t3b, total)`. |
| 10. Empleabilidad (solo graduados) | `dashboard_data.json` (resumen.empleabilidad) | Si existe `Situación laboral`, cuenta respuestas en `EMPLEABILIDAD_CATEGORIAS`. |
| 11. NPS/CSAT por carrera | `nps_carrera.json`, `csat_carrera.json` | Groupby Carrera (legacy). |
| 12. NPS/CSAT por ciclo+carrera | `nps_ciclo_carrera.json`, `csat_ciclo_carrera.json` | Groupby (Facultad, Carrera, Ciclo) si `tiene_ciclo`. |
| 13. Dimensiones | `dimensiones.json` | Groupby (Facultad, Carrera, Ciclo) × `categoria_dim`. |
| 14. Conteos | `ids.json` | Groupby (Facultad, Carrera, Ciclo) con `total=len(sub)`. |
| 15. Hallazgos + dashboard | `dashboard_data.json` | Estructura `version: "2.0"` + `resumen` + `hallazgos` + `nps` (lowercase) + `csat`. |
| 16. Filtros | `filtros.json` | `version`, `has_ciclo`, `facultades` (sorted), `carreras` (sorted), `ciclos` (sorted), `facultad_carrera`. |
| 17. Fragmentacion NPS | `fragmentos_nps.json` | Por cada comentario NPS con texto, `fragmentar_comentario_nps()` (spaCy). |
| 18. Dataset cualitativo | `dataset_cualitativo.json` | Por cada fragmento, `procesar_opinion_unit()` + `analizar_sentimiento_intensidad()`. |
| 19. Sentimiento v3.0 | `sentimiento.json` | Transformacion UI del dataset_cualitativo. |
| 20. Periodos | `periodos.json` (por nivel) | Sorted por año-semestre, marca `isNew: true` solo en el ultimo. |

### Motor cualitativo moderno (v3.0)

> **Importante:** La documentacion anterior describia el motor cualitativo como keyword matching contra 8 topicos predefinidos. Esto es obsoleto desde v3.0.2. El motor actual usa SentenceTransformer + spaCy + sklearn.

**Flujo real** (ver ARCHITECTURE.md para el diagrama completo):

```
Comentario NPS
    ↓ sanitizar_comentario (lib/nlp.py)
    ↓ fragmentar_comentario_nps (lib/segmentacion_nps.py, spaCy)
    ↓ procesar_opinion_unit (lib/aspect_extraction.py, spaCy noun chunks + embeddings)
    ↓ analizar_sentimiento_intensidad (lib/sentiment_engine.py, embeddings + reglas lexicas)
    ↓
sentimiento.json v3.0
```

**Modelos externos** (descargados en runtime, cacheados):

- `paraphrase-multilingual-MiniLM-L12-v2` (~118 MB, SentenceTransformer, cache en `~/.cache/huggingface/`).
- `es_core_news_sm` (spaCy, descargado en CI via `python -m spacy download`).

**Procesamiento de comentarios**: el ETL procesa TODOS los comentarios NPS con texto (no solo Pasivos + Detractores como decia la documentacion anterior). La fragmentacion genera Meaning Units que luego se clasifican individualmente.

**Calibracion de sentimiento**: el motor aplica multiples niveles de calibracion:
- Umbral de neutralidad `abs(diff) < 0.12` (sentiment_engine.py, reducido desde `0.20` en versiones previas para recuperar criticas valiosas que antes quedaban ocultas como neutras).
- **Fase 7 (2026-06-24)**: Umbral de confianza configurable `SENTIMENT_CONFIDENCE_THRESHOLD = 0.4` en `lib/config.py`. Cuando la confianza del softmax cae bajo el umbral Y no hay senal lexica fuerte (es_evento_negativo=False), el sentimiento se fuerza a 'neutro'. Esto resuelve el caso degenerado donde los 3 scores son iguales (ej. 0,0,0) y argmax cae arbitrariamente en 'positivo' (primer indice). Calibracion empirica sobre pregrado 2026-1: umbral 0.4 produce cambios selectivos (2.7%), umbral 0.6 seria destructivo (88.8%).

### `validate_generated_json.py` (~390 lineas)

**Purpose**: Valida los JSONs generados aplicando JSON Schema Draft-07 + invariantes de negocio.

**Input**: Niveles academicos como argumentos CLI (default: `["undergraduate", "graduate"]`).

**Validation Pipeline**:

1. **JSON Schema Draft-07**: carga cada schema desde `schemas/` y ejecuta `Draft7Validator.iter_errors()`. Schemas disponibles:
   - `dashboard_data.schema.json`
   - `filtros.schema.json`
   - `sentimiento.schema.json`
   - `dimensiones.schema.json`
   - `nps_ciclo_carrera.schema.json`
   - `csat_ciclo_carrera.schema.json`
   - `ids.schema.json`

2. **Invariantes de negocio** (no expresables en JSON Schema):
   - Suma de `total` en `ids.json` debe ser > 0.
   - `filtros.facultad_carrera` debe cubrir todas las facultades listadas.
   - `dimensiones.json` debe tener al menos una fila con `total > 0`.
   - `periodos.json` debe tener exactamente un item con `isNew: true`.

3. **Validacion HTML**: cada `index.html` debe contener los fragmentos requeridos para la seccion cualitativa.

**Comportamiento**:

- Si el schema rechaza, el validador rechaza (no es mas permisivo que el schema).
- Si la libreria `jsonschema` no esta instalada, emite warning pero continua con las validaciones custom.
- Return codes: 0 = exito, 1 = errores encontrados.

### `validacion_empirica_sentimiento.py` (34 lineas)

**Purpose**: Script ad-hoc de calibracion manual del motor de sentimiento. Ejecuta 10 muestras etiquetadas contra `analizar_sentimiento_intensidad()` y reporta `classification_report` de scikit-learn.

**No es parte del CI**. Es una herramienta interna para evaluar cambios en la calibracion del motor.

### `lib/` (7 modulos)

| Modulo | Lineas | Responsabilidad | Estado |
| --- | --- | --- | --- |
| `config.py` | 382 | Mapeos de columnas, catalogos de negocio, topicos (legacy, sin uso), stopwords (legacy, sin uso). | Activo. |
| `metrics.py` | 26 | `calc_nps(p, pa, d)` y `calc_csat(t3b, total)`. Funciones puras. | Activo. |
| `io_helper.py` | 81 | `load_json` (BOM-safe), `read_csv_robust` (UTF-8 con fallback latin-1), `normalize_dates`. | Activo. |
| `nlp.py` | 457 | `sanitizar_comentario` (activo) + `agrupar_comentarios_por_topico` (267 lineas, **MUERTO**: importado por build_json.py pero no invocado). | Parcialmente obsoleto. |
| `segmentacion_nps.py` | 324 | Fragmentacion de comentarios NPS en Meaning Units con spaCy. | Activo. |
| `aspect_extraction.py` | 254 | Extraccion de aspecto literal (spaCy noun chunks) + normalizacion a dimension oficial. | Activo. |
| `sentiment_engine.py` | 135 | Clasificacion hibrida sentimiento + intensidad (1-5). | Activo. |

### `schemas/` (7 JSON Schemas Draft-07)

Fuente formal de tipos. Cargados por `validate_generated_json.py`.

### `config/stop_aspectos.json`

Lista de 24 stopwords para extraccion de aspectos (consumido por `aspect_extraction.py`).

### `tests/` (4 suites Python)

- `test_sentiment_engine.py` (11 tests, unittest + mocking para modelo funcional)
- `test_segmentacion.py` (8 tests, unittest)
- `test_aspect_extraction.py` (5 tests, unittest — **pendiente verificar**: assertions esperan buckets que pueden no existir en `CATEGORIA_PADRE_MAP`)
- `test_calibracion.py` (3 casos, script print-based, no unittest)

**Nota:** Estos tests no se ejecutan en CI actualmente. Solo se ejecutan manualmente.

## Dependencies

- **Runtime ETL**: Python 3.11+ (fijado en CI), `pandas`, `sentence-transformers`, `scikit-learn`, `spacy`, `numpy` (transitivo).
- **Modelos externos**: `paraphrase-multilingual-MiniLM-L12-v2` (Hugging Face), `es_core_news_sm` (spaCy).
- **Validador**: Python 3.11+, `jsonschema` (Draft-07).
- **CI**: GitHub Actions (`.github/workflows/build_students.yml`, `.github/workflows/validate-survey-json.yml`).

## Execution

```bash
# Generar todos los JSON files para todos los CSVs detectados
# Nota: build_json.py debe ejecutarse desde zoho-survey/students/ o con PYTHONPATH configurado
cd zoho-survey/students
python ../scripts/build_json.py

# O usando npm desde la raiz del proyecto
npm run build:json

# Validar niveles especificos (default: undergraduate + graduate)
python zoho-survey/scripts/validate_generated_json.py undergraduate graduate

# O usando npm
npm run validate:json

# Ejecutar tests Python (manualmente, no en CI)
cd zoho-survey/scripts
python -m unittest discover tests/

# Calibracion empirica del motor de sentimiento
python zoho-survey/scripts/validacion_empirica_sentimiento.py
```

## Configuration (`lib/config.py`)

| Constante | Tipo | Description |
| --- | --- | --- |
| `COLUMN_RENAME_PREGRADO` | Dict[str, str] | 37 mapeos Zoho Survey → nombres internos para pregrado. |
| `COLUMN_RENAME_GRADUADO` | Dict[str, str] | 48 mapeos para graduados (incluye situacion laboral, dimensiones de docencia). |
| `CARRERA_FACULTAD` | Dict[str, str] | 13 carreras → 8 facultades. |
| `CATEGORIA_DIMENSION_PREGRADO` | Dict[str, str] | 4 categorias: Academico, Administrativo y Bienestar, Infraestructura, Tecnologia. |
| `CATEGORIA_DIMENSION_GRADUADO` | Dict[str, str] | 6 categorias: agrega Docencia y Desarrollo Profesional. |
| `RESPUESTAS_TEXTO` | List[str] | 7 valores Zoho Survey (5 SAT + "No utilizo" + "No conozco"). |
| `ETAPA_MAP` | Dict[int, str] | Ciclos 1-2 Inicial, 3-5 Intermedio, 6-12 Avanzado. |
| `TOPICOS` | Dict[str, any] | 8 topicos con palabras, tipo, icono. **Legacy: no usado en modulos activos.** |
| `STOPWORDS` | Set[str] | ~90 stopwords en español. **Legacy: importado en nlp.py pero no usado.** |
| `EMPLEABILIDAD_CATEGORIAS` | List[str] | 4 categorias de empleado. |

## Technical Debt

- **Catalogos hardcodeados**: `CARRERA_FACULTAD`, `CATEGORIA_DIMENSION_*` y `ALIAS_DICT_MANUAL` (en aspect_extraction.py) son diccionarios hardcodeados. Cambios a la estructura facultad/carrera requieren modificacion de codigo.
- **CSV encoding fallback**: `read_csv_robust` intenta UTF-8, fallback a latin-1. No hay deteccion explicita de encoding.
- **Acoplamiento a nombres de columna Zoho**: cualquier cambio en nombres de columna de Zoho Survey rompe el pipeline. No hay paso de validacion temprana.
- **Generacion legacy**: `nps_carrera.json` y `csat_carrera.json` se siguen generando aunque son legacy.
- **No hay procesamiento incremental**: rebuilds all periods on every run, even if only one CSV changed.
- **Codigo muerto en nlp.py**: `agrupar_comentarios_por_topico` (267 lineas) importado pero no invocado.
- **Auto-download de spaCy eliminado (Fase 6)**: `aspect_extraction.py` y `sentiment_engine.py` ya NO llaman `spacy.cli.download()` en runtime. El modelo `es_core_news_sm` debe instalarse explícitamente vía `python -m spacy download es_core_news_sm` (documentado en `requirements.txt` y CI). Si no está disponible, los módulos fallan explícitamente con `OSError` en lugar de intentar descarga silenciosa.
- **Print de depuracion**: `segmentacion_nps.py:181` contiene `print()` activo.
- **Tests no ejecutados en CI**: los tests Python no corren automaticamente en PRs.
- **Idempotencia edge case**: si el CSV no tiene fechas validas, `build_json.py` usa `pd.Timestamp.now()` como fallback, rompiendo idempotencia teorica.

## AI Agent Notes

- **Idempotencia**: `build_json.py` debe producir siempre salida identica para entrada identica. Nunca modificar JSON generados manualmente — regenerar.
- **Formato de filename CSV**: debe contener `ENCUESTA` y un patron de periodo `(20\d{2}(?:-[12])?)`. El nivel se detecta por substrings: `NO DOCENTES`, `EMPLEADORES`, `EGRESADOS`, `DOCENTES`, `GRADUADOS`, `ESTUDIANTIL|ESTUDIANTES`.
- **Nuevo periodo template**: si `index.html` no existe para un periodo, `build_json.py` lo copia desde `template/` con `{{SHARED_PATH}}` reemplazado. Para actualizar todos los periodos, eliminar y regenerar.
- **`periodos.json` automatico**: el script actualiza `periodos.json` despues de procesar, marcando el ultimo periodo cronologico como `isNew: true`.
- **Cuando agregar nuevos topicos**: ya NO se usa `TOPICOS` en config.py. El motor moderno usa `ALIAS_DICT_MANUAL` en `aspect_extraction.py`. Para agregar un nuevo aspecto, editar ese diccionario.
- **Convencion de claves**: NPS en minusculas (`promotores, pasivos, detractores`); CSAT capitalizado (`Totalmente satisfecho`, etc.). Ver `CONTRACTS.md`.
- **Schemas como fuente de verdad**: antes de modificar la estructura de cualquier JSON, actualizar el schema correspondiente en `schemas/` y el validador en el mismo PR.
