# Changelog

Historial de cambios significativos del proyecto. Basado en [Keep a Changelog](https://keepachangelog.com/).

## [3.0.6] — 2026-06-23

### Fixed
- Agregado el mapeo de dimensiones faltantes (Académico, Administrativo y Bienestar, Infraestructura, Tecnología) a la constante `CATEGORIA_DIMENSION_GRADUADO` en `config.py` para asegurar que el pipeline ETL procese correctamente los datos y se rendericen los visuales de nivel de satisfacción y visibilidad de servicios en "Graduados Pregrado".

---

## [3.0.5] — 2026-06-23

### Changed
- Cambio del filtro "Tema" a "Tema Padre" en "Detalle de ideas", actualizando la etiqueta en todos los periodos y el selector dinámico de JavaScript para agrupar y filtrar comentarios mediante categorías de nivel superior (`c.categoria_padre || c.categoria`).
- Redistribución de anchos de columna en la tabla del explorador de comentarios (Carrera: 16%, Ciclo: 5%, NPS: 5%, Texto abierto: 34%, Idea analizada: 18%, Tema: 12%, Sentimiento: 5%, Intensidad: 5%).
- Modificación del renderizador de tabla cualitativa en `sentiment-view.js` para asegurar que la columna "Tema" muestre explícitamente el subtema/aspecto (`c.categoria`) en lugar del tema padre, y quitar el formato en negrita (font-weight:600) de la columna "Carrera".

### Fixed
- Reversión de los filtros redundantes agregados erróneamente en "Detalle de ideas" (Facultad, Carrera, Ciclo, Limpiar).
- Corrección de formato para el input de búsqueda de comentarios (`#explorador-search`) heredando la fuente institucional (`Roboto`) y tamaño de texto (`12px` / `var(--text-md)`), removiendo el icono de chevron y ajustando padding simétrico.
- Corrección de cálculo en la tabla "Respuestas por carrera — distribución NPS completa" (`renderCareerNPSTable`), diferenciando correctamente el número de comentarios únicos ("Texto abierto" usando Set de IDs) respecto al número total de fragmentos ("Ideas analizadas").
- Simplificación del validador de contratos JSON (`validate_generated_json.py`) y del archivo de esquema (`sentimiento.schema.json`) para ajustar el objeto de tópicos al contrato simplificado v3.0 (`topico`, `total_comentarios`, `positivos`, `negativos`, `neutros`).
- Actualización de documentación de contratos en `CONTRACTS.md` y `JSON_SCHEMA.md` para reflejar la eliminación de atributos obsoletos en tópicos y la remoción de filtros redundantes en el HTML de los periodos.

### Removed
- Eliminación del interruptor/checkbox de texto corregido (`#explorador-toggle-texto`) en "Detalle de ideas" de la plantilla y todas las páginas de periodos, configurando el visor para mostrar siempre la idea analizada (corregida) por defecto.

---

## [3.0.4] — 2026-06-23

### Fixed
- Remoción de los contenedores de filtros redundantes (`sent-aspectos`, `sent-npscarrera`, `sent-tabla`) en la sección de Análisis Cualitativo, centralizando el estado de filtrado hacia el selector global (`sent`) para simplificar la interacción.
- Corrección de la estructura de anidamiento en la lectura de `sentimiento.json` en `sentiment-view.js`. La función `init` ahora lee los comentarios desde la raíz del JSON sin requerir la clave `por_ciclo`, evitando sobrescrituras silenciosas de la variable global de comentarios.
- Corrección del desajuste de IDs estáticos del DOM ( `intensidad-positivos-container` e `intensidad-negativos-container`) y la función JavaScript `_renderList` que impedían el renderizado visual de los gráficos de intensidad de aspectos.
- Incorporación de reglas defensivas de strings ('todas') en `getFilteredSubset` para evitar filtros huérfanos que truncaban silenciosamente los paneles "Aspectos más positivos", "Aspectos más negativos" y "Respuestas por carrera" tras retenciones agresivas de estado local en ciertos navegadores.

---

## [3.0.3] — 2026-06-12

### Added
- Calibración de neutralidad sensible en el clasificador cualitativo (`nlp.py`), reduciendo el umbral de neutralidad de `abs(diff) < 0.20` a `abs(diff) < 0.12`. Esta calibración fue seleccionada tras evaluar experimentalmente cuatro escenarios, logrando un acierto del 66% general y 84% en la clasificación de quejas (Neutro → Negativo), recuperando críticas valiosas que antes quedaban ocultas.

### Changed
- Regeneración completa de los datasets de comentarios `sentimiento.json` para pregrado y graduados aplicando la nueva sensibilidad de polaridad, sin introducir cambios en la arquitectura de embeddings, tópicos ni en el esquema contractual.

### Backlog (Futuras Oportunidades)
- Implementación de reglas semánticas para prevenir falsos negativos ante declaraciones de desconocimiento ("no conozco", "no utilizo").
- Implementación de reglas lingüísticas de negación ("no ... bien", "dista de", "carece de") previas al embedding para mitigar falsos positivos.

---

## [3.0.2] — 2026-06-12

### Added
- Optimización de inferencia semántica por lotes (batch inference) en `nlp.py` con SentenceTransformers utilizando `batch_size=32`. Consigue paridad matemática del 100% de clasificaciones (sentimiento, categoría, tópico y fragmento) y reduce los tiempos de ejecución de build drásticamente.

### Changed
- Consolidación definitiva del módulo cualitativo v3.0: se retira el flag `USE_V3_SENTIMENT` del frontend y se unifican las llamadas de datos de comentarios cualitativos directamente sobre `sentimiento.json`.
- Minificación selectiva aplicada en el ETL (`build_json.py`) para los JSON de alto peso (`dimensiones.json`, `sentimiento.json`, `nps_ciclo_carrera.json`, `csat_ciclo_carrera.json`), disminuyendo en más de 160,000 líneas en blanco el volumen de transferencia sobre GitHub Pages, mientras se preservan legibles los JSON estructurales de filtros e identificadores.
- `validate_generated_json.py` actualizado para hacer obligatorio el esquema cualitativo de `sentimiento.json` (v3.0) y retirar la coexistencia paralela de `sentimiento_v3.json`.
- `CONTRACTS.md` y `ARCHITECTURE.md` actualizados para formalizar los nuevos esquemas contractuales y advertir que `nps_carrera.json` y `csat_carrera.json` continúan activos únicamente como fallback de carga síncrona en encuestas sin ciclos (`has_ciclo=false`).

### Removed
- Eliminación de archivos temporales redundantes `sentimiento_v3.json` y del cargador de fallback legacy `renderTablaSentimientoCarrera()` del frontend.

---

## [2.0.3] — 2026-06-11

### Added
- Persistencia del estado de navegación mediante `localStorage`, almacenando el tipo de encuesta (`ulima_selected_survey`) y el período seleccionado por tipo de encuesta (`ulima_selected_period_[survey_id]`).
- Navegación dinámica y adaptativa en la barra superior (`loader.js`): al seleccionar un elemento oculto dentro del menú desplegable "MÁS", este se fuerza a ser visible intercambiándose por el último elemento visible.
- Atributos semánticos ARIA en el menú desplegable "MÁS" (`aria-haspopup`, `aria-expanded`, `role="menu"`, `role="menuitem"`) para mejorar la accesibilidad de lectores de pantalla.
- Lógica de preservación y transferencia de foco para que al interactuar mediante teclado en el menú "MÁS", el foco se reasigne correctamente en lugar de perderse por la reestructuración del DOM.

### Changed
- `loader.js`: Se invocan los métodos `.schedule()` de reordenamiento de los objetos de overflow tras cambiar de encuesta o periodo académico para asegurar la reevaluación inmediata de anchos y visibilidad.

### Fixed
- Corrección de grosor asimétrico en barras de desplazamiento de `.table-scroll`: unificados los grosores horizontal (`height: 6px`) y vertical (`width: 6px`) en selectores webkit y añadidas propiedades estándar `scrollbar-*` de grosor delgado (`thin`) y combinación de color institucional como fallback para Firefox.

---

## [2.0.2] — 2026-06-11

### Added
- Cabecera fija (sticky header) responsiva en las tablas `.survey-table` del Análisis Detallado para mejorar la legibilidad durante el scroll vertical.

### Changed
- `layout.css`: Definido el token de altura `--sticky-header-h: 45px;` en `:root` y configurado `.sticky-header` con `height: var(--sticky-header-h)` para garantizar una altura fija y uniforme libre de variaciones por renderizado tipográfico.
- `components.css`: Configurado `.survey-table th` con `position: sticky`, `top: calc(var(--sticky-header-h) - 1px)` y `z-index: 10`, aplicando un solapamiento de seguridad de 1px para evitar filtraciones de texto.
- `components.css`: Ajustado el breakpoint de desktop en `.table-scroll` de `821px` a `769px` para alinear con el sistema de breakpoints.
- `sections.css`: Redefinida la variable `--sticky-header-h` en media queries de tablet y mobile. Configurado `.table-scroll` con `max-height` (`380px` en tablet, `300px` en mobile) y `overflow-y: auto`, y reajustado `.survey-table th` a `top: 0` para mantener las cabeceras fijas dentro de su propio contenedor de scroll en dispositivos móviles y evitar que se desactiven por el `overflow-x: auto`.

---

## [2.0.1] — 2026-06-10

### Added
- Documentación de subcomponentes JS modularizados (`filter-controller.js`, `radar-chart.js`, `sentiment-view.js`) en [ARCHITECTURE.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/ARCHITECTURE.md).
- Detalle del subdirectorio Python `scripts/lib/` y sus 4 submódulos en [ARCHITECTURE.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/ARCHITECTURE.md).
- Documentación de los workflows de CI/CD (`build_students.yml`, `deploy-legacy.yml`, `validate-survey-json.yml`) en [ARCHITECTURE.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/ARCHITECTURE.md).
- Advertencia técnica sobre el orden de dependencias en el cargador JS (`dom-helpers.js` antes de `custom-select.js`) en [docs/developer-guide.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/docs/developer-guide.md).

### Fixed
- Contratos de datos en [CONTRACTS.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/CONTRACTS.md): Unificación de claves NPS a minúsculas (`promotores`, `pasivos`, `detractores`) para concordar con la implementación real del ETL.
- Definición de propiedad en `ids.json` de [CONTRACTS.md](file:///q:/ANALISTA%20DE%20DATOS/6.%20Encuesta%20de%20Satisfacci%C3%B3n/6.11%20GitHub/survey-storytelling/CONTRACTS.md): Corrección de `count` a `total` para reflejar la salida del backend.
- Carga de dependencias en el portal principal `index.html` (importación de `dom-helpers.js` añadida para solventar error de carga en `custom-select`).
- Referencias de espacio de nombres en `radar-chart.js` (añadido alias `_dh` para métodos utilitarios de DOM).
- Centrado y redimensión del gráfico de radar general: Ajuste dinámico de `viewBox` (`-80 0 760 500`) en SVG y `aspect-ratio` (`76 / 50`) en CSS para maximizar su tamaño (un 60% más grande) y eliminar el espacio vacío superior/inferior.
- Solapamiento de etiquetas en el radar: Algoritmo de dos pasadas para espaciado vertical mínimo (`15px`) y proyección circular adaptativa de textos polares/laterales.

---

## [2.0.0] — 2026-06-03

### Added
- Sanitización HTML (`escapeHTML`, `sanitizeHTML`) para prevención de XSS
- 8 módulos JS independientes: `constants.js`, `formatters.js`, `sanitizer.js`, `dom-helpers.js`, `tooltip.js`, `progress-bar.js`, `custom-select.js`, `multiselect.js`
- CSS modularizado en 5 capas: `tokens.css`, `reset.css`, `layout.css`, `components.css`, `sections.css`
- 34 tests unitarios con framework `test-framework.js` + runner HTML
- 3 JSON Schemas (draft-07): `dashboard_data`, `filtros`, `sentimiento`
- `lib/config.py` con configuración ETL externalizada
- `docs/ai-agent-guide.md` — guía para DeepSeek, Claude, Copilot
- Variables CSS de capa z-index (`--z-base` a `--z-splash`)
- `LOADER_CONFIG` en loader.js con constantes externalizadas
- `SURVEY_CONFIG` ampliado con `MAX_CICLOS_DEFAULT/ESPECIALES`, `RADAR_LABEL_MAXLEN`, etc.
- `version: "2.0"` en `dashboard_data.json`, `filtros.json`, `sentimiento.json`

### Changed
- `dashboard.js`: monolito 1717 líneas → orquestador que delega en 8 módulos con fallback inline
- `dashboard.css`: monolito 1176 líneas → entry point 16 líneas con `@import`
- ETL: 14→9 archivos JSON por periodo (eliminados `resumen.json`, `nps.json`, `csat.json`, `nps_ciclo.json`, `csat_ciclo.json`)
- `loader.css`: `DM Sans` → `Roboto`, `--font-family` variable agregada, `#fff` → `var(--white)`
- `etapa_map`: ciclo 6° corregido de "Intermedio" → "Avanzado" (según documento de contexto)
- `build_json.py` y `validate_generated_json.py`: paths corregidos (doble anidamiento `zoho-survey/zoho-survey/`)
- `package.json`: versión `2.0.0`, script `validate:json` corregido
- `loader.js`: strings y timeouts externalizados a `LOADER_CONFIG`

### Removed
- 15 archivos JSON legacy del repositorio (5 por periodo × 3 periodos)
- 4 archivos `.txt` placeholder en `posgraduate/`
- 4 archivos `.md` obsoletos/duplicados: `docs/architecture-overview.md`, `zoho-survey/shared/README.md`, `MIGRATION.md`, `zoho-survey/students/JSON_SCHEMA.md`

### Fixed
- XSS en `showTooltip()` — sanitización con whitelist de tags
- `PERIODS` mutable en `loader.js` documentado como variable de estado
- Hardcoded colors: `#F37021` → `var(--splash-bg)`, `#000000` → `var(--black)`
- Duplicación de `getSelectedValues`/`setSelectedValues` en 3 archivos → `utils/dom-helpers.js`
- **Header/loader redesign**: CSS Grid body layout elimina `position:fixed` y `--bar-h` hardcodeado
- **Iframe height bug**: `#frame-wrap` ahora usa grid `1fr` en vez de `top: 96px`, adaptándose automáticamente a la altura real del `#topbar`
- **Responsive**: agregado breakpoint 820px, corregidos gaps/paddings en 960px y 640px
- **Mobile selects**: integrado `SurveyCustomSelect` con tema oscuro institucional (fondo `#2a221c`, hover `--ulima-orange`, sin fondo blanco ni azul nativo)
- **Duplicate CSS**: eliminado segundo bloque `.survey-tab` en `loader.css`
- **Header visual polish (2ª iteración)**: gap vertical `.topbar-right` 1px→6px, badge NUEVO reposicionado debajo del pill, labels uniformizadas (11px), añadida etiqueta simétrica "ENCUESTA" junto a "PERIODO", font-size escalado en 3 breakpoints

### Migration Notes
- Patrón de delegación con fallback inline: backward compatible con dashboards existentes
- Todos los dashboards cargan sin los nuevos scripts (fallback inline en dashboard.js)
- Rollback disponible vía `git restore` por archivo
- Tag `v-pre-refactor` creado como punto de restauración

---

## [1.0.0] — 2025
- Versión inicial con dashboard monolítico
- ETL: CSV → 14 JSONs por periodo
- 4 secciones: Ejecutivo, Operativo, Detallado, Cualitativo
- Deploy en GitHub Pages vía `deploy-legacy.yml`
