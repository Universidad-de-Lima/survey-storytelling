# apps/backend

Backend API para servir datos de encuestas de satisfacción. Implementado con Fastify + TypeScript, siguiendo Clean Architecture.

## Purpose

Proveer acceso programático a los datos de encuestas mediante una API REST. Sirve datos precomputados desde archivos JSON (generados por el pipeline ETL Python) sin base de datos en runtime.

## Architecture Role

Capa de API del sistema. Traduce los JSON contracts estáticos del pipeline ETL en endpoints REST. Es un wrapper que permite al frontend React acceder a los datos sin necesidad de leer el filesystem directamente.

## Stack

| Technology | Version | Purpose                          |
| ---------- | ------- | -------------------------------- |
| Fastify    | 4.x     | HTTP server framework            |
| TypeScript | 5.4     | Type safety                      |
| Zod        | 3.x     | Runtime validation (env, params) |
| Vitest     | 1.x     | Unit testing                     |
| tsx        | 4.x     | TypeScript execution (dev)       |

## Structure

```
src/
├── config/           # Environment validation and configuration
│   ├── env.ts        # Zod schema for env vars
│   └── index.ts
├── modules/          # Feature modules (Clean Architecture)
│   ├── surveys/      # Survey data endpoints
│   │   ├── survey.routes.ts     # Route definitions
│   │   ├── survey.controller.ts # Request handling
│   │   ├── survey.service.ts    # Business logic
│   │   ├── survey.repository.ts # Data access (file I/O)
│   │   ├── survey.types.ts      # Module-specific types
│   │   └── index.ts
│   └── analytics/    # (placeholder)
├── middleware/        # Shared middleware
│   ├── cors.ts       # CORS configuration
│   ├── rate-limit.ts # Rate limiting
│   ├── error-handler.ts # Global error handler
│   └── index.ts
├── shared/           # Shared utilities
│   └── utils/
├── database/         # (placeholder for future DB)
├── app.ts            # Fastify app factory
└── server.ts         # Entry point
```

## API Endpoints

| Method | Path                                     | Description        |
| ------ | ---------------------------------------- | ------------------ |
| GET    | `/api/health`                            | Health check       |
| GET    | `/api/surveys/periods`                   | List all periods   |
| GET    | `/api/surveys/:level/:period/dashboard`  | Dashboard KPIs     |
| GET    | `/api/surveys/:level/:period/dimensions` | Dimension data     |
| GET    | `/api/surveys/:level/:period/filters`    | Filter options     |
| GET    | `/api/surveys/:level/:period/sentiment`  | Sentiment analysis |
| GET    | `/api/surveys/:level/:period/ids`        | Response counts    |
| GET    | `/api/surveys/:level/:period/nps-cross`  | NPS cross table    |
| GET    | `/api/surveys/:level/:period/csat-cross` | CSAT cross table   |

## Data Flow

```
Request → Route → Controller (validates params via Zod)
                → Service (business logic)
                → Repository (reads JSON from filesystem)
                → Response (serialized JSON)
```

## Dependencies

- **Internal**: `@survey-storytelling/shared-types`
- **Runtime**: Fastify, `@fastify/cors`, `@fastify/helmet`, `@fastify/rate-limit`, Zod
- **Data source**: JSON files in `zoho-survey/students/{level}/{period}/json/`

## Configuration

| Variable               | Default                 | Description             |
| ---------------------- | ----------------------- | ----------------------- |
| `NODE_ENV`             | `development`           | Environment             |
| `PORT`                 | `3000`                  | Server port             |
| `HOST`                 | `0.0.0.0`               | Server host             |
| `CORS_ORIGIN`          | `http://localhost:5173` | Allowed CORS origin     |
| `DATA_DIR`             | `./data`                | JSON data directory     |
| `LOG_LEVEL`            | `info`                  | Logging level           |
| `RATE_LIMIT_MAX`       | `100`                   | Max requests per window |
| `RATE_LIMIT_WINDOW_MS` | `60000`                 | Rate limit window (ms)  |

## Technical Debt

- **No database**: All data comes from static JSON files. No persistence layer exists.
- **Single source path**: Repository only looks in legacy `zoho-survey/students/` path. New data pipelines would require additional repository implementations.
- **No caching**: Each request reads from the filesystem. No in-memory caching for repeated requests.
- **Analytics module**: Empty placeholder, no functionality implemented.

## Improvement Opportunities

- Add in-memory caching layer (e.g., `node-cache` or Redis) for frequently accessed data.
- Implement streaming for large JSON files.
- Add OpenAPI/Swagger documentation via `@fastify/swagger`.
- Add request logging middleware with structured logging.
- Implement API versioning (`/api/v1/...`).

## AI Agent Notes

- Clean Architecture layers: Routes → Controller → Service → Repository. Never put business logic in routes.
- All external inputs (params, query, body, env) must be validated with Zod schemas.
- The `SurveyRepository` falls back gracefully if JSON files don't exist.
- Error handling is centralized in `middleware/error-handler.ts`. Custom errors should extend `FastifyError`.
- Add new modules in `src/modules/{name}/` following the same pattern as `surveys/`.
