# Architecture

Documentos de arquitectura del sistema.

## Contents

| File            | Description                       |
| --------------- | --------------------------------- |
| `README.md`     | This index                        |
| `../decisions/` | Decisiones arquitectónicas (ADRs) |

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    survey-storytelling                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                    │
│  │   Frontend    │    │   Backend    │                    │
│  │ (Vite+React)  │◄──►│  (Fastify)   │                    │
│  │   :5173      │    │   :3000      │                    │
│  └──────────────┘    └──────┬───────┘                    │
│                             │                            │
│                    ┌────────▼────────┐                   │
│                    │  JSON Contracts │                   │
│                    │ (zoho-survey/)  │                   │
│                    └────────▲────────┘                   │
│                             │                            │
│                    ┌────────┴────────┐                   │
│                    │  ETL Pipeline   │                   │
│                    │ (Python/pandas) │                   │
│                    └────────▲────────┘                   │
│                             │                            │
│                    ┌────────┴────────┐                   │
│                    │  CSV (Zoho)     │                   │
│                    └─────────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

1. **Static-first**: The system remains deployable as static files (GitHub Pages). The backend is optional and provides API access to the same JSON data.
2. **Monorepo**: pnpm workspaces + Turborepo for dependency management and build orchestration.
3. **Feature-based frontend**: Each UI feature is self-contained with its own components, hooks, services, and state.
4. **Clean architecture backend**: Routes → Controller → Service → Repository layer separation.
5. **Python ETL preserved**: The core data transformation pipeline remains in Python. No rewrite.
