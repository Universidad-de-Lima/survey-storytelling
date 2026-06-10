# AI Agent Guide

Guia operativa corta para agentes IA que necesitan modificar `survey-storytelling`.

## Leer Primero

| Necesidad | Documento |
| --- | --- |
| Reglas obligatorias de edicion | `AGENTS.md` |
| Arquitectura y modulos | `ARCHITECTURE.md` |
| Contratos CSV/JSON | `CONTRACTS.md` |
| Tests en navegador | `tests/README.md` |
| Cambios historicos | `docs/CHANGELOG.md` |

No crear documentos nuevos si una de estas fuentes puede actualizarse.

## Quick Facts

| Dato | Valor |
| --- | --- |
| Tipo | SPA estatica para GitHub Pages |
| Stack | HTML, CSS, Vanilla JS, Python |
| Backend | No |
| Base de datos | No |
| Runtime dependencies | 0 |
| Build data dependency | pandas |
| Tests | Mini-framework propio en navegador |

## Entry Points

| Archivo | Cuando tocarlo |
| --- | --- |
| `zoho-survey/index.html` | Navegacion entre tipos de encuesta y periodos. |
| `zoho-survey/template/index.html` | Layout base de dashboards por periodo. |
| `zoho-survey/shared/js/loader.js` | Flujo del navegador de encuestas. |
| `zoho-survey/shared/js/dashboard.js` | Orquestacion del dashboard. |
| `zoho-survey/shared/js/config/constants.js` | Metas, ciclos y constantes compartidas. |
| `zoho-survey/scripts/build_json.py` | Transformacion CSV -> JSON. |
| `zoho-survey/scripts/validate_generated_json.py` | Validacion estructural de JSON y HTML. |
| `tests/run-tests.html` | Runner de tests unitarios. |

## Reglas De Cambio

Hacer:

- Inspeccionar archivos reales antes de responder o editar.
- Mantener Vanilla JS con IIFE y APIs `window.Survey*`.
- Usar `escapeHTML()` o `sanitizeHTML()` antes de insertar contenido externo con `innerHTML`.
- Agregar o actualizar tests cuando cambien utilidades compartidas.
- Mantener cambios de contratos sincronizados entre ETL, validadores, frontend y `CONTRACTS.md`.

No hacer:

- No modificar manualmente JSON generados.
- No introducir React, Vue, Svelte ni dependencias runtime sin decision explicita.
- No asumir que existe `npm test`; los tests se ejecutan con `tests/run-tests.html`.
- No usar rutas `surveys/...`; la aplicacion vive en `zoho-survey/...`.
- No duplicar en guias operativas el contenido canonico de `ARCHITECTURE.md` o `CONTRACTS.md`.

## Tareas Comunes

### Cambiar una meta

Editar `zoho-survey/shared/js/config/constants.js` y validar visualmente el dashboard afectado.

### Agregar un topico semantico

Editar la configuracion usada por `zoho-survey/scripts/build_json.py`, regenerar JSON y validar con:

```bash
python zoho-survey/scripts/validate_generated_json.py undergraduate
```

### Agregar un periodo

1. Colocar el CSV en `data/`.
2. Ejecutar `python zoho-survey/scripts/build_json.py`.
3. Revisar que se generen los JSON del periodo y que `periodos.json` quede actualizado.
4. Ejecutar el validador correspondiente.
5. Abrir `http://localhost:8080/zoho-survey/` con `npm start`.

### Probar utilidades JS

1. Abrir `tests/run-tests.html` directamente o servir el repo con `npm start`.
2. Agregar el test en `tests/unit/`.
3. Registrar el script en `tests/run-tests.html`.

## Checklist Antes De Cerrar Un Cambio

- Rutas verificadas contra el arbol real.
- Documentacion canonica actualizada, sin duplicar contenido.
- JSON generados no editados manualmente.
- Contratos actualizados si cambio la forma de datos.
- Tests o validacion manual reportados en el PR o respuesta final.
