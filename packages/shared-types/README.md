# packages/shared-types

TypeScript type definitions and constants shared across all packages and apps in the monorepo.

## Purpose

Define los contratos de datos del sistema en un solo lugar, garantizando type safety entre frontend, backend y paquetes compartidos. Refleja los esquemas JSON documentados en `JSON_SCHEMA.md`.

## Architecture Role

Capa de contratos. Es el único punto de definición de tipos para todos los datos que fluyen entre el pipeline ETL (Python → JSON), la API (Fastify) y el frontend (React).

## Key Types

| Type             | Source File               | Description                                        |
| ---------------- | ------------------------- | -------------------------------------------------- |
| `DashboardData`  | `dashboard_data.json`     | KPIs agregados, hallazgos, distribuciones NPS/CSAT |
| `DimensionRow`   | `dimensiones.json`        | Satisfacción por facultad/carrera/ciclo/dimensión  |
| `FilterOptions`  | `filtros.json`            | Opciones de filtro: facultades, carreras, ciclos   |
| `ResponseCount`  | `ids.json`                | Conteos de respuestas                              |
| `NpsCrossRow`    | `nps_ciclo_carrera.json`  | NPS cruzado por carrera y ciclo                    |
| `CsatCrossRow`   | `csat_ciclo_carrera.json` | CSAT cruzado por carrera y ciclo                   |
| `SentimentData`  | `sentimiento.json`        | Análisis semántico de comentarios                  |
| `PeriodInfo`     | `periodos.json`           | Información de periodo académico                   |
| `FilterState`    | —                         | Estado de filtros en el frontend                   |
| `ApiResponse<T>` | —                         | Envoltorio genérico de respuesta API               |

## Key Constants

| Constant            | Value                            | Description                         |
| ------------------- | -------------------------------- | ----------------------------------- |
| `SATISFACTION_KEYS` | `['Totalmente satisfecho', ...]` | Escala de 5 niveles de satisfacción |
| `NPS_THRESHOLDS`    | `{ PROMOTOR_MIN: 9, ... }`       | Umbrales de clasificación NPS       |
| `META_NPS`          | `50`                             | Target NPS para KPIs                |
| `META_CSAT`         | `93`                             | Target CSAT para KPIs               |

## Dependencies

- **Runtime**: None (pure TypeScript types)
- **Dev**: TypeScript

## Usage

```typescript
import type { DashboardData, FilterOptions } from '@survey-storytelling/shared-types';
import { META_NPS, META_CSAT } from '@survey-storytelling/shared-types';
```

## AI Agent Notes

- This package contains **no runtime code** — only type definitions and constants.
- Types must stay synchronized with the JSON schemas in `zoho-survey/students/JSON_SCHEMA.md`.
- Adding new JSON contracts requires adding corresponding types here first.
- The `ApiResponse<T>` generic is the standard API response wrapper used by the backend.
