# Roadmap de Mejora Técnica

## Alcance y criterio de priorización

Este roadmap se basa exclusivamente en hallazgos confirmados durante la auditoría técnica del repositorio. No propone código ni cambios de implementación; ordena el trabajo futuro por criticidad, riesgo, impacto y dependencia.

Escala de prioridad:

- **Alta**: exposición de datos, degradación de funcionalidad publicada o controles que bloquean cambios seguros.
- **Media**: deuda que aumenta el costo de mantenimiento o la probabilidad de regresiones.
- **Baja**: mejoras de eficiencia o claridad sin riesgo inmediato confirmado.

## Correcciones críticas

### C1. Exposición de comentarios originales en artefactos públicos

- **Problema detectado:** `sentimiento.json` conserva `comentario_original` y la UI cualitativa lo usa como texto abierto.
- **Evidencia:** `build_json.py` asigna `comentario_original`; `sentiment-view.js` lo muestra y busca; los JSON publicados contienen comentarios completos.
- **Impacto:** El dashboard público distribuye el texto completo de respuestas abiertas.
- **Riesgo:** Exposición de información identificable o sensible que un participante haya escrito en texto libre.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Menor superficie de privacidad y un contrato público limitado a datos necesarios para la visualización.
- **Archivos o componentes involucrados:** `zoho-survey/scripts/build_json.py`, `zoho-survey/shared/js/components/sentiment-view.js`, `sentimiento.schema.json`, `CONTRACTS.md`, JSON por periodo.
- **Dependencias:** Definición funcional de qué texto cualitativo requiere realmente la UI y política institucional de publicación de respuestas abiertas.
- **Orden recomendado:** 1.

### C2. Envío de texto original a DeepSeek antes de su redacción

- **Problema detectado:** El comentario fuente llega al prompt de DeepSeek antes de la redacción aplicada a la respuesta del modelo.
- **Evidencia:** `ia_cualitativo.py` recibe y envía `comentario`; `ia_validacion.py` redacta después los campos devueltos por la IA.
- **Impacto:** Los datos libres se transmiten a un proveedor externo aun cuando luego se redacten los fragmentos publicados.
- **Riesgo:** Incumplimiento de expectativas de privacidad, tratamiento externo de información identificable y dependencia de un tercero para datos sensibles.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Flujo cualitativo consistente con una política de minimización de datos.
- **Archivos o componentes involucrados:** `ia_cualitativo.py`, `ia_validacion.py`, `io_helper.py`, `prompts_cualitativo.py`, `SECURITY.md`, `.env.example`.
- **Dependencias:** C1 y definición institucional de datos permitidos para procesamiento externo.
- **Orden recomendado:** 2, inmediatamente después de definir el alcance de C1.

### C3. Sanitización posterior al push del CSV

- **Problema detectado:** El workflow sanitiza archivos dentro de CI, después de que un CSV activa el push.
- **Evidencia:** `build_zoho_survey.yml` ejecuta `sanitize_csv_pii.py --all`; `data/` está versionado y no ignorado.
- **Impacto:** La protección depende de que el archivo ya haya llegado al repositorio.
- **Riesgo:** Un CSV no sanitizado puede permanecer en el historial Git aunque CI produzca una versión sanitizada después.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Protección desde la entrada de datos y trazabilidad confiable de archivos fuente.
- **Archivos o componentes involucrados:** `data/`, `sanitize_csv_pii.py`, `build_zoho_survey.yml`, `.gitignore`, `SECURITY.md`, `docs/onboarding.md`.
- **Dependencias:** Política de ingestión y responsables de exportar CSV desde Zoho Survey.
- **Orden recomendado:** 3.

## Mejoras de arquitectura

### A1. Sincronización de plantilla y dashboards generados

- **Problema detectado:** Los dashboards existentes no incluyen todos los IDs cualitativos exigidos por la plantilla actual.
- **Evidencia:** `validate_generated_json.py` emitió advertencias en los tres periodos publicados para `sentimiento`, `explorador-tema` y `explorador-carrera`.
- **Impacto:** El contrato HTML no es uniforme entre periodos y la plantilla vigente.
- **Riesgo:** Regresiones parciales de la vista cualitativa y comportamiento distinto por periodo.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Un único contrato HTML verificable para todos los dashboards.
- **Archivos o componentes involucrados:** `zoho-survey/template/index.html`, HTML de cada periodo, `validate_generated_json.py`, `test_html_contract.py`.
- **Dependencias:** C1, porque el contrato cualitativo debe estabilizarse antes de regenerar periodos.
- **Orden recomendado:** 4.

### A2. Delimitación de contratos públicos e intermedios

- **Problema detectado:** Existe schema para `dataset_cualitativo.json`, pero el validador no lo incorpora; la documentación lo caracteriza de manera contradictoria.
- **Evidencia:** Hay ocho schemas en `scripts/schemas/`; `SCHEMA_BY_FILE` contiene siete entradas; `AGENTS.md` afirma que el archivo no tiene schema formal.
- **Impacto:** No está definido de forma inequívoca qué artefactos son contratos y cuáles son internos.
- **Riesgo:** Cambios incompatibles, validación incompleta y exposición accidental de datos intermedios.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Fronteras claras entre datos publicados, auditables y de procesamiento interno.
- **Archivos o componentes involucrados:** `scripts/schemas/`, `validate_generated_json.py`, `CONTRACTS.md`, `AGENTS.md`, `intermediate/`.
- **Dependencias:** C1 y A1.
- **Orden recomendado:** 5.

### A3. Determinismo de artefactos generados

- **Problema detectado:** El ETL incorpora `Timestamp.now()` en metadata de exportación.
- **Evidencia:** `build_json.py` asigna `fecha_generacion` desde la fecha de ejecución.
- **Impacto:** Reprocesar el mismo CSV puede producir diffs aun cuando los datos de encuesta no cambien.
- **Riesgo:** Commits innecesarios, menor trazabilidad y dificultad para identificar cambios reales.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Builds reproducibles y cambios generados más auditables.
- **Archivos o componentes involucrados:** `build_json.py`, `dashboard_data.schema.json`, `CONTRACTS.md`, pruebas de idempotencia.
- **Dependencias:** A2, por tratarse de metadata contractual.
- **Orden recomendado:** 6.

### A4. Reducción de concentración en orquestadores frontend

- **Problema detectado:** `dashboard.js` y `sentiment-view.js` concentran 1,270 y 1,004 líneas respectivamente.
- **Evidencia:** Mediciones directas de los módulos y dependencia de múltiples contratos DOM/JSON.
- **Impacto:** El análisis, cambios y pruebas de funciones transversales requieren intervenir archivos grandes.
- **Riesgo:** Regresiones costosas en filtros, carga de datos y visualización cualitativa.
- **Prioridad:** Media.
- **Complejidad:** Alta.
- **Beneficio esperado:** Menor acoplamiento y pruebas más focalizadas.
- **Archivos o componentes involucrados:** `dashboard.js`, `sentiment-view.js`, componentes de filtros, `template/index.html`, pruebas JS.
- **Dependencias:** A1, A2 y ampliación de cobertura de Testing T1.
- **Orden recomendado:** 12.

## Rendimiento

### R1. Priorización de carga de datos opcionales

- **Problema detectado:** El dashboard carga varios JSON opcionales durante la inicialización.
- **Evidencia:** `dashboard.js` usa `Promise.all` para endpoints críticos y otro grupo de endpoints opcionales.
- **Impacto:** El volumen inicial crece con cada periodo y con el análisis cualitativo.
- **Riesgo:** Demoras perceptibles en redes lentas y mayor transferencia de datos no requeridos de inmediato.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Carga inicial más rápida y menor consumo de recursos.
- **Archivos o componentes involucrados:** `dashboard.js`, `sentiment-view.js`, JSON por periodo, plantilla.
- **Dependencias:** C1, porque la definición del payload cualitativo altera el volumen de datos.
- **Orden recomendado:** 13.

### R2. Observabilidad de caché, tiempos y consumo IA

- **Problema detectado:** El sistema posee caché, concurrencia y métricas de tokens, pero la auditoría no encontró una línea operativa consolidada para evaluar su comportamiento real.
- **Evidencia:** `ia_cache.py` registra hits; `ia_cualitativo.py` produce tiempos, tokens y errores; el auditor no pudo acceder a logs de ejecución CI.
- **Impacto:** No se puede dimensionar con evidencia histórica la eficiencia del procesamiento cualitativo.
- **Riesgo:** Costos o tiempos de build inesperados al crecer el volumen de comentarios.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Decisiones de capacidad basadas en mediciones verificables.
- **Archivos o componentes involucrados:** `ia_cualitativo.py`, `ia_cache.py`, `ia_client.py`, workflow de build.
- **Dependencias:** C2 y acceso a resultados operativos de CI.
- **Orden recomendado:** 14.

## Seguridad

### S1. Revisión de persistencia de datos sensibles fuera del artefacto Pages

- **Problema detectado:** El workflow excluye `exports/` e `intermediate/` de Pages, pero los datos siguen siendo artefactos de repositorio o caché según el flujo.
- **Evidencia:** `build_zoho_survey.yml` elimina esos directorios antes del upload; `ia_cache.json` se conserva mediante Actions Cache.
- **Impacto:** La protección de Pages no equivale a una política completa de retención y acceso.
- **Riesgo:** Acceso indebido a datos de auditoría o a resultados de IA fuera del sitio publicado.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Gestión coherente de datos en repositorio, artefactos y cachés.
- **Archivos o componentes involucrados:** `build_zoho_survey.yml`, `ia_cache.py`, `csv_exporter.py`, `.gitignore`, `SECURITY.md`.
- **Dependencias:** C1, C2 y C3.
- **Orden recomendado:** 7.

### S2. Inventario de sinks `innerHTML` y origen de datos

- **Problema detectado:** El frontend y `health.html` usan múltiples asignaciones a `innerHTML`.
- **Evidencia:** Búsqueda estática en `dashboard.js`, `sentiment-view.js`, componentes y `health.html`; existe `SurveySanitizer` como control compartido.
- **Impacto:** La seguridad depende de que cada flujo aplique correctamente el saneamiento.
- **Riesgo:** XSS si un contrato JSON o `periodos.json` introduce texto no controlado.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Trazabilidad de datos renderizados y menor riesgo de omisiones de saneamiento.
- **Archivos o componentes involucrados:** `utils/sanitizer.js`, `dashboard.js`, `sentiment-view.js`, `health.html`, `loader.js`.
- **Dependencias:** A2 y Testing T2.
- **Orden recomendado:** 8.

## Calidad del código

### Q1. Convertir lint informativo en una línea base gobernada

- **Problema detectado:** Ruff y ESLint se ejecutan sin bloquear el pipeline.
- **Evidencia:** `tests.yml` contiene `--exit-zero` y `|| true` para ambos linters.
- **Impacto:** Las advertencias no detienen regresiones de calidad.
- **Riesgo:** Aumento sostenido de deuda y fallos detectables tarde.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Calidad mínima verificable en cada cambio.
- **Archivos o componentes involucrados:** `ruff.toml`, `.eslintrc.json`, `tests.yml`, fuentes Python y JS.
- **Dependencias:** Línea base de resultados y Testing T1.
- **Orden recomendado:** 9.

### Q2. Eliminar referencias heredadas verificadas

- **Problema detectado:** Persisten referencias a motor legacy, fallback, workflows y contratos inexistentes.
- **Evidencia:** `.env.example`, `docs/developer-guide.md`, `students/JSON_SCHEMA.md`, `students/README.md`, comentarios de `build_zoho_survey.yml` y `AGENTS.md`.
- **Impacto:** El código parece tener comportamientos que ya no existen.
- **Riesgo:** Cambios incorrectos, diagnósticos equivocados y mantenimiento duplicado.
- **Prioridad:** Alta.
- **Complejidad:** Baja.
- **Beneficio esperado:** Menor ambigüedad operativa y reducción de deuda documental/técnica.
- **Archivos o componentes involucrados:** `.env.example`, `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `CONTRACTS.md`, `docs/`, workflows.
- **Dependencias:** A2 para distinguir con precisión contratos activos e históricos.
- **Orden recomendado:** 10.

## Testing

### T1. Cobertura de integración para el motor IA y exportaciones

- **Problema detectado:** Hay pruebas directas para caché, filtro y validación, pero no cobertura dedicada comprobada para `ia_cualitativo`, `prompts_cualitativo`, `ia_client` y `csv_exporter`.
- **Evidencia:** Inventario de `scripts/tests/` y módulos activos en `scripts/lib/`.
- **Impacto:** Las rutas de integración con proveedor externo y exportaciones tienen menor protección ante cambios.
- **Riesgo:** Fallas de procesamiento o privacidad detectadas recién en CI o producción.
- **Prioridad:** Alta.
- **Complejidad:** Media.
- **Beneficio esperado:** Regresiones detectadas antes de generar o publicar artefactos.
- **Archivos o componentes involucrados:** módulos IA, `csv_exporter.py`, pruebas Python, fixtures controladas.
- **Dependencias:** C1 y C2, porque los contratos de texto deben estabilizarse primero.
- **Orden recomendado:** 11.

### T2. Pruebas de contratos HTML, accesibilidad y UI cualitativa

- **Problema detectado:** Los tests detectan orden de scripts e IDs, pero existen advertencias en dashboards; la suite DOM no pudo ejecutarse localmente por ausencia de `jsdom`.
- **Evidencia:** advertencias de `validate_generated_json.py`; `tests.yml` ejecuta `test-dom.js`; dependencia `jsdom` no está instalada en el clon auditado.
- **Impacto:** La integridad del contrato visual no está demostrada en todos los periodos en el entorno local.
- **Riesgo:** Degradaciones de accesibilidad y UI no detectadas por validación de JSON.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Mayor seguridad al cambiar IDs, filtros, tooltips y vistas cualitativas.
- **Archivos o componentes involucrados:** `template/index.html`, HTML de periodos, `tests/unit/test-dom.js`, `test_html_contract.py`, componentes JS.
- **Dependencias:** A1 y disponibilidad reproducible de dependencias de test.
- **Orden recomendado:** 15.

## Documentación

### D1. Consolidación de fuentes canónicas

- **Problema detectado:** Coexisten documentos canónicos, históricos y operativos con afirmaciones incompatibles.
- **Evidencia:** `JSON_SCHEMA.md` se declara histórico pero describe workflow inexistente; `AGENTS.md` contradice el API real de tooltip y el número de schemas; `.env.example` describe fallback eliminado.
- **Impacto:** No es posible confiar en una lectura aislada para operar el sistema.
- **Riesgo:** Decisiones técnicas erróneas y documentación divergente en cada cambio.
- **Prioridad:** Alta.
- **Complejidad:** Baja.
- **Beneficio esperado:** Contexto único y fiable para desarrolladores, analistas y agentes.
- **Archivos o componentes involucrados:** `README.md`, `ARCHITECTURE.md`, `CONTRACTS.md`, `AGENTS.md`, `docs/`, `zoho-survey/students/*.md`, `.env.example`.
- **Dependencias:** A2 y Q2.
- **Orden recomendado:** 16.

## DevOps

### O1. Claridad de artefacto y post-despliegue

- **Problema detectado:** El workflow despliega antes de confirmar los artefactos generados en `main`; el health check posterior solo informa y usa respuestas HEAD.
- **Evidencia:** orden de pasos en `build_zoho_survey.yml`; implementación de `health.html`.
- **Impacto:** El artifact desplegado y el estado confirmado de rama pueden diferir temporalmente; el health check no comprueba semántica de datos.
- **Riesgo:** Diagnóstico ambiguo de incidentes y diferencias entre lo desplegado y lo versionado.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Mayor trazabilidad del ciclo build, deploy y confirmación.
- **Archivos o componentes involucrados:** `build_zoho_survey.yml`, `health.html`, `validate_generated_json.py`.
- **Dependencias:** A1, A2 y T1.
- **Orden recomendado:** 17.

### O2. Reproducibilidad de dependencias de desarrollo y CI

- **Problema detectado:** Las dependencias Python usan rangos mínimos y las pruebas DOM requieren una dependencia no instalada en el clon auditado.
- **Evidencia:** `requirements.txt` usa `>=`; `package.json` declara `jsdom`; la ejecución local de `test:js:dom` no pudo iniciarse sin ella.
- **Impacto:** El resultado local puede variar respecto de CI.
- **Riesgo:** Diagnósticos inconsistentes y dificultades para reproducir fallas.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Entornos verificables y resultados consistentes entre equipos.
- **Archivos o componentes involucrados:** `requirements.txt`, `package-lock.json`, `package.json`, workflows, onboarding.
- **Dependencias:** D1.
- **Orden recomendado:** 18.

## Experiencia de usuario

### U1. Estados funcionales para datos ausentes o inconsistentes

- **Problema detectado:** Existen encuestas placeholder, periodos heterogéneos y advertencias cualitativas no bloqueantes.
- **Evidencia:** `periodos.json` de posgrado apunta a `underconstruction.html`; `health.html` contempla tipos sin datos; JSON por periodo presenta distinta cantidad de archivos.
- **Impacto:** La experiencia puede variar entre encuestas y periodos según el estado de sus artefactos.
- **Riesgo:** Mensajes ambiguos o secciones incompletas para usuarios finales.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Comportamiento predecible ante ausencia de datos, periodos próximos y módulos opcionales.
- **Archivos o componentes involucrados:** `loader.js`, `underconstruction.html`, `health.html`, `dashboard.js`, plantilla, `periodos.json`.
- **Dependencias:** A1, A2 y T2.
- **Orden recomendado:** 19.

### U2. Verificación funcional de accesibilidad en componentes dinámicos

- **Problema detectado:** El repositorio contiene ARIA, enlace de salto y APIs de tooltip, pero no se confirmó la interacción completa en navegador publicado.
- **Evidencia:** HTML y componentes contienen atributos de accesibilidad; el sitio publicado no fue accesible desde el navegador de auditoría y la suite DOM no se ejecutó localmente.
- **Impacto:** El cumplimiento funcional de teclado, foco y lector de pantalla permanece parcialmente no verificado.
- **Riesgo:** Barreras de uso para usuarios que dependen de tecnologías de asistencia.
- **Prioridad:** Media.
- **Complejidad:** Media.
- **Beneficio esperado:** Experiencia consistente para navegación por teclado y tecnologías asistivas.
- **Archivos o componentes involucrados:** `loader.js`, `custom-select.js`, `multiselect.js`, `tooltip.js`, plantilla, CSS compartido y pruebas DOM.
- **Dependencias:** T2 y disponibilidad de entorno de prueba reproducible.
- **Orden recomendado:** 20.

## Roadmap por fases

### Fase 1: Protección de datos y contrato cualitativo

**Orden:** C1, C2, C3, S1.

La primera fase contiene los únicos riesgos confirmados que involucran texto libre, proveedor externo, repositorio y artefactos de publicación. Debe concluir antes de regenerar dashboards o ampliar el motor IA, porque define qué información puede procesarse, almacenarse y mostrarse.

### Fase 2: Consistencia contractual y línea base de calidad

**Orden:** A1, A2, A3, S2, Q1, Q2.

Con el alcance de datos definido, se estabilizan los contratos HTML/JSON y la reproducibilidad de artefactos. Luego se convierte la calidad existente en una línea base observable y se eliminan referencias heredadas que contradicen la arquitectura actual.

### Fase 3: Cobertura verificable y mantenibilidad interna

**Orden:** T1, A4, R1, R2, T2.

Esta fase fortalece primero las pruebas que protegen la integración IA y exportaciones. Solo después es razonable reducir la concentración de lógica frontend y ajustar carga de datos, porque ambas actividades necesitan redes de seguridad y métricas confiables.

### Fase 4: Operación, documentación final y experiencia integral

**Orden:** D1, O1, O2, U1, U2.

La fase final consolida la operación: documentación canónica, trazabilidad de despliegue, entornos reproducibles y validación de la experiencia para encuestas completas, placeholders y accesibilidad. Se ubica al final porque depende de contratos, pruebas y comportamientos ya estabilizados.

## Criterio de salida por fase

- **Fase 1:** No existe texto original no autorizado en los artefactos ni en el flujo externo de IA; la ingestión de CSV sigue una política definida.
- **Fase 2:** Plantilla, periodos, schemas, validador y documentación describen el mismo contrato.
- **Fase 3:** Las rutas críticas tienen cobertura suficiente para intervenir los orquestadores con riesgo controlado.
- **Fase 4:** El ciclo de entrega es trazable, reproducible y comprensible para equipos técnicos y usuarios finales.
