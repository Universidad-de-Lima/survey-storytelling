# ADR-0001: Eliminación de testsprite_tests/

**Fecha:** 2026-07-08
**Estado:** Aprobado
**Decisor:** Equipo de desarrollo

## Contexto

El repositorio `survey-storytelling` contenía una carpeta `testsprite_tests/` que
era un overlay externo generado por la herramienta TestSprite. Esta carpeta incluía:

- `package.json` aislado con dependencia `playwright ^1.61.1`
- `run_tests.mjs` (13 de 22 TCs implementados)
- `standard_prd.json` (PRD autogenerado por TestSprite)
- `testsprite_frontend_test_plan.json` (22 TCs)
- `tmp/config.json` con **API key de DeepSeek expuesta en texto plano**
- `tmp/mcp.log` con metadatos del entorno de desarrollo
- `tmp/code_summary.yaml` con análisis estático autogenerado
- `node_modules/` (18 MB) commiteado accidentalmente
- `package-lock.json` commiteado

### Problemas detectados

1. **Seguridad crítica**: API key de DeepSeek expuesta en `tmp/config.json`
2. **Repositorio inflado**: 18 MB de `node_modules/` commiteados
3. **Metadatos expuestos**: rutas Windows absolutas, puertos, logs MCP en `tmp/`
4. **No integrado al CI**: `testsprite_tests/` no era referenciado por ningún
   workflow de GitHub Actions del proyecto principal
5. **No es parte del core**: TestSprite es una herramienta externa de QA;
   sus artefactos no deben vivir en el repositorio del producto
6. **`.gitignore` defectuoso**: el patrón `testsprite_tests\tmp\config.json`
   (con backslash Windows) no funcionaba en sistemas Unix

## Decisión

**Eliminar completamente la carpeta `testsprite_tests/` del repositorio.**

### Justificación

- TestSprite es una herramienta de QA externa, no parte del sistema `survey-storytelling`.
- Los tests E2E (si se necesitan en el futuro) deben vivir en `tests/e2e/` nativo,
  integrados al CI del proyecto, no en un overlay aislado.
- La API key expuesta constituye una vulnerabilidad crítica que requiere rotación
  inmediata (ver CC-01 del plan de mejora).
- Los 18 MB de `node_modules/` contaminan el repositorio innecesariamente.

### Acciones tomadas

1. `testsprite_tests/` eliminada del repositorio (CC-09)
2. `.gitignore` actualizado con `testsprite_tests/` como patrón defensivo (CC-02)
3. API key de DeepSeek rotada (CC-01 — requiere acción manual del equipo)
4. Este ADR documenta la decisión para trazabilidad

## Consecuencias

### Positivas

- **Repositorio más ligero**: -18 MB de `node_modules/`
- **Seguridad mejorada**: API key expuesta eliminada (aunque requiere rotación externa)
- **Claridad de fronteras**: el repositorio solo contiene código del producto
- **`.gitignore` efectivo**: patrón Unix funciona en todos los SO

### Negativas

- **Pérdida de 22 TCs**: los casos de prueba de TestSprite se pierden. Si se
  necesitan tests E2E en el futuro, deben re-implementarse nativamente (ver
  mejora TEST-13 del plan: "Añadir tests E2E con Playwright en CI principal").
- **Pérdida de PRD autogenerado**: `standard_prd.json` se pierde. El PRD del
  proyecto vive en la documentación existente (`README.md`, `ARCHITECTURE.md`,
  `CONTRACTS.md`).

### Neutras

- El CI del proyecto (`tests.yml`, `build_students.yml`, `validate-survey-json.yml`)
  no se ve afectado porque no referenciaba `testsprite_tests/`.

## Alternativas consideradas

| Alternativa | Descartada porque |
|---|---|
| Mantener `testsprite_tests/` y solo eliminar `tmp/` | `node_modules/` (18MB) seguía inflando el repo; `run_tests.mjs` y PRD no son parte del core |
| Mover `testsprite_tests/` a un repo separado | Complejidad innecesaria; TestSprite es externo y puede ejecutarse on-demand sin vivir en el repo |
| Integrar `testsprite_tests/` al CI principal | Requiere mantener Playwright como dependencia; mejor re-implementar tests E2E nativos (TEST-13) |

## Referencias

- Plan de mejora CC-09: Eliminar completamente `testsprite_tests/`
- Plan de mejora CC-01: Rotar API key DeepSeek expuesta
- Plan de mejora CC-02: Corregir `.gitignore`
- Plan de mejora TEST-13 (futuro): Añadir tests E2E con Playwright en CI principal
