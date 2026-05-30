# .github/workflows

Pipeline de CI/CD para survey-storytelling. Tres workflows esenciales para un sitio estático en GitHub Pages.

## Purpose

Automatizar la generación de datos JSON (ETL Python), validar contratos y desplegar el dashboard estático a GitHub Pages.

## Architecture Role

Capa de automatización mínima. Sin TypeScript, sin React, sin testing JS — solo Python + GitHub Pages.

## Workflows

### uild_students.yml — Auto-build Survey JSON
**Trigger**: Push a zoho-survey/students/data/** o zoho-survey/students/scripts/**. También workflow_dispatch.
**Runs**: Python 3.11 + pandas
**Steps**: Checkout → Setup Python → Install pandas → Run uild_json.py → Commit JSON
**Risk**: Auto-commit sin validación post-build.

### alidate-survey-json.yml — Validate Survey JSON
**Trigger**: PR a zoho-survey/students/**. Push a main.
**Runs**: Python 3.11
**Steps**: Checkout → Setup Python → Run alidate_generated_json.py undergraduate
**Nota**: Solo valida undergraduate.

### deploy-legacy.yml — Deploy to GitHub Pages
**Trigger**: Push a main con cambios en zoho-survey/** o index.html. También workflow_dispatch.
**Runs**: actions/checkout → configure-pages → upload-pages-artifact → deploy-pages
**Output**: Sirve la raíz del repositorio como sitio estático en GitHub Pages.

## Technical Debt

- **Solo undergraduate validado**: alidate-survey-json.yml solo corre validación para pregrado.
- **Sin validación post-build**: uild_students.yml no ejecuta el validador antes del commit.
- **Commit sin control**: El bot survey-bot commitea cambios sin PR ni revisión.
- **Sin cache de pip**: Cada ejecución reinstala pandas.

## AI Agent Notes

- Los únicos workflows activos son: uild_students.yml, alidate-survey-json.yml, deploy-legacy.yml.
- deploy-legacy.yml despliega la raíz del repositorio en GitHub Pages usando ctions/deploy-pages.
- El resto de workflows (CI, tests, lint, security) fueron eliminados porque el proyecto no usa TypeScript/React.
