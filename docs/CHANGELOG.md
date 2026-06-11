# Changelog

Historial de cambios significativos del proyecto. Basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [2.0.2] — 2026-06-11

### Added
- Cabecera fija (sticky header) responsiva en las tablas `.survey-table` del Análisis Detallado para mejorar la legibilidad durante el scroll vertical.

### Changed
- `components.css`: Configurado `.survey-table th` con `position: sticky`, `top: 47px` y `z-index: 10`.
- `components.css`: Ajustado el breakpoint de desktop en `.table-scroll` de `821px` a `769px` para alinear con el sistema de breakpoints.
- `sections.css`: Añadidos offsets `top` responsivos para `.survey-table th` en tablet (`57px` en `max-width: 768px`) y mobile (`38px` en `max-width: 480px`).

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
