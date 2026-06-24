# Guía de Desarrollo y Operaciones

Guía operativa para desarrolladores humanos y agentes de IA que necesitan mantener o modificar el sistema `survey-storytelling`.

## Documentación de Referencia

Antes de realizar cambios, familiarízate con los siguientes documentos según tu necesidad:

| Necesidad | Documento |
| --- | --- |
| Reglas técnicas obligatorias | [AGENTS.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/AGENTS.md) |
| Arquitectura del sistema y carpetas | [ARCHITECTURE.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/ARCHITECTURE.md) |
| Especificación y esquemas de datos | [CONTRACTS.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/CONTRACTS.md) |
| Ejecución y creación de pruebas | [tests/README.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/tests/README.md) |
| Lógica de filtros del frontend | [docs/filter-logic.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/docs/filter-logic.md) |
| Historial de versiones | [docs/CHANGELOG.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/docs/CHANGELOG.md) |

## Quick Facts

| Dato | Valor |
| --- | --- |
| Tipo | SPA estática para GitHub Pages |
| Stack | HTML, CSS, Vanilla JS, Python |
| Dependencias Runtime | 0 |
| Dependencias ETL | pandas |
| Ejecución de Tests | Servidor local o archivo HTML directo |

## Puntos de Entrada Comunes

| Archivo | Cuándo tocarlo |
| --- | --- |
| [zoho-survey/index.html](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/index.html) | Navegación entre tipos de encuesta y periodos. |
| [zoho-survey/template/index.html](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/template/index.html) | Plantilla base de dashboards por periodo. |
| [zoho-survey/shared/js/loader.js](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/shared/js/loader.js) | Flujo del navegador de encuestas. |
| [zoho-survey/shared/js/dashboard.js](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/shared/js/dashboard.js) | Orquestación general del dashboard. |
| [zoho-survey/shared/js/config/constants.js](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/shared/js/config/constants.js) | Metas, ciclos y constantes compartidas. |
| [zoho-survey/scripts/build_json.py](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/scripts/build_json.py) | Transformación CSV -> JSON. |
| [zoho-survey/scripts/validate_generated_json.py](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/scripts/validate_generated_json.py) | Validación estructural de JSON y HTML. |

> [!IMPORTANT]
> **Orden de carga de dependencias JS:**
> En los archivos HTML (`zoho-survey/index.html` y la plantilla `zoho-survey/template/index.html`), las dependencias de scripts deben importarse en un orden específico. Particularmente, `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` para evitar errores en tiempo de ejecución (`TypeError: window.SurveyDomHelpers is undefined`) que bloqueen el loader del portal.


---

## Tareas Comunes

### 1. Cambiar una Meta de NPS o CSAT
1. Edita el objeto correspondiente en [zoho-survey/shared/js/config/constants.js](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/shared/js/config/constants.js).
2. Valida visualmente los cambios levantando el servidor local (`npm start`).

### 2. Agregar un Tópico Semántico para NPS
1. Edita el diccionario `TOPICOS` en [zoho-survey/scripts/lib/config.py](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/zoho-survey/scripts/lib/config.py) agregando las palabras clave, tipo de sentimiento e ícono.
2. Regenera los JSONs ejecutando `npm run build:json`.
3. Valida la estructura ejecutando `npm run validate:json`.

### 3. Agregar un Nuevo Periodo de Encuesta (Ingesta de Datos)
1. Coloca el archivo CSV exportado desde Zoho Survey en la carpeta `data/`.
2. Asegúrate de que el nombre del archivo contenga el año/periodo (ej. `ENCUESTA_PREGRADO_2026-1.csv`).
3. Ejecuta `npm run build:json` desde la raíz para generar los archivos JSON de datos y actualizar automáticamente `periodos.json`.
4. Ejecuta `npm run validate:json` para comprobar que las salidas cumplan los contratos estructurales.
5. Inicia el servidor (`npm start`), abre `http://localhost:8080/zoho-survey/` en tu navegador y valida que el nuevo periodo cargue correctamente en la barra superior.

### 4. Probar y Crear Utilidades JavaScript
Para detalles de adición y ejecución de pruebas unitarias, consulta [tests/README.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/tests/README.md).

---

## Checklist de Validación antes de Commitear

- [ ] Las rutas de archivos modificadas han sido validadas contra el árbol real.
- [ ] No se han realizado ediciones manuales a los archivos JSON generados en `zoho-survey/students/**/json/`.
- [ ] Si se modificó la estructura de datos, se actualizaron coherentemente los validadores de Python y [CONTRACTS.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/CONTRACTS.md).
- [ ] Se ejecutaron las pruebas unitarias locales en navegador sin fallos.
- [ ] Se corrió con éxito `npm run validate:json` antes del commit.
