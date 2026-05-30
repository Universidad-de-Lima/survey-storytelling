# Architecture Audit — survey-storytelling

**Fecha:** 2026-05-30
**Propósito:** Documentar la limpieza de componentes over-engineered y la vuelta a una arquitectura static-first.

## Resumen

El proyecto se simplificó eliminando ~70% del código que era infraestructura agregada innecesariamente:
- React + Vite + TypeScript (apps/frontend)
- Fastify + Backend API (apps/backend)
- Paquetes workspace (packages/)
- Docker + Nginx (infrastructure/)
- Monorepo tooling (pnpm, turbo, eslint, tsconfig)
- 5 workflows de CI/CD redundantes

## Lo que se eliminó

| Componente | Archivos | Peso estimado |
|-----------|----------|--------------|
| apps/frontend (React + Vite + TS) | ~20 archivos | ~300 MB en deps |
| apps/backend (Fastify + TS) | ~15 archivos | ~100 MB en deps |
| packages/* (4 paquetes) | ~15 archivos | ~80 MB en deps |
| infrastructure/ (Docker, Nginx) | 5 archivos | ~5 MB |
| tests/ (esqueletos) | ~5 archivos | ~10 MB |
| docs/ (vacíos) | ~5 archivos | ~10 KB |
| Workflows CI/lint/tests/security | 5 archivos | — |
| pnpm-lock.yaml | 1 archivo | 181 KB |
| Config files (turbo, eslint, tsconfig, npmrc) | 8 archivos | — |
| **Total** | **~80 archivos** | **~530 MB** |

## Lo que se conservó

- zoho-survey/ (dashboard legacy funcional)
- .github/workflows/build_students.yml (ETL Python)
- .github/workflows/validate-survey-json.yml (validación)
- .github/workflows/deploy-legacy.yml (deploy GitHub Pages)
- index.html (entry point)
- README.md, ARCHITECTURE.md, CONTRACTS.md, AGENTS.md
- package.json (simplificado, solo scripts Python)

## Arquitectura actual

`
CSV → Python ETL → JSON → Vanilla JS Dashboard → GitHub Pages
`

Cero backend, cero build steps, cero dependencias runtime.
