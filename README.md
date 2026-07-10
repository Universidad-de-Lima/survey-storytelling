# survey-storytelling v3.1.0

[![Build and Deploy](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/build_zoho_survey.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/build_zoho_survey.yml)
[![Tests](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/tests.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/tests.yml)
[![Validate JSON](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/validate-survey-json.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-storytelling/actions/workflows/validate-survey-json.yml)

Sistema estático de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte CSV exportados desde Zoho Survey en dashboards interactivos, sin backend ni base de datos, desplegables en GitHub Pages.

## Quick Start

Para inicializar y probar el proyecto localmente, ejecuta los siguientes comandos desde la raíz del repositorio:

```bash
# 1. Colocar los archivos CSV de Zoho Survey en la carpeta data/

# 2. Instalar dependencias locales (si es la primera vez)
npm install

# 3. Generar los JSONs agregados del periodo
npm run build:json

# 4. Validar la estructura de los JSONs y contratos HTML generados
npm run validate:json

# 5. Iniciar el servidor local
npm start
# Abrir http://localhost:8080/zoho-survey/
```

## Documentación del Proyecto

Este repositorio sigue una estructura de documentación modularizada con responsabilidades únicas para evitar duplicación de contenido:

* **Reglas Operativas:** [AGENTS.md](AGENTS.md) contiene las directivas obligatorias de codificación para agentes de IA y desarrolladores.
* **Diseño Técnico:** [ARCHITECTURE.md](ARCHITECTURE.md) describe la arquitectura del sistema, el mapa de componentes, la estructura física de directorios (incluyendo la aplicación `zoho-survey/`) y el registro único de deuda técnica del código.
* **Contratos de Datos:** [CONTRACTS.md](CONTRACTS.md) especifica las entradas CSV, salidas JSON, schemas estructurados, invariantes matemáticas y deuda técnica de datos.
* **Guías de Procedimiento:** [docs/developer-guide.md](docs/developer-guide.md) detalla flujos comunes como la adición de periodos, cambio de metas u otros tópicos.
* **Lógica del Dashboard:** [docs/filter-logic.md](docs/filter-logic.md) describe las reglas del negocio aplicadas a los filtros en cascada del frontend.
* **Pruebas de Unidad:** [tests/README.md](tests/README.md) detalla cómo ejecutar y extender los tests unitarios.
* **Changelog:** [docs/CHANGELOG.md](docs/CHANGELOG.md) contiene el historial de cambios del proyecto.
* **Onboarding:** [docs/onboarding.md](docs/onboarding.md) es la guía de inicio para nuevos desarrolladores y analistas.
* **Health Check:** [zoho-survey/health.html](zoho-survey/health.html) verifica la integridad de todos los dashboards y JSONs.
