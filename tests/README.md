# Tests

Infraestructura de tests unitarios para `survey-storytelling`. Cero dependencias, ejecutable en cualquier navegador.

## Quick Start

Abrir `tests/run-tests.html` en el navegador:

```
tests/run-tests.html → Carga módulos + tests → Muestra resultados ✓/✗
```

## Estructura

```
tests/
├── run-tests.html           ← Runner HTML (abrir en navegador)
├── test-framework.js        ← assert, describe, it, renderTo
└── unit/
    ├── test-config.js       ← SURVEY_CONFIG (9 tests)
    ├── test-formatters.js   ← SurveyFormatters (13 tests)
    └── test-sanitizer.js    ← SurveySanitizer (12 tests)
```

## Cómo agregar un nuevo test

1. Crear `tests/unit/test-<nombre>.js`
2. Usar el patrón:

```javascript
(() => {
  'use strict';
  const { assert, describe, it } = window.TestFramework;
  const modulo = window.SurveyMiModulo;

  describe('miModulo', () => {
    it('debe hacer X', () => {
      assert.equal(modulo.miFuncion('input'), 'expected');
    });
  });
})();
```

3. Agregar el `<script>` en `tests/run-tests.html`
4. Abrir `run-tests.html` en el navegador

## Tests actuales: 34

| Archivo | Tests | Módulo bajo prueba |
|---------|-------|--------------------|
| `test-config.js` | 9 | `SURVEY_CONFIG` |
| `test-formatters.js` | 13 | `SurveyFormatters` |
| `test-sanitizer.js` | 12 | `SurveySanitizer` |
