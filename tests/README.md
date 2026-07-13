# Tests

Infraestructura de tests unitarios para `survey-storytelling`. No usa dependencias npm ni Vitest; se ejecuta en navegador con un mini-framework propio (`tests/test-framework.js`) o en Node con jsdom.

## Ejecutar Tests

### Opción 1: Navegador (recomendado para desarrollo)

Abrir directamente:

```text
tests/run-tests.html
```

O servir el repositorio y abrir la ruta en navegador:

```bash
npm start
# http://localhost:8080/tests/run-tests.html
```

### Opción 2: Node (sin DOM, para CI)

```bash
npm run test:js
```

Ejecuta los tests que no requieren DOM real (usan un stub mínimo de `window`/`document`).

### Opción 3: Node con jsdom (para tests que necesitan DOM real)

```bash
npm run test:js:dom
```

Ejecuta `tests/unit/test-dom.js` con jsdom.

### Opción 4: CI (GitHub Actions)

Los tests se ejecutan automáticamente en cada PR y push a `main` vía `.github/workflows/tests.yml`:
- `python-tests`: ejecuta `python -m unittest discover tests/` en `zoho-survey/scripts/`.
- `js-tests`: ejecuta `npm run test:js` + `npm run test:js:dom` + verificación de sintaxis con `node -c`.

## Estructura

```text
tests/
├── run-tests.html              # Runner HTML para navegador
├── test-framework.js           # Mini-framework: assert, describe, it, renderTo
└── unit/
    ├── test-config.js          # SURVEY_CONFIG (9 tests)
    ├── test-formatters.js      # SurveyFormatters (26 tests)
    ├── test-metrics.js         # SurveyMetrics (10 tests)
    ├── test-sanitizer.js       # SurveySanitizer (20 tests)
    ├── test-sentiment-view.js  # SurveySentimentView API surface (9 tests)
    ├── test-filter-controller.js  # SurveyFilterController (16 tests)
    ├── test-loader.js          # Loader logic (16 tests)
    ├── test-insights-ia.js     # Insights IA (4 tests)
    └── test-dom.js             # Tests con jsdom (33 tests, dialecto propio)
```

## Agregar Un Test

### Tests con TestFramework (recomendado)

1. Crear `tests/unit/test-<nombre>.js`.
2. Usar el patrón IIFE y `window.TestFramework`.
3. Registrar el archivo con `<script>` en `tests/run-tests.html`.
4. Para ejecución en CI, añadir el archivo al script inline en `package.json` (`test:js`) y en `.github/workflows/tests.yml`.
5. Abrir el runner y verificar el resultado.

```javascript
(() => {
  'use strict';
  const { assert, describe, it } = window.TestFramework;
  const modulo = window.SurveyMiModulo;

  describe('miModulo', () => {
    it('hace X', () => {
      assert.equal(modulo.miFuncion('input'), 'expected');
    });
  });
})();
```

### Tests con jsdom (para tests que necesitan DOM real)

Usar el patrón de `tests/unit/test-dom.js` con su propio runner inline (`test()`, `assertEqual()`, `assertTrue()`).

## Cobertura Actual

> **Estado del snapshot (auditoría URAF v5.0, 2026-07-10):** El snapshot del repositorio
> entregado **no incluye el directorio `zoho-survey/`**, por lo que los módulos bajo test
> (`shared/js/**`) no están disponibles y los tests no pueden ejecutarse localmente sobre
> este snapshot. Las cifras siguientes reflejan los tests **declarados** en cada archivo.
> Adicionalmente, `test-sanitizer.js` está **vacío (0 bytes)** y `test-sentiment-view.js`
> **no está presente** en el snapshot (ver `AGENTS.md` y `CHANGELOG.md` para el estado del
> repositorio completo). Esta es una deuda de consistencia pendiente (IM-005, URAF v5.0).

### Tests con TestFramework (declarados)

| Archivo | Tests declarados | Estado en snapshot |
| --- | --- | --- |
| `test-config.js` | 9 | presente (9 tests) |
| `test-formatters.js` | 26 | presente (26 tests) |
| `test-metrics.js` | 10 | presente (10 tests) |
| `test-sanitizer.js` | 20 | **vacío (0 bytes, 0 tests reales)** — pendiente de implementar |
| `test-sentiment-view.js` | 9 | **ausente del snapshot** — pendiente de restaurar |
| `test-filter-controller.js` | 16 | presente (16 tests) |
| `test-loader.js` | 16 | presente (16 tests) |
| `test-insights-ia.js` | 4 | presente (4 tests) |

### Tests con jsdom (declarados)

| Archivo | Tests declarados | Módulo bajo prueba |
| --- | --- | --- |
| `test-dom.js` | 33 | `SurveyFormatters`, `SurveySanitizer`, `SurveyDomHelpers`, `SurveyTooltip` (con DOM real) |

### Total declarado: 143 tests — Total real en snapshot: 113 tests

La diferencia (30 tests) corresponde a `test-sanitizer.js` vacío (20) + `test-sentiment-view.js`
ausente (9) + 1 discrepancia menor en `test-dom.js`. **Los 3 runners de tests** (`package.json
`test:js`, `tests.yml` inline, `tests/run-tests.html`) han sido alineados (IM-005) para
referenciar el mismo conjunto canónico de 8 archivos de tests TestFramework.

## Tests Python

Los tests Python viven en `zoho-survey/scripts/tests/` y se ejecutan con:

```bash
cd zoho-survey/scripts && python -m unittest discover tests/ -v
```

Ver `zoho-survey/scripts/README.md` para detalle de cobertura Python.

## Notas

- **Tests eliminados en Fase 1**: `test-tooltip.js`, `test-multiselect.js`, `test-progress-bar.js`, `test-radar-chart.js`, `test-custom-select.js` fueron eliminados porque nunca se cargaban en ningún runner y tenían un bug latente (`assert.true` no existe en el framework, solo `assert.isTrue`).
- **Tests E2E**: Playwright fue eliminado en Fase 2 porque nunca se integró al CI. Si se quiere E2E real, planificar en una fase futura con cobertura más amplia.
- **Linting**: Ruff (Python) y ESLint (JS) se ejecutan en CI de forma informativa desde Fase 2. Se harán estrictos en Fase 3 tras auto-fixear las violaciones existentes.
