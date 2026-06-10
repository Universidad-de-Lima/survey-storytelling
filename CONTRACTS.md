# Contratos De Datos

Este documento es la fuente canonica para los datos que fluyen por el sistema. Define entradas CSV, salidas JSON, responsabilidades por capa e invariantes de validacion.

## Entrada CSV

Los CSV fuente viven en `data/` y provienen de Zoho Survey. El ETL oficial es `zoho-survey/scripts/build_json.py`.

Columnas criticas para encuestas estudiantiles:

- `ID de respuesta`: identificador unico.
- `Net Promoter Score (de un total de 10)`: escala 0-10 para NPS.
- `¿Que carrera profesional estudias?`: base para filtros por carrera.
- `¿Que ciclo es el que cursas?`: base para filtros por ciclo.

El mapeo real de columnas debe verificarse en `zoho-survey/scripts/build_json.py` y `zoho-survey/scripts/lib/config.py`.

## Salida JSON v2.0

El pipeline genera hasta 9 archivos por periodo en `zoho-survey/students/{level}/{period}/json/`.

| Archivo | Tipo | Version | Estado |
| --- | --- | --- | --- |
| `dashboard_data.json` | object | `"2.0"` | requerido |
| `dimensiones.json` | array | implicita | requerido |
| `ids.json` | array | implicita | requerido |
| `nps_ciclo_carrera.json` | array | implicita | requerido |
| `csat_ciclo_carrera.json` | array | implicita | requerido |
| `filtros.json` | object | `"2.0"` | requerido |
| `sentimiento.json` | object | `"2.0"` | requerido |
| `nps_carrera.json` | array | implicita | legacy opcional |
| `csat_carrera.json` | array | implicita | legacy opcional |

Los archivos legacy se validan si existen, pero no deben asumirse como entrada principal del frontend.

## `dashboard_data.json`

Contiene agregados globales, hallazgos y distribuciones NPS/CSAT.

Schema: `zoho-survey/scripts/schemas/dashboard_data.schema.json`.

Ejemplo minimo:

```json
{
  "version": "2.0",
  "resumen": {
    "encuestas": 3998,
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-06-01",
    "año": "2026-1",
    "nps": { "score": 65.4 },
    "csat": { "score": 92.1 }
  },
  "hallazgos": {
    "csat_pct": 92.1,
    "nps_score": 65.4,
    "nps_tipo": "positivo",
    "nps_etapas": [],
    "tendencia": "estable",
    "delta": 0
  },
  "nps": {
    "Promotores": 2669,
    "Pasivos": 1111,
    "Detractores": 218
  },
  "csat": {
    "Totalmente satisfecho": 1626,
    "Muy satisfecho": 1135,
    "Satisfecho": 800,
    "Insatisfecho": 300,
    "Totalmente insatisfecho": 137
  }
}
```

`resumen.empleabilidad` solo aparece cuando la encuesta lo soporta, por ejemplo en graduados. Debe contener `score`, `empleados` y `total`.

## `dimensiones.json`

Array de resultados por facultad, carrera, ciclo, categoria y dimension.

Cada fila debe incluir:

- `facultad`, `carrera`, `ciclo`
- `categoria`, `dimension`
- `t3b`, `b2b`, `total`, `t3b_pct`, `no_utilizo`, `no_conozco`
- `Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho`
- `No utilizo`, `No conozco`

Debe existir al menos una fila con `total > 0`.

## `filtros.json`

Schema: `zoho-survey/scripts/schemas/filtros.schema.json`.

Claves requeridas:

- `version`
- `has_ciclo`
- `facultades`
- `carreras`
- `ciclos`
- `facultad_carrera`

`facultades` y `carreras` deben ser listas no vacias. `ciclos` puede ser lista vacia cuando `has_ciclo=false`.

## `ids.json`

Cada fila debe incluir:

- `facultad`
- `carrera`
- `ciclo`
- `count`

La suma total de `count` debe ser mayor a 0.

## `sentimiento.json`

Schema: `zoho-survey/scripts/schemas/sentimiento.schema.json`.

Claves requeridas:

- `version`
- `resumen`
- `topicos`
- `por_carrera`
- `por_ciclo`

`resumen` requiere:

- `total_con_comentario`
- `total_analizados`
- `pasivos`
- `detractores`
- `nota`

Cada topico requiere:

- `topico`
- `tipo` (`negativo`, `mejora` o `positivo`)
- `icono`
- `total_comentarios`
- `por_facultad`
- `por_carrera`
- `por_ciclo`
- `frases_representativas`

## `nps_ciclo_carrera.json` Y `csat_ciclo_carrera.json`

Cada fila requiere `facultad`, `carrera` y `ciclo`.

NPS requiere:

- `Promotores`
- `Pasivos`
- `Detractores`

CSAT requiere:

- `Totalmente satisfecho`
- `Muy satisfecho`
- `Satisfecho`
- `Insatisfecho`
- `Totalmente insatisfecho`

## Responsabilidades Por Capa

| Capa | Responsabilidad |
| --- | --- |
| ETL Python | Transformar CSV en JSON deterministico y validable. |
| JSON | Transportar datos precomputados, sin decisiones de layout. |
| Frontend JS | Consumir contratos y renderizar; no recalcular agregados del ETL. |
| Validador | Fallar explicitamente cuando una salida rompe estructura o invariantes. |

## Invariantes

- NPS debe estar entre -100 y 100.
- CSAT debe estar entre 0 y 100.
- Los IDs de carrera en `filtros.json` deben coincidir con los usados por los JSON de NPS/CSAT.
- Los JSON generados no deben modificarse manualmente.
- Cambios incompatibles requieren actualizar el ETL, validadores, frontend y este documento en el mismo PR.

## Deuda Tecnica De Contratos

- `nps_carrera.json` y `csat_carrera.json` siguen como legacy.
- `nps_ciclo_carrera.json` y `csat_ciclo_carrera.json` contienen datos combinados por carrera y ciclo; consolidarlos solo tendria sentido si aparece un problema real de latencia o mantenimiento.
- Solo algunos objetos tienen version explicita `"2.0"`; los arrays mantienen version implicita.
