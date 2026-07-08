# Tests

Infraestructura de tests unitarios para `survey-storytelling`. No usa dependencias npm ni Vitest; se ejecuta en navegador con un mini-framework propio.

## Ejecutar Tests

Abrir directamente:

```text
tests/run-tests.html
```

O servir el repositorio y abrir la ruta en navegador:

```bash
npm start
# http://localhost:8080/tests/run-tests.html
```

## Estructura

```text
tests/
├── run-tests.html        # Runner HTML
├── test-framework.js     # assert, describe, it, renderTo
└── unit/
    ├── test-config.js      # SURVEY_CONFIG
    ├── test-formatters.js  # SurveyFormatters
    └── test-sanitizer.js   # SurveySanitizer
```

## Agregar Un Test

1. Crear `tests/unit/test-<nombre>.js`.
2. Usar el patron IIFE y `window.TestFramework`.
3. Registrar el archivo con `<script>` en `tests/run-tests.html`.
4. Abrir el runner y verificar el resultado.

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

## Cobertura Actual

| Archivo | Tests | Modulo bajo prueba |
| --- | --- | --- |
| `test-config.js` | 9 | `SURVEY_CONFIG` |
| `test-formatters.js` | 13 | `SurveyFormatters` |
| `test-sanitizer.js` | 12 | `SurveySanitizer` |

Total: 34 tests.
