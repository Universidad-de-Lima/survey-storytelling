# survey-storytelling v2.0

Sistema estático de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte datos CSV exportados de Zoho Survey en un dashboard interactivo SPA, sin backend, sin base de datos, 100% estático y desplegable en GitHub Pages.

## Purpose

Transformar datos crudos de encuestas de satisfacción (CSV) en dashboards visuales interactivos estáticos. Sin servidores, sin build steps, cero dependencias runtime.

## Quick Start

```bash
# 1. Colocar CSV en data/
# 2. Generar JSONs
python zoho-survey/scripts/build_json.py

# 3. Validar contratos
python zoho-survey/scripts/validate_generated_json.py undergraduate

# 4. Iniciar servidor local
npm start
# → Abrir http://localhost:8080/zoho-survey/
```

## Architecture Role

Pipeline ETL (Python) → JSON → HTML/CSS/JS → GitHub Pages.

```
CSV (Zoho Survey) → [build_json.py] → JSON contracts (9/periodo) → [dashboard.js + 7 módulos] → HTML/CSS render
                                     ↓
                         [validate_generated_json.py] (validación CI)
```

## Project Structure (v2.0)

```
survey-storytelling/
├── data/                          ← CSVs fuente (3 archivos)
├── docs/                          ← Documentación
│   ├── ai-agent-guide.md          ← Guía para DeepSeek, Claude, Copilot
│   ├── CHANGELOG.md               ← Historial de versiones
│   └── development-guide.md
├── tests/                         ← Tests unitarios (34 tests)
│   ├── run-tests.html             ← Runner (abrir en navegador)
│   ├── test-framework.js
│   └── unit/ (3 test files)
├── .github/workflows/             ← 3 workflows CI/CD
├── zoho-survey/                   ← Aplicación principal
│   ├── index.html                 ← Entry point (loader)
│   ├── underconstruction.html
│   ├── shared/
│   │   ├── css/                   ← 6 archivos modulares
│   │   │   ├── tokens.css         ← Design tokens
│   │   │   ├── reset.css          ← Reset + utilidades
│   │   │   ├── layout.css         ← Header, nav, grid, footer
│   │   │   ├── components.css     ← KPIs, filtros, barras, tablas
│   │   │   ├── sections.css       ← Media queries
│   │   │   └── dashboard.css      ← Entry point (@import)
│   │   ├── js/
│   │   │   ├── config/constants.js      ← Metas, ciclos
│   │   │   ├── utils/formatters.js      ← 13 funciones de formateo
│   │   │   ├── utils/sanitizer.js       ← escapeHTML + sanitizeHTML
│   │   │   ├── components/tooltip.js    ← Tooltip flotante
│   │   │   ├── components/progress-bar.js← Barra de progreso
│   │   │   ├── components/custom-select.js← Dropdown personalizado
│   │   │   ├── components/multiselect.js← Dropdown multiselección
│   │   │   ├── dashboard.js       ← Orquestador
│   │   │   └── loader.js          ← Navegador
│   │   └── img/
│   ├── template/index.html        ← Template para nuevos periodos
│   ├── scripts/
│   │   ├── build_json.py          ← ETL: CSV → 9 JSONs/periodo
│   │   ├── validate_generated_json.py
│   │   ├── lib/config.py          ← Config ETL externalizada
│   │   └── schemas/ (3 JSON Schemas)
│   └── students/
│       ├── undergraduate/ (2025-2, 2026-1)
│       ├── graduate/ (2026)
│       └── posgraduate/ (placeholder)
├── ARCHITECTURE.md                ← Documentación técnica detallada
├── CONTRACTS.md                   ← Contratos de datos v2.0
├── AGENTS.md                      ← Reglas para IA
└── package.json
```

## System Layers

| Layer | Path | Technology | Responsibility |
|-------|------|------------|----------------|
| **Source** | `data/` | CSV (UTF-8) | Raw Zoho Survey exports |
| **ETL** | `zoho-survey/scripts/` | Python 3.11 + pandas | Transform, aggregate, topic analysis |
| **Contracts** | `zoho-survey/students/{level}/{period}/json/` | JSON (9 files) | Precomputed data (versioned) |
| **Loader** | `zoho-survey/index.html` | Vanilla JS (ES6) | Survey type + period navigation |
| **Dashboard** | `zoho-survey/shared/js/` | Vanilla JS (ES6), 8 modules | Interactive SPA |
| **Styles** | `zoho-survey/shared/css/` | CSS3, 5 layers | Responsive design system |
| **Tests** | `tests/` | Vanilla JS | 34 unit tests |
| **CI/CD** | `.github/workflows/` | GitHub Actions | Build, validate, deploy |

Para documentación detallada: `ARCHITECTURE.md`, `CONTRACTS.md`, `AGENTS.md`, `docs/ai-agent-guide.md`.
