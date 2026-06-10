# survey-storytelling v2.0

Sistema estatico de visualizacion de encuestas de satisfaccion para la Universidad de Lima. Convierte CSV exportados desde Zoho Survey en dashboards interactivos, sin backend, sin base de datos y desplegables en GitHub Pages.

## Quick Start

```bash
# 1. Colocar CSV en data/
# 2. Generar JSONs
python zoho-survey/scripts/build_json.py

# 3. Validar contratos
python zoho-survey/scripts/validate_generated_json.py undergraduate

# 4. Iniciar servidor local
npm start
# Abrir http://localhost:8080/zoho-survey/
```

## Flujo Del Sistema

```text
CSV de Zoho Survey
  -> zoho-survey/scripts/build_json.py
  -> contratos JSON por periodo
  -> zoho-survey/shared/js/dashboard.js
  -> HTML/CSS estatico en GitHub Pages
```

## Documentacion Canonica

| Documento | Responsabilidad |
| --- | --- |
| `AGENTS.md` | Reglas obligatorias para agentes IA y cambios automatizados. |
| `ARCHITECTURE.md` | Arquitectura tecnica, capas, modulos, patrones y deuda vigente. |
| `CONTRACTS.md` | Unica fuente para contratos CSV/JSON, invariantes y validacion. |
| `docs/ai-agent-guide.md` | Guia operativa corta para agentes que van a modificar el repo. |
| `docs/CHANGELOG.md` | Historial de cambios relevantes por version. |
| `tests/README.md` | Como ejecutar y extender los tests del navegador. |
| `zoho-survey/README.md` | Guia local del subdirectorio de la aplicacion. |

Evitar duplicar en nuevos documentos informacion que ya pertenece a estas fuentes.

## Estructura Principal

```text
survey-storytelling/
├── data/                    # CSVs fuente
├── docs/                    # Guias de soporte y changelog
├── tests/                   # Mini-framework y tests unitarios en navegador
├── .github/workflows/       # Build JSON, validacion y deploy GitHub Pages
├── zoho-survey/             # Aplicacion estatica, ETL, contratos y dashboards
├── AGENTS.md
├── ARCHITECTURE.md
├── CONTRACTS.md
└── package.json
```

## Capas

| Capa | Ruta | Responsabilidad |
| --- | --- | --- |
| Fuente | `data/` | CSVs exportados desde Zoho Survey. |
| ETL | `zoho-survey/scripts/` | Transformar, agregar, validar y generar JSON. |
| Contratos | `zoho-survey/students/{level}/{period}/json/` | Datos precomputados para el frontend. |
| Loader | `zoho-survey/index.html`, `zoho-survey/shared/js/loader.js` | Navegacion entre encuestas y periodos. |
| Dashboard | `zoho-survey/shared/js/` | SPA interactiva en Vanilla JS. |
| Estilos | `zoho-survey/shared/css/` | Tokens, layout, componentes y secciones. |
| Tests | `tests/` | Tests unitarios ejecutados en navegador. |
| CI/CD | `.github/workflows/` | Build, validacion y deploy. |

## Reglas De Mantenimiento

- No modificar manualmente JSON generados.
- No introducir frameworks ni dependencias runtime sin una decision explicita.
- Mantener `CONTRACTS.md` como fuente unica de la forma de los datos.
- Mantener `ARCHITECTURE.md` como fuente unica de estructura tecnica.
- Mantener `AGENTS.md` como fuente unica de reglas para IA.
