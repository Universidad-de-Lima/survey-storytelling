# AI Agents Configuration — survey-storytelling

This file defines rules and conventions for AI coding agents working on this project.

## Architecture

- **Monorepo** with pnpm workspaces + Turborepo
- **Frontend**: Vite + React + TypeScript + TailwindCSS in `apps/frontend/`
- **Backend**: Fastify + TypeScript in `apps/backend/`
- **ETL Pipeline**: Python scripts in `scripts/` directory
- **Static data**: Generated JSON contracts in `apps/frontend/public/data/`

## Project Conventions

### File Naming
- React components: PascalCase (`kpi-card.tsx` → `KpiCard`)
- Utility files: kebab-case (`format-date.ts`)
- Constants: UPPER_SNAKE_CASE
- Variables/functions: camelCase
- Types/interfaces: PascalCase with descriptive names

### Imports
- Use absolute imports with `@/` prefix for app code
- Import shared types from `@survey-storytelling/shared-types`
- Import UI components from `@survey-storytelling/ui`
- NO deep relative imports (`../../../shared/`)

### TypeScript Rules
- `strict: true` — never disable
- No `any` — use `unknown` and type guards if needed
- Explicit return types on public functions
- All external inputs must be validated with Zod

### Frontend Architecture (Feature-Based)
Each feature in `apps/frontend/src/features/{feature}/`:
- `components/` — UI components
- `hooks/` — React hooks (state, data fetching)
- `services/` — API calls
- `state/` — Zustand stores
- `types/` — Feature-specific types
- `utils/` — Feature-specific utilities
- `pages/` — Page components

### Backend Architecture (Clean Architecture)
Each module in `apps/backend/src/modules/{module}/`:
- `{module}.routes.ts` — Route definitions
- `{module}.controller.ts` — Request handling
- `{module}.service.ts` — Business logic
- `{module}.repository.ts` — Data access
- `{module}.types.ts` — Module-specific types
- `{module}.test.ts` — Unit tests

### ETL Pipeline (Python)
- `scripts/build_json.py` — Single source of truth for JSON generation
- `scripts/validate_generated_json.py` — Contract validation
- Never manually edit generated JSON files
- ETL must remain idempotent

## Critical Rules for AI Agents

1. **Read before editing**: Always read `docs/architecture/`, `docs/api/`, and `docs/decisions/` before making architectural changes
2. **DOM ID contracts**: If modifying HTML templates, verify `dashboard.js` DOM ID contracts in `JSON_SCHEMA.md`
3. **Never break static deployment**: The project must remain deployable as static files (GitHub Pages compatible)
4. **Preserve Python ETL**: The ETL pipeline is the core data transformation — never rewrite it without explicit approval
5. **Incremental changes**: Prefer small, focused commits over large rewrites
6. **Test before commit**: Run `pnpm test` and `pnpm type-check` before committing

## Sensitive Points

- `scripts/build_json.py` `COLUMN_RENAME` dictionary — changes in Zoho Survey column names break pipeline
- `apps/frontend/src/features/dashboard/` — filter cascade logic is complex; study before modifying
- `apps/backend/src/config/env.ts` — environment variables must be validated with Zod
- `apps/frontend/public/data/` — auto-generated JSON; never edit manually
