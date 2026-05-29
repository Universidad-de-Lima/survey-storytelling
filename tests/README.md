# tests

Pruebas de integración y E2E del monorepo. Las pruebas unitarias viven junto al código que prueban (`*.test.ts` en cada paquete/app).

## Purpose

Proveer un nivel de testing adicional (integración y end-to-end) que complementa las pruebas unitarias existentes en cada workspace.

## Architecture Role

Capa de calidad. Garantiza que los módulos del sistema funcionen correctamente en conjunto y que los flujos críticos del usuario no se rompan.

## Structure

```
tests/
├── unit/           # Cross-package unit tests (mínimos)
├── integration/    # Integration tests (API + data)
└── e2e/            # End-to-end tests (Playwright)
```

## Test Strategy

| Level | Tool | Location | Scope |
|-------|------|----------|-------|
| **Unit** | Vitest | Co-located in each package (`*.test.ts`) | Individual functions and components |
| **Integration** | Vitest + Supertest | `tests/integration/` | API endpoints, data flow between modules |
| **E2E** | Playwright | `tests/e2e/` | Full user workflows in browser |

## Running Tests

```bash
# All tests
pnpm test

# Specific levels
pnpm test:unit
pnpm test:integration
pnpm test:e2e

# Frontend tests only
pnpm --filter @survey-storytelling/frontend test

# Backend tests only
pnpm --filter @survey-storytelling/backend test
```

## Conventions

- Test files use `.test.ts` or `.test.tsx` extension.
- Test data lives in `tests/fixtures/` (not yet created).
- Mock external dependencies (filesystem, network) at the boundary.
- Use `describe`/`it` blocks for organization.
- Follow AAA pattern: Arrange, Act, Assert.

## AI Agent Notes

- Unit tests are co-located with source code. Integration and E2E tests are centralized here.
- Backend integration tests may require running the actual Fastify app (use `buildApp()` from `@/app`).
- Frontend tests use `jsdom` environment. For E2E, Playwright requires a running dev server.
- TODO: Create `tests/fixtures/` with sample JSON data for integration tests.
