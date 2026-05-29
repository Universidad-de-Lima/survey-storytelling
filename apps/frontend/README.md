# apps/frontend

Frontend dashboard para visualización de encuestas de satisfacción. Implementado con Vite + React 18 + TypeScript + TailwindCSS v4.

## Purpose

Proveer una interfaz de usuario interactiva para explorar resultados de encuestas de satisfacción por periodo académico y nivel (pregrado/posgrado).

## Architecture Role

Capa de presentación del sistema. Consume datos de la API REST (`apps/backend/`) o directamente de archivos JSON estáticos para renderizado offline. Sigue una arquitectura feature-based.

## Stack

| Technology     | Version | Purpose                   |
| -------------- | ------- | ------------------------- |
| Vite           | 5.x     | Build tool and dev server |
| React          | 18.3    | UI framework              |
| TypeScript     | 5.4     | Type safety               |
| TailwindCSS    | 4.x     | Utility-first CSS         |
| TanStack Query | 5.x     | Server state management   |
| React Router   | 6.x     | Client-side routing       |
| Zustand        | 4.x     | Client state management   |
| Zod            | 3.x     | Runtime validation        |
| Vitest         | 1.x     | Unit testing              |

## Structure

```
src/
├── app/              # App shell: providers, router, layouts
│   ├── App.tsx
│   ├── providers/
│   ├── router/
│   └── layouts/
├── features/         # Feature modules (autonomous)
│   ├── surveys/      # Survey list and period selection
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── state/
│   │   ├── types/
│   │   └── pages/
│   └── dashboard/    # Dashboard visualization
│       ├── components/
│       ├── hooks/
│       ├── services/
│       ├── state/
│       ├── types/
│       ├── utils/
│       └── pages/
├── shared/           # Shared utilities
│   ├── components/   # Reusable UI components
│   ├── hooks/        # Shared hooks
│   ├── services/     # API client configuration
│   ├── utils/        # Helper functions
│   ├── validators/   # Zod schemas
│   └── types/        # Shared type definitions
├── assets/           # Static assets
├── styles/           # Global styles and Tailwind config
├── test/             # Test setup
├── main.tsx          # Entry point
└── vite-env.d.ts     # Vite type declarations
```

## Key Files

| File                                                        | Responsibility                       |
| ----------------------------------------------------------- | ------------------------------------ |
| `src/main.tsx`                                              | Entry point, React root render       |
| `src/app/App.tsx`                                           | Root component, provider composition |
| `src/app/router/app-router.tsx`                             | Route definitions                    |
| `src/app/providers/app-provider.tsx`                        | QueryClient setup                    |
| `src/features/surveys/pages/survey-list-page.tsx`           | Period selection page                |
| `src/features/dashboard/pages/dashboard-page.tsx`           | Dashboard container                  |
| `src/features/dashboard/components/dashboard-executive.tsx` | Ejecutivo section (KPIs, NPS/CSAT)   |
| `src/styles/index.css`                                      | Tailwind imports + design tokens     |

## Data Flow

```
User navigates to /
  → SurveyListPage fetches /api/surveys/periods
  → User selects a period
  → Navigate to /{level}/{period}
    → DashboardPage fetches /api/surveys/{level}/{period}/dashboard
    → Renders 4 sections:
      1. Ejecutivo (KPIs, NPS/CSAT bars)
      2. Operativo (Top 3 categories, radar)
      3. Detallado (Tables, cross-analysis)
      4. Cualitativo (Sentiment analysis)
```

## Dependencies

- **Internal**: `@survey-storytelling/shared-types`, `@survey-storytelling/ui`
- **Runtime**: React, TanStack Query, React Router, Zustand, Zod
- **Dev**: Vite, TypeScript, TailwindCSS, Vitest, Testing Library

## Configuration

Environment variables (via `VITE_` prefix):

| Variable              | Default         | Description            |
| --------------------- | --------------- | ---------------------- |
| `VITE_API_URL`        | `/api`          | Backend API base URL   |
| `VITE_DEFAULT_PERIOD` | `latest`        | Default period to load |
| `VITE_DEFAULT_LEVEL`  | `undergraduate` | Default academic level |

## Technical Debt

- **Skeleton features**: Dashboard sections Operativo, Detallado, Cualitativo are not fully implemented yet (only Ejecutivo is complete).
- **No tests for survey-list-page**: Only DashboardExecutive has unit tests.
- **No error boundaries**: React error boundaries not implemented.
- **No loading skeletons**: Only spinner for loading states.

## Improvement Opportunities

- Complete remaining dashboard sections (Operativo, Detallado, Cualitativo).
- Add React error boundaries for graceful error handling.
- Implement lazy loading for dashboard sections.
- Add E2E tests with Playwright.
- Implement code splitting per feature route.
- Add PWA support for offline access to static data.

## AI Agent Notes

- All feature directories are autonomous: they contain their own components, hooks, services, state, types, and utils.
- Absolute imports use `@/` prefix (e.g., `@/features/dashboard/...`).
- New features should follow the same pattern: `features/{name}/{layer}/`.
- Never import across feature boundaries directly; use shared utilities via `shared/`.
- Custom hooks for data fetching should use TanStack Query (`useQuery`/`useMutation`).
- Client state should use Zustand stores in `features/{name}/state/`.
- Module CSS is not used; styling is done via TailwindCSS utility classes.
