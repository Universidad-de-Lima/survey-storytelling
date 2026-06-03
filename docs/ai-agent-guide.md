# AI Agent Guide — survey-storytelling v2.0

Guía de referencia rápida para agentes de IA (DeepSeek, Claude, GitHub Copilot)
que necesiten comprender, modificar o extender este proyecto.

---

## Quick Facts

| Dato | Valor |
|------|-------|
| Tipo | Static Site Generator (SPA) |
| Stack | HTML5 + CSS3 + Vanilla JS (ES6+) + Python 3.11 |
| Deploy | GitHub Pages |
| Backend | No |
| Base de datos | No (CSV → JSON estáticos) |
| Dependencias runtime | 0 (cero) |
| Dependencias build | pandas (Python) |
| Tests | 34 unit tests (navegador) |

---

## Entry Points

| Archivo | Rol | Cuándo modificarlo |
|---------|-----|--------------------|
| `zoho-survey/index.html` | Navegador/loader de encuestas | Nuevos tipos de encuesta |
| `zoho-survey/template/index.html` | Template para dashboards | Cambios de layout/UI |
| `zoho-survey/shared/js/dashboard.js` | Orquestador del dashboard | Cambios en lógica de renderizado |
| `zoho-survey/shared/js/loader.js` | Lógica del navegador | Cambios en flujo de selección |
| `zoho-survey/scripts/build_json.py` | ETL: CSV → JSON | Cambios en el pipeline de datos |
| `zoho-survey/scripts/validate_generated_json.py` | Validador de contratos | Nuevos contratos o reglas |
| `tests/run-tests.html` | Runner de tests | Abrir en navegador para validar |

---

## Architecture Decision Records

### ¿Por qué no React/Vue/Svelte?

- GitHub Pages no soporta SSR ni build steps complejos
- El proyecto debe ser mantenible por analistas de datos, no solo developers
- Cero costo operativo es un requisito no negociable
- Vanilla JS es suficiente para la complejidad actual

### ¿Por qué IIFE y no ES Modules?

- Compatibilidad con navegadores sin necesidad de `type="module"`
- Los módulos se cargan como `<script>` normales
- Cada módulo expone su API en `window.Survey*`
- `dashboard.js` usa delegación con fallback inline (backward compatible)

### ¿Por qué múltiples archivos JSON y no uno solo?

- Carga paralela (Promise.all) → más rápido que un archivo grande
- Cada visualización consume solo los datos que necesita
- Facilita la validación independiente de cada contrato
- Si un archivo falla, los demás siguen funcionando (graceful degradation)

---

## How to Add a New Survey Period

1. Colocar el CSV en `data/` con naming: `ENCUESTA DE SATISFACCIÓN {TIPO} - {PERIODO}.csv`
2. Ejecutar `python zoho-survey/scripts/build_json.py`
3. El script detecta automáticamente tipo y periodo
4. Genera `json/` con 9 archivos en el directorio correspondiente
5. Copia `template/index.html` como `{periodo}/index.html`
6. Actualiza `periodos.json` automáticamente

**No modificar manualmente los JSON generados.**

---

## How to Add a New Visualization

1. Crear el módulo en `shared/js/visualizations/` (o `components/`)
2. Exponer la API en `window.SurveyMiVisualizacion`
3. Agregar la función de renderizado en `dashboard.js`
4. Agregar el `<script>` en `template/index.html`
5. Agregar el HTML necesario en `template/index.html`
6. Agregar estilos en `shared/css/components.css`

Patrón:
```javascript
// shared/js/visualizations/mi-chart.js
window.SurveyMiChart = (() => {
  'use strict';
  function render(containerId, data) { /* ... */ }
  return { render };
})();
```

---

## Module Dependency Graph

```
loader.js
  └── periodos.json (fetch dinámico)

dashboard.js
  ├── config/constants.js        (window.SURVEY_CONFIG)
  ├── utils/formatters.js        (window.SurveyFormatters)
  ├── utils/sanitizer.js         (window.SurveySanitizer)
  ├── components/tooltip.js      (window.SurveyTooltip)
  ├── components/progress-bar.js (window.SurveyProgressBar)
  ├── components/custom-select.js(window.SurveyCustomSelect)
  ├── components/multiselect.js  (window.SurveyMultiselect)
  └── json/*.json (9 endpoints)

build_json.py
  ├── lib/config.py              (COLUMN_RENAME, mappings, TOPICOS)
  └── data/*.csv
```

---

## Data Flow

```
data/*.csv
  → build_json.py (COLUMN_RENAME, aggregations, topic analysis)
    → json/dashboard_data.json  ← KPIs, NPS, CSAT, hallazgos
    → json/dimensiones.json     ← datos granulares por facultad/carrera/ciclo
    → json/ids.json             ← conteos por segmento
    → json/nps_ciclo_carrera.json
    → json/csat_ciclo_carrera.json
    → json/nps_carrera.json     ← legacy
    → json/csat_carrera.json    ← legacy
    → json/filtros.json         ← metadatos para cascada de filtros
    → json/sentimiento.json     ← análisis cualitativo (tópicos)
      → dashboard.js (loadAllData → filtrarDatos → render*)
        → index.html (iframe en loader)
```

---

## Safety Rules for AI Agents

### ✅ DO

- Modificar `config/constants.js` para cambiar metas o listas
- Agregar nuevos módulos en `utils/`, `components/`, o `visualizations/`
- Extender `build_json.py` con nuevas agregaciones
- Agregar tests en `tests/unit/`
- Usar `escapeHTML()` o `sanitizeHTML()` antes de cualquier `innerHTML`
- Mantener el patrón de delegación con fallback inline

### ❌ DON'T

- NO introducir frameworks (React, Vue, etc.)
- NO agregar dependencias npm runtime
- NO modificar manualmente archivos JSON generados
- NO romper la compatibilidad backward de los contratos JSON
- NO usar `innerHTML` sin sanitizar contenido externo
- NO hacer refactors masivos sin tests que los respalden

---

## Common Tasks

### Cambiar la meta de CSAT

Editar `shared/js/config/constants.js`:
```javascript
window.SURVEY_CONFIG = {
  META_CSAT: 95,  // antes 93
  // ...
};
```

### Agregar una nueva carrera al catálogo

Editar `scripts/lib/config.py` y agregar la entrada en `CARRERA_FACULTAD`.

### Agregar un nuevo tópico al análisis semántico

Editar `scripts/lib/config.py` y agregar la entrada en `TOPICOS`.

### Depurar el dashboard

1. Abrir `tests/run-tests.html` → verificar que los 34 tests pasan
2. Abrir el dashboard en el navegador → F12 → Console
3. Verificar que `window.SURVEY_CONFIG`, `window.SurveyFormatters`, etc. existen
4. Verificar que los 9 JSONs cargan sin errores 404

---

## File Size Reference

| Archivo | Líneas | Rol |
|---------|--------|-----|
| `dashboard.js` | ~1,700 | Orquestador principal |
| `loader.js` | ~200 | Navegador de encuestas |
| `build_json.py` | ~770 | ETL pipeline |
| `components.css` | ~520 | Estilos de componentes |
| `sections.css` | ~170 | Media queries + secciones |
| `layout.css` | ~170 | Header, nav, grid, footer |
| `tokens.css` | ~50 | Variables CSS |
| `reset.css` | ~60 | Reset + utilidades |
