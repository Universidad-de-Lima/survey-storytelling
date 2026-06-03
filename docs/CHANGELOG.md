# Changelog

Historial de cambios significativos del proyecto. Basado en [Keep a Changelog](https://keepachangelog.com/).

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
