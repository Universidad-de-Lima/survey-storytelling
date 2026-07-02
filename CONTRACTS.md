# Contratos De Datos

Este documento es la fuente canonica para los datos que fluyen por el sistema. Define entradas CSV, salidas JSON, responsabilidades por capa e invariantes de validacion.

> **Fuente de verdad:** Para tipos formales, consultar los JSON Schemas Draft-07 en `zoho-survey/scripts/schemas/*.schema.json`. Para la implementacion de generacion, `zoho-survey/scripts/build_json.py`. Este documento es la version humana del contrato; en caso de discrepancia, el schema y el ETL prevalecen.

## Entrada CSV

Los CSV fuente viven en `data/` y provienen de Zoho Survey. El ETL oficial es `zoho-survey/scripts/build_json.py`.

Columnas criticas para encuestas estudiantiles:

- `ID de respuesta`: identificador unico.
- `Net Promoter Score (de un total de 10)`: escala 0-10 para NPS.
- `¿Que carrera profesional estudias?`: base para filtros por carrera.
- `¿Que ciclo es el que cursas?`: base para filtros por ciclo.
- `La Universidad de Lima`: columna base para CSAT global.

El mapeo real de columnas debe verificarse en `zoho-survey/scripts/build_json.py` y `zoho-survey/scripts/lib/config.py` (`COLUMN_RENAME_PREGRADO`, `COLUMN_RENAME_GRADUADO`).

## Salida JSON v2.0

El pipeline genera hasta 11 archivos por periodo en `zoho-survey/students/{level}/{period}/json/`.

| Archivo | Tipo | Version | Estado | Schema |
| --- | --- | --- | --- | --- |
| `dashboard_data.json` | object | `"2.0"` | requerido | `dashboard_data.schema.json` |
| `dimensiones.json` | array | implicita | requerido | `dimensiones.schema.json` |
| `ids.json` | array | implicita | requerido | `ids.schema.json` |
| `nps_ciclo_carrera.json` | array | implicita | requerido | `nps_ciclo_carrera.schema.json` |
| `csat_ciclo_carrera.json` | array | implicita | requerido | `csat_ciclo_carrera.schema.json` |
| `filtros.json` | object | `"2.0"` | requerido | `filtros.schema.json` |
| `sentimiento.json` | object | `"3.0"` | requerido | `sentimiento.schema.json` |
| `fragmentos_nps.json` | array | implicita | requerido | sin schema formal (intermedio ETL) |
| `dataset_cualitativo.json` | object | implicita | requerido | sin schema formal (intermedio ETL) |
| `nps_carrera.json` | array | implicita | legacy opcional | sin schema formal |
| `csat_carrera.json` | array | implicita | legacy opcional | sin schema formal |

> **Nota sobre `fragmentos_nps.json` y `dataset_cualitativo.json`:** Son archivos intermedios del ETL consumidos internamente por `build_json.py` para producir `sentimiento.json`. El frontend no los consume directamente. No tienen schema formal porque son datos de trabajo, no contratos públicos.

Los archivos legacy (`nps_carrera.json`, `csat_carrera.json`) se validan solo si existen; el validador emite advertencia. El frontend los carga como fallback síncrono solo en encuestas sin ciclos (`has_ciclo=false`, ej. graduados).

## Convencion de claves NPS

El ETL produce todas las claves NPS en **minúsculas**: `promotores`, `pasivos`, `detractores`. Esta es la convencion canonica del contrato.

El frontend (`dashboard.js`) acepta ambos casings via nullish coalescing (`nps.Promotores ?? nps.promotores ?? 0`) por compatibilidad backward con periodos antiguos. **Los nuevos periodos siempre se generan en minúsculas.**

El CSAT mantiene las claves capitalizadas (`Totalmente satisfecho`, etc.) porque provienen directamente del catálogo de respuestas Zoho Survey (`RESPUESTAS_TEXTO` en `lib/config.py`).

## `dashboard_data.json`

Contiene agregados globales, hallazgos y distribuciones NPS/CSAT.

Schema: `zoho-survey/scripts/schemas/dashboard_data.schema.json` (Draft-07, `additionalProperties: false`).

Ejemplo real (undergraduate 2026-1):

```json
{
  "version": "2.0",
  "resumen": {
    "encuestas": 4239,
    "carreras": 14,
    "facultades": 7,
    "fecha_inicio": "2026-05-11",
    "fecha_fin": "2026-06-17",
    "dias": 38,
    "dias_recoleccion": 26,
    "año": 2026,
    "periodo": "2026-1",
    "nps": {
      "score": 72.61,
      "promotores": 3231,
      "pasivos": 855,
      "detractores": 153,
      "total": 4239
    },
    "csat": {
      "score": 97.85,
      "t3b": 4148,
      "total": 4239,
      "t2b": 3087,
      "t2b_pct": 72.82,
      "ponderado": 82.58079735786743
    }
  },
  "hallazgos": {
    "csat_pct": 97,
    "nps_score": 72,
    "nps_tipo": "Excelente",
    "nps_etapas": {
      "Avanzado": 69.97,
      "Inicial": 73.61,
      "Intermedio": 75.78
    },
    "tendencia": "disminuye",
    "delta": 3,
    "top_dimensiones": [
      { "name": "Perfil del egreso de la carrera", "score": 96.99 }
    ],
    "top_facultades": [
      { "name": "Facultad de Ingeniería", "score": 98.53 }
    ]
  },
  "nps": {
    "promotores": 3231,
    "pasivos": 855,
    "detractores": 153,
    "score": 72.61
  },
  "csat": {
    "Totalmente satisfecho": 1806,
    "Muy satisfecho": 1281,
    "Satisfecho": 1061,
    "Insatisfecho": 75,
    "Totalmente insatisfecho": 16,
    "No utilizo": 0,
    "No conozco": 0
  }
}
```

### Enums

- `hallazgos.nps_tipo`: `Excelente` (≥60), `Bueno` (≥30), `Regular` (≥0), `Pésimo` (<0).
- `hallazgos.tendencia`: `disminuye`, `aumenta`, `se mantiene` (comparando NPS Inicial vs Avanzado).
- `resumen.empleabilidad`: solo aparece cuando la encuesta lo soporta (graduados). Requiere `score`, `empleados`, `total`.
- `resumen.año`: entero (ej. `2026`), **no** string.
- `resumen.periodo`: string identificador del periodo (`"2026-1"` o `"2026"`).
- `resumen.csat.t2b` / `t2b_pct` / `ponderado`: indicadores extendidos de satisfacción (Top 2 Box y Promedio Ponderado). **Opcionales** por compatibilidad con periodos generados antes de su incorporación; los nuevos periodos siempre los incluyen. El frontend deriva ambos desde la distribución `csat` top-level como fallback vía `utils/metrics.js` (gemelo JS de `lib/metrics.py`). `t2b_pct` se redondea a 2 decimales (mismo patrón que `score`); `ponderado` se almacena sin redondear (precisión interna, redondeo solo al mostrar). Invariante: `t2b ≤ t3b ≤ total`. Pesos Likert: `[5,4,3,2,1]` alineados a `RESPUESTAS_TEXTO[:5]` (definidos en `lib/config.py` y `config/constants.js`).

## `dimensiones.json`

Array de resultados por facultad, carrera, ciclo, categoria y dimension.

Schema: `zoho-survey/scripts/schemas/dimensiones.schema.json`.

Cada fila incluye:

- `facultad`, `carrera`, `ciclo`
- `categoria`, `dimension`
- `t3b`, `b2b`, `total`, `t3b_pct`, `no_utilizo`, `no_conozco` (minúsculas)
- `Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho` (capitalizadas)
- `No utilizo`, `No conozco` (capitalizadas)

Invariante: debe existir al menos una fila con `total > 0`.

> **Nota:** El ETL produce ambos casings para `no_utilizo`/`No utilizo` y `no_conozco`/`No conozco` por compatibilidad. Los schemas los declaran ambos.

## `filtros.json`

Schema: `zoho-survey/scripts/schemas/filtros.schema.json`.

Claves requeridas:

- `version` (`"2.0"`)
- `has_ciclo` (booleano)
- `facultades` (lista no vacía)
- `carreras` (lista no vacía)
- `ciclos` (lista, puede ser vacía cuando `has_ciclo=false`)
- `facultad_carrera` (objeto no vacío)

Invariante: `facultad_carrera` debe mapear TODAS las facultades listadas en `facultades`.

## `ids.json`

Schema: `zoho-survey/scripts/schemas/ids.schema.json`.

Cada fila incluye:

- `facultad`
- `carrera`
- `ciclo`
- `total` (clave canónica; `count` se acepta como legacy en el validador pero el ETL siempre produce `total`)

Invariante: la suma total de `total` debe ser mayor a 0.

## `nps_ciclo_carrera.json` y `csat_ciclo_carrera.json`

Schemas: `nps_ciclo_carrera.schema.json`, `csat_ciclo_carrera.schema.json`.

Cada fila requiere `facultad`, `carrera` y `ciclo`.

NPS requiere (minúsculas, canónicas):

- `promotores`, `pasivos`, `detractores`, `score` (opcional)

CSAT requiere (capitalizadas, catálogo Zoho):

- `Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho`
- `No utilizo`, `No conozco` (opcionales)
- `score` (CSAT score calculado)

## `sentimiento.json`

Schema: `zoho-survey/scripts/schemas/sentimiento.schema.json`.

Claves requeridas a top-level (7):

- `version` (`"3.0"`)
- `resumen`
- `insights_ia`
- `topicos`
- `comentarios`
- `por_carrera`
- `por_ciclo`

`resumen` requiere:

- `total_respuestas`, `total_con_comentario`, `total_analizados`, `comentarios_invalidos`
- `distribucion_sentimiento` (objeto con `positivo`, `neutro`, `negativo`)
- `distribucion_intensidad` (objeto con `alta`, `media`, `baja`)
- `pasivos`, `detractores`, `nota` (string)

`insights_ia` requiere:

- `global` (string)
- `por_categoria_padre` (objeto con insights por categoría)

Cada tópico requiere:

- `topico`, `total_comentarios`, `positivos`, `negativos`, `neutros`

Cada comentario requiere:

- `id`, `carrera`, `facultad`, `ciclo`
- `nps_score` (0-10)
- `sentimiento` (enum: `positivo`, `negativo`, `neutro`)
- `intensidad` (1-5)
- `categoria`, `categoria_padre`
- `fragmento_original`, `fragmento_mostrar`
- `es_valido` (booleano)
- `motivo_invalidez` (string o `null` cuando `es_valido=true`)

Campos opcionales adicionales en comentarios (producidos por el ETL):

- `aspecto_normalizado`, `comentario_id_original`, `comentario_original`
- `fragmento_secuencia`, `es_fragmento`

## Responsabilidades Por Capa

| Capa | Responsabilidad |
| --- | --- |
| ETL Python (`build_json.py`) | Transformar CSV en JSON deterministico y validable contra schemas Draft-07. |
| JSON | Transportar datos precomputados, sin decisiones de layout. |
| Frontend JS | Consumir contratos y renderizar; no recalcular agregados del ETL. |
| Schemas Draft-07 | Fuente formal de tipos. El validador no debe ser mas permisivo que el schema. |
| Validador (`validate_generated_json.py`) | Aplicar schema + invariantes de negocio cruzadas. Fallar explicitamente ante cualquier rompimiento. |

## Invariantes de negocio (no expresables en JSON Schema)

- La suma de `total` en `ids.json` debe ser mayor a 0.
- `filtros.facultad_carrera` debe cubrir todas las facultades listadas en `filtros.facultades`.
- `dimensiones.json` debe contener al menos una fila con `total > 0`.
- `periodos.json` debe tener exactamente un item con `isNew: true`.
- NPS debe estar entre -100 y 100.
- CSAT debe estar entre 0 y 100.
- Los IDs de carrera en `filtros.json` deben coincidir con los usados por los JSON de NPS/CSAT.
- Los JSON generados no deben modificarse manualmente.
- Cambios incompatibles requieren actualizar el ETL, schemas, validador, frontend y este documento en el mismo PR.

## Deuda Tecnica De Contratos

- `nps_carrera.json` y `csat_carrera.json` siguen como legacy (fallback de carga síncrona en encuestas sin ciclos).
- `fragmentos_nps.json` y `dataset_cualitativo.json` no tienen schema formal porque son intermedios del ETL, no contratos públicos.
- Solo algunos objetos tienen version explicita (`"2.0"`, `"3.0"`); los arrays mantienen version implicita.
- El frontend acepta ambos casings para NPS por compatibilidad backward; los nuevos periodos siempre se generan en minúsculas.
