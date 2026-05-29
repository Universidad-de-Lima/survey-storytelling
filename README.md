# survey-storytelling

Monorepo del sistema de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte datos CSV exportados de Zoho Survey en un dashboard interactivo, con frontend moderno (React/TypeScript) y API backend (Fastify).

## Purpose

Transformar datos crudos de encuestas de satisfacción (CSV) en dashboards visuales interactivos. El sistema ofrece dos modos de operación:
1. **Modo estático** (legacy): SPA vanilla JS sin backend, desplegable en GitHub Pages
2. **Modo API** (moderno): Frontend React + Backend Fastify con acceso programático a datos

## Architecture Role

Monorepo pnpm + Turborepo. Pipeline ETL (Python) → JSON contracts → API (Fastify) → Frontend (React).

```
CSV (Zoho Survey) → [build_json.py] → JSON contracts → [Fastify API] → [React Frontend]
                          ↓                  │
              [validate_generated_json.py]    └→ [Vanilla JS Dashboard] (legacy, GitHub Pages)
```

## Project Structure

```
survey-storytelling/
├── apps/
│   ├── frontend/          # Vite + React + TypeScript + TailwindCSS
│   └── backend/           # Fastify + TypeScript API
├── packages/
│   ├── shared-types/      # TypeScript interfaces & constants
│   ├── ui/                # Shared React components
│   ├── eslint-config/     # Shared ESLint configuration
│   └── tsconfig/          # Shared TypeScript configurations
├── scripts/               # Python ETL pipeline (reference)
├── zoho-survey/           # Legacy static dashboard & data (preserved)
├── docs/                  # Architecture, API, decisions
├── infrastructure/        # Docker Compose, Nginx, Dockerfiles
├── tests/                 # Integration & E2E tests
├── .github/workflows/     # CI/CD pipelines
├── .vscode/               # Editor config & AI agents setup
├── package.json           # Root workspace config
├── pnpm-workspace.yaml    # Workspace definition
└── turbo.json             # Build orchestration
```

## System Layers

| Layer | Path | Technology | Responsibility |
|-------|------|------------|----------------|
| **Source** | `zoho-survey/students/data/` | CSV (UTF-8/Latin-1) | Raw survey exports from Zoho Survey |
| **ETL** | `zoho-survey/students/scripts/` | Python 3.11 + pandas | Transform, aggregate, topic analysis |
| **Contracts** | `zoho-survey/students/{level}/{period}/json/` | JSON | Precomputed data contracts |
| **API** | `apps/backend/` | Fastify + TypeScript | Serve JSON data via REST endpoints |
| **Frontend** | `apps/frontend/` | Vite + React + TypeScript + TailwindCSS | Interactive dashboard SPA |
| **Legacy Dashboard** | `zoho-survey/` | Vanilla JS (ES6) | Original static dashboard (preserved) |
| **CI/CD** | `.github/workflows/` | GitHub Actions | ETL build, CI, tests, deploy |

## Key Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| ETL Pipeline | `zoho-survey/students/scripts/build_json.py` | CSV → JSON transformation, NPS/CSAT calculation, topic analysis |
| JSON Validator | `zoho-survey/students/scripts/validate_generated_json.py` | Contract compliance verification |
| Dashboard SPA | `zoho-survey/shared/js/dashboard.js` | 4-section interactive visualization (Ejecutivo, Operativo, Detallado, Cualitativo) |
| Period Loader | `zoho-survey/shared/js/loader.js` | Multi-period navigation with pills/select |
| HTML Template | `zoho-survey/students/template/index.html` | Period dashboard scaffold, copied by ETL |

## Data Flow

### Build Time (Offline)
1. **Input**: CSV from Zoho Survey placed in `data/` directory
2. **ETL**: `build_json.py` reads CSVs matching `ENCUESTA*` pattern, extracts period from filename regex `(20\d{2}-[12])`
3. **Generation**: Produces ~12 JSON files per period + `periodos.json` per level, copies `template/index.html` if missing
4. **Validation**: CI runs `validate_generated_json.py` on PR/push to main

### Runtime (Browser)
1. `loader.js` fetches `periodos.json`, renders period pills/select
2. User selects period → `loader.js` sets `iframe.src`
3. Period `index.html` loads `dashboard.js`
4. `dashboard.js` fetches 7 JSON files from `./json/` directory
5. 4-section dashboard renders with all data

## Execution Flow

```
User opens {level}/index.html
  → loader.js initializes (splash screen → main wrapper)
  → Fetches periodos.json → renders pills (desktop) / select (mobile)
  → Loads default (latest) period in #dashboard-frame iframe
    → iframe: period/index.html loads dashboard.js
      → dashboard.js fetches ./json/*.json (7 active files)
      → Cache object stores all fetched data
      → Renders 4 sections sequentially:
        1. Ejecutivo: KPIs, NPS/CSAT bars, hallazgos
        2. Operativo: Top 3 category bars, radar chart, fortalezas
        3. Detallado: Question table, career detail, service visibility
        4. Cualitativo: Sentiment KPIs, topic analysis, career breakdown
      → Filter system initializes (6 groups, cascade logic)
      → User interacts with filters → filtrarDatos() → updateCascade() → re-render section
```

## Dependencies

- **Python**: 3.11+, `pandas` (CSV processing)
- **Frontend**: Zero external runtime dependencies (vanilla JS, CSS custom properties)
- **CI**: GitHub Actions (ubuntu-latest)
- **Deployment**: GitHub Pages compatible (fully static)

## Configuration

- `periodos.json` per level — auto-generated by ETL, defines period list with `isNew` flag
- `template/index.html` — copied by ETL for new periods, must maintain DOM ID contracts
- Constants in `dashboard.js`: `META_NPS = 50`, `META_CSAT = 93`, `CARRERAS_12_CICLOS`, cycle range rules

## Technical Debt

- **CSV column coupling**: `build_json.py` depends on exact Zoho Survey column names in `COLUMN_RENAME`. Zoho changes break pipeline silently.
- **Hardcoded career-cycle logic**: `CARRERAS_12_CICLOS` and `FACULTADES_12_CICLOS` arrays in `dashboard.js` should be configurable via `filtros.json`.
- **Redundant JSON files**: Legacy files (`nps.json`, `csat.json`, `nps_carrera.json`, `csat_carrera.json`, `resumen.json`) still generated but not consumed by dashboard.
- **Postgraduate placeholder**: `postgraduate/` contains only placeholder `.txt` files; ETL expects `POSGRADO` CSV naming but none provided.
- **dashboard.js monolithic**: 1200+ line single file with mixed concerns (fetch, render, events, formatting).
- **No lazy loading**: 7 JSON files fetched upfront regardless of user navigation within sections.
- **CI without post-build validation**: `build_students.yml` commits generated JSON without running the validator first.

## Improvement Opportunities

- Migrate career-cycle rules from `dashboard.js` constants to `filtros.json` configuration.
- Remove legacy JSON file generation from `build_json.py` once confirmed no consumers exist.
- Add post-build validation step in `build_students.yml` before auto-commit.
- Modularize `dashboard.js` into separate files (data, render, filters, utils).
- Add CSV pre-validation script for column presence before ETL execution.
- Extend CI validation to cover `postgraduate` level.
- Replace PNG assets with SVG for better scalability and theming.

## AI Agent Notes

- **Read before editing**: `AGENTS.md` (project conventions), `ARCHITECTURE.md` (system architecture), `CONTRACTS.md` (data contracts), `JSON_SCHEMA.md` (JSON validation rules), `FILTER_LOGIC.md` (filter cascade logic).
- **ETL idempotency**: `build_json.py` must remain idempotent. Never manually edit generated JSON.
- **DOM ID contracts**: `dashboard.js` consumes specific DOM IDs from `index.html`. Changing them without updating both files breaks the dashboard.
- **Period pattern**: New periods follow `{YYYY}-{S}` where `S` is semester (1 or 2). Period detection via regex `(20\d{2}-[12])` in filename.
- **Validation command**: `python zoho-survey/students/scripts/validate_generated_json.py undergraduate` (or `postgraduate`).
- **CI trigger**: Push to `zoho-survey/students/data/**` or `zoho-survey/students/scripts/**` triggers auto-build and commit.
- **Architecture documents**: `ARCHITECTURE.md` (Mermaid diagrams, component map), `CONTRACTS.md` (data schemas, invariants), `AGENTS.md` (coding conventions).
- **Documentation index**: Each subdirectory has a README.md with local scope, architecture role, and AI agent notes. Follow the chain: `README.md` → `zoho-survey/README.md` → submodule READMEs.
