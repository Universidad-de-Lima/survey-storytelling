# survey-storytelling

Sistema estático de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte datos CSV exportados de Zoho Survey en un dashboard interactivo SPA, sin backend, sin base de datos, 100% estático y desplegable en GitHub Pages.

## Purpose

Transformar datos crudos de encuestas de satisfacción (CSV) en dashboards visuales interactivos estáticos. Sin servidores, sin build steps, cero dependencias runtime.

## Architecture Role

Pipeline ETL (Python) → JSON → HTML/CSS/JS → GitHub Pages.

`
CSV (Zoho Survey) → [build_json.py] → JSON contracts → [dashboard.js] → HTML/CSS render
                          ↓
              [validate_generated_json.py] (validación CI)
`

## Project Structure

`
survey-storytelling/
├── index.html               ← Entry point (redirect a zoho-survey/students/undergraduate/)
├── zoho-survey/             ← Dashboard estático completo
│   ├── shared/              ← CSS, JS, imágenes compartidos
│   └── students/
│       ├── data/            ← CSVs fuente
│       ├── scripts/         ← ETL Python (build_json.py, validate_generated_json.py)
│       ├── template/        ← Template HTML para nuevos periodos
│       ├── undergraduate/   ← Dashboards de pregrado (2025-2, 2026-1)
│       └── postgraduate/    ← Placeholder posgrado
├── .github/workflows/       ← Solo 3 workflows: ETL build, validación, deploy
├── package.json             ← Solo scripts para ETL Python
├── README.md
├── ARCHITECTURE.md
├── CONTRACTS.md
└── AGENTS.md
`

## System Layers

| Layer       | Path                                          | Technology           | Responsibility                        |
| ----------- | --------------------------------------------- | -------------------- | ------------------------------------- |
| **Source**  | zoho-survey/students/data/                  | CSV (UTF-8/Latin-1)  | Raw survey exports from Zoho Survey   |
| **ETL**     | zoho-survey/students/scripts/               | Python 3.11 + pandas | Transform, aggregate, topic analysis  |
| **Contracts** | zoho-survey/students/{level}/{period}/json/ | JSON                 | Precomputed data contracts            |
| **Dashboard** | zoho-survey/shared/js/dashboard.js         | Vanilla JS (ES6)     | Interactive visualization SPA         |
| **Styles**  | zoho-survey/shared/css/                     | CSS3 (custom properties) | Responsive design system          |
| **CI/CD**   | .github/workflows/                          | GitHub Actions       | ETL build, validate, deploy           |

Para documentación detallada, ver: ARCHITECTURE.md, CONTRACTS.md, AGENTS.md.
