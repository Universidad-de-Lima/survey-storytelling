# Guía de Desarrollo y Operaciones

Guía operativa para desarrolladores humanos y agentes de IA que necesitan mantener o modificar el sistema `survey-storytelling`.

## Documentación de Referencia

Antes de realizar cambios, familiarízate con los siguientes documentos según tu necesidad:

| Necesidad | Documento |
| --- | --- |
| Reglas técnicas obligatorias | [AGENTS.md](AGENTS.md) |
| Arquitectura del sistema y carpetas | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Especificación y esquemas de datos | [CONTRACTS.md](CONTRACTS.md) |
| Ejecución y creación de pruebas | [tests/README.md](tests/README.md) |
| Lógica de filtros del frontend | [docs/filter-logic.md](docs/filter-logic.md) |
| Historial de versiones | [docs/CHANGELOG.md](docs/CHANGELOG.md) |

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
| [zoho-survey/index.html](zoho-survey/index.html) | Navegación entre tipos de encuesta y periodos. |
| [zoho-survey/template/index.html](zoho-survey/template/index.html) | Plantilla base de dashboards por periodo. |
| [zoho-survey/shared/js/loader.js](zoho-survey/shared/js/loader.js) | Flujo del navegador de encuestas. |
| [zoho-survey/shared/js/dashboard.js](zoho-survey/shared/js/dashboard.js) | Orquestación general del dashboard. |
| [zoho-survey/shared/js/config/constants.js](zoho-survey/shared/js/config/constants.js) | Metas, ciclos y constantes compartidas. |
| [zoho-survey/scripts/build_json.py](zoho-survey/scripts/build_json.py) | Transformación CSV -> JSON. |
| [zoho-survey/scripts/validate_generated_json.py](zoho-survey/scripts/validate_generated_json.py) | Validación estructural de JSON y HTML. |

> [!IMPORTANT]
> **Orden de carga de dependencias JS:**
> En los archivos HTML (`zoho-survey/index.html` y la plantilla `zoho-survey/template/index.html`), las dependencias de scripts deben importarse en un orden específico. Particularmente, `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` para evitar errores en tiempo de ejecución (`TypeError: window.SurveyDomHelpers is undefined`) que bloqueen el loader del portal.


---

## Tareas Comunes

### 1. Cambiar una Meta de NPS o CSAT
1. Edita el objeto correspondiente en [zoho-survey/shared/js/config/constants.js](zoho-survey/shared/js/config/constants.js).
2. Valida visualmente los cambios levantando el servidor local (`npm start`).

### 2. Agregar un Tópico Semántico para NPS
1. Edita el diccionario `TOPICOS` en [zoho-survey/scripts/lib/config.py](zoho-survey/scripts/lib/config.py) agregando las palabras clave, tipo de sentimiento e ícono.
2. Regenera los JSONs ejecutando `npm run build:json`.
3. Valida la estructura ejecutando `npm run validate:json`.

### 3. Agregar un Nuevo Periodo de Encuesta (Ingesta de Datos)
1. Coloca el archivo CSV exportado desde Zoho Survey en la carpeta `data/`.
2. Asegúrate de que el nombre del archivo contenga el año/periodo (ej. `ENCUESTA_PREGRADO_2026-1.csv`).
3. Ejecuta `npm run build:json` desde la raíz para generar los archivos JSON de datos y actualizar automáticamente `periodos.json`.
4. Ejecuta `npm run validate:json` para comprobar que las salidas cumplan los contratos estructurales.
5. Inicia el servidor (`npm start`), abre `http://localhost:8080/zoho-survey/` en tu navegador y valida que el nuevo periodo cargue correctamente en la barra superior.

### 4. Probar y Crear Utilidades JavaScript
Para detalles de adición y ejecución de pruebas unitarias, consulta [tests/README.md](tests/README.md).

---

## Checklist de Validación antes de Commitear

- [ ] Las rutas de archivos modificadas han sido validadas contra el árbol real.
- [ ] No se han realizado ediciones manuales a los archivos JSON generados en `zoho-survey/students/**/json/`.
- [ ] Si se modificó la estructura de datos, se actualizaron coherentemente los validadores de Python y [CONTRACTS.md](CONTRACTS.md).
- [ ] Se ejecutaron las pruebas unitarias locales en navegador sin fallos.
- [ ] Se corrió con éxito `npm run validate:json` antes del commit.

---

## Configuración del Motor Cualitativo

El sistema soporta dos motores de análisis cualitativo, controlados desde `lib/config.py`:

| Variable | Valores | Efecto |
|---|---|---|
| `DEEPSEEK_API_KEY` | API key string | Activa motor IA (DeepSeek). Si no está definida, usa motor Legacy |
| `IA_CUALITATIVO_FALLBACK=1` | env var | Fuerza modo legacy incluso con API key |
| `IA_CUALITATIVO_CACHE=0` | env var | Desactiva caché IA (`ia_cache.json`) |
| `IA_CUALITATIVO_WORKERS` | entero (default 15) | Workers concurrentes para IA |
| `IA_CUALITATIVO_MAX_RPM` | entero (default 60) | Rate limit de API |
| `IA_CUALITATIVO_TIMEOUT` | entero (default 60s) | Timeout por llamada |

**Motor IA (DeepSeek)** — activo en producción desde Fase IA:
- Una sola llamada API ejecuta 5 tareas: segmentación → sentimiento con reglas NPS → intensidad → clasificación taxonómica → cross-reference CSAT.
- Caché persistente en `ia_cache.json` (hash SHA256 de comentario + contexto + prompt version).
- Rate limit: 60 RPM, 15 workers concurrentes. Timeout: 60s por llamada.
- Costo estimado: ~$0.50 por build completo, ~$0.05 con caché.

**Motor Legacy (spaCy + embeddings)** — fallback automático:
- 3 módulos encadenados: `segmentacion_nps.py` → `aspect_extraction.py` → `sentiment_engine.py`.
- Precisión vs ground truth humano: sentimiento 59.7%, taxonomía 32.6%.
- Mantenido como respaldo si DeepSeek API no está disponible.

### Alternar entre motores

Para forzar el motor legacy en el próximo build (incluso con API key):
1. Ve a GitHub → Actions → `Build and Deploy Survey` → Run workflow.
2. En el campo "environment variables", escribe: `IA_CUALITATIVO_FALLBACK=1`.
3. O alternativamente, configura `IA_CUALITATIVO_MODE = "legacy"` en `lib/config.py` antes del push.

---

## Validación Cualitativa con la Skill `qualitative_research_synthesis`

El repositorio incluye una skill para agentes IA en `.agents/skills/qualitative_research_synthesis/SKILL.md`. Esta skill es **complementaria** al ETL automático y se usa para:

- **Revisión mensual de "Pendiente de Clasificación"**: tomar una muestra de fragmentos que el ETL no pudo clasificar y revisarlos manualmente.
- **Validación de calidad**: comparar clasificaciones del ETL contra criterio humano en muestras aleatorias.
- **Síntesis narrativa para reportes**: generar interpretaciones cualitativas para stakeholders no técnicos.

### Flujo de revisión recomendado

1. Extraer una muestra de `sentimiento.json` — filtrar por `"categoria_padre": "Pendiente de Clasificación"`.
2. Usar un agente IA con la skill para analizar la muestra.
3. Si se identifican patrones (ej. una dimensión nueva que debería estar en la taxonomía), actualizar `config/alias_aspectos.json`.
4. Regenerar JSONs y verificar que "Pendiente de Clasificación" disminuye.

La skill NO reemplaza al ETL. Su rol es de **síntesis e interpretación** sobre datos ya procesados.

---

## Rollback de Emergencia

### Revertir al último build bueno
1. Ir a GitHub → Commits. Buscar el último commit del bot (`github-actions`).
2. Copiar el hash del commit bueno.
3. En tu rama local: `git checkout <hash> -- zoho-survey/students/`
4. Commit y push: `git commit -m "Rollback: restaurar JSONs" && git push`

### Forzar re-build limpio
1. GitHub → Actions → **Build and Deploy Survey** → Run workflow.
2. Esto regenera todos los JSONs desde los CSVs en `data/`.
3. Verificar en GitHub Pages que los dashboards cargan.

### Revertir `periodos.json`
- Borrar el archivo y hacer push → el workflow lo regenera.
- O restaurar: `git checkout HEAD~1 -- zoho-survey/students/*/periodos.json`

### Revertir caché IA (`ia_cache.json`)
- Borrar el archivo y hacer push → se reconstruye en el próximo build (con costo de API).

---

## Checklist de Validación antes de Commitear
