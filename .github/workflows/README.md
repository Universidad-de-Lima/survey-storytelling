# .github/workflows

Pipeline de CI/CD para el proyecto survey-storytelling. Incluye workflows para el pipeline ETL (Python), CI del monorepo (TypeScript), testing, linting, deploy y seguridad.

## Purpose

Automatizar todo el ciclo de vida del proyecto: generación de datos ETL, validación de contratos JSON, CI del monorepo TypeScript, deploy a GitHub Pages, y auditorías de seguridad.

## Architecture Role

Capa de automatización e integración continua. Workflows legacy (ETL Python) coexisten con los nuevos workflows del monorepo moderno (TypeScript/React/Fastify).

## Workflows

### Legacy ETL

#### `build_students.yml` — Auto-build Survey JSON
**Trigger**: Push a `zoho-survey/students/data/**` o `zoho-survey/students/scripts/**`. También `workflow_dispatch`.
**Runs**: Python 3.11 + pandas
**Steps**: Checkout → Setup Python → Install pandas → Run `build_json.py` → Commit JSON
**Risk**: Auto-commit sin validación post-build.

#### `validate-survey-json.yml` — Validate Survey JSON
**Trigger**: PR a `zoho-survey/students/**`. Push a `main`.
**Runs**: Python 3.11
**Steps**: Checkout → Setup Python → Run `validate_generated_json.py undergraduate`
**Nota**: Solo valida `undergraduate`.

### Modern CI/CD

#### `ci.yml` — Continuous Integration
**Trigger**: Push/PR a `main` (excluye `zoho-survey/**` y `**.md`)
**Runs**: pnpm + Node 20
**Steps**: Install → Type Check → Lint → Unit Tests → Build
**Concurrency**: Cancel-in-progress para PRs.

#### `tests.yml` — Test Suite
**Trigger**: Push/PR a `main` cuando cambian `apps/**`, `packages/**`, `tests/**`
**Jobs**: Unit tests + Integration tests
**Coverage**: Upload de coverage como artifact.

#### `lint.yml` — Lint & Format
**Trigger**: Push/PR a `main`
**Jobs**: ESLint + Prettier (paralelos)

#### `deploy-frontend.yml` — GitHub Pages Deploy
**Trigger**: Push a `main` con cambios en `apps/frontend/**`, `packages/ui/**`, `packages/shared-types/**`
**Runs**: Build → Upload Pages Artifact → Deploy to GitHub Pages
**Environment**: `github-pages`

#### `security.yml` — Security Scan
**Trigger**: Semanal (lunes 06:00) + push/PR a `main`
**Jobs**: Dependency audit (pnpm audit) + Gitleaks secrets detection

## Technical Debt

- **Solo undergraduate validado**: `validate-survey-json.yml` solo corre validación para pregrado. Posgrado no está cubierto.
- **Sin validación post-build**: `build_students.yml` no ejecuta el validador después de generar JSON, solo hace commit.
- **Commit sin control**: El bot `survey-bot` commitea cambios sin PR ni revisión. Puede introducir cambios no deseados.
- **Sin notificación de fallos**: No hay configuración de alertas si el build o validación fallan.
- **Sin cache de pip**: Cada ejecución reinstala pandas, aumentando el tiempo de ejecución.

## Improvement Opportunities

- **Post-build validation**: Add `validate_generated_json.py` step in `build_students.yml` before commit to prevent committing invalid JSON.
- **Path scoping**: Replace `git add .` with specific path patterns to avoid committing unintended changes.
- **Postgraduate validation**: Add `validate_generated_json.py postgraduate` step in `validate-survey-json.yml`.
- **pip cache**: Add `actions/cache` for pip packages to reduce workflow execution time.
- **Commit signing**: Configure the bot to sign commits for better traceability.
- **Failure notifications**: Add GitHub commit status checks or Slack/Discord webhook notifications on failure.
- **PR auto-label**: Add step to label PRs that modify contracts as `data-change` or `schema-change`.

## AI Agent Notes

- Ambos workflows usan `ubuntu-latest` y Python 3.11.
- El build workflow usa `git add .` desde `zoho-survey/students`, lo que incluye cualquier cambio no deseado en el directorio.
- El patrón de paths en `on.push.paths` debe actualizarse si se modifican las rutas de los scripts o datos.
- Para debuggear: `workflow_dispatch` permite ejecutar `build_students.yml` manualmente desde la UI de GitHub.
- El workflow `build_students.yml` solo se dispara con pushes a `data/**` o `scripts/**`. Los cambios en `template/` no disparan build.
- `validate-survey-json.yml` se ejecuta en PRs y pushes a `main` que afecten `students/**`. No cubre cambios en `shared/`.
