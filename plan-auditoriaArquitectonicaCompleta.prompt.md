# Plan: Auditoría Arquitectónica Completa — survey-storytelling

## TL;DR
Auditoría integral del sistema estático de visualización de encuestas (CSV→JSON→HTML/CSS/JS→GitHub Pages) que identifica fortalezas, debilidades, riesgos y propone una arquitectura objetivo pragmática con roadmap de migración priorizado.

---

# Fase 0 — Comprensión del Proyecto

## Propósito del Proyecto
Sistema estático de visualización y storytelling para encuestas de satisfacción de la Universidad de Lima. Transforma exportaciones CSV de Zoho Survey en dashboards interactivos desplegados en GitHub Pages, sin backend ni dependencias runtime.

## Flujo Funcional Principal
1. Usuario accede a `zoho-survey/index.html` → loader.js detecta tipo de encuesta y periodo
2. Selecciona periodo → iframe carga el dashboard correspondiente
3. Dashboard (`index.html` del periodo) ejecuta `dashboard.js`
4. `dashboard.js` carga 7-14 archivos JSON desde `./json/`
5. Renderiza 4 secciones: Ejecutivo, Operativo, Detallado, Cualitativo
6. Filtros cascada (Facultad→Carrera→Ciclo) permiten drill-down

## Flujo de Datos
```
CSV (Zoho Survey) → build_json.py → 12+ JSON files → dashboard.js → DOM render
                         ↓
                validate_generated_json.py (CI)
                         ↓
                periodos.json (auto-generated nav manifest)
```

## Documentación Existente
- AGENTS.md: Reglas de proyecto, JSON, ETL, GitHub Actions, estrategia refactor
- ARCHITECTURE.md: Mapa componentes, pipeline, patrones, deuda técnica
- CONTRACTS.md: Esquemas entrada/salida, invariantes
- README.md: Descripción general, estructura, dependencias
- zoho-survey/scripts/README.md: Documentación ETL
- zoho-survey/shared/README.md: Componentes reutilizables
- zoho-survey/students/README.md: Módulo estudiantil
- zoho-survey/students/FILTER_LOGIC.md: Lógica filtros cascada
- zoho-survey/students/JSON_SCHEMA.md: Contratos JSON dashboard

## Convenciones Actuales
- CamelCase para JS, kebab-case para CSS/HTML IDs
- IIFE para encapsulamiento JS (no ES modules)
- JSON compacto, sin redundancia, backward-compatible
- build_json.py como única fuente de transformación
- Separación estricta datos/vista (JSON ↔ JS)
- Delegación de eventos para filtros
- Registry centralizado de referencias DOM

## Restricciones Técnicas Observadas
- Sitio 100% estático (GitHub Pages)
- Sin frameworks JS (Vanilla only)
- Sin bundlers/transpilers
- Python solo para ETL
- JSON como único formato de intercambio
- Navegadores modernos ES6+ sin transpilación
- Node >= 18 solo para scripts npm auxiliares

---

# Fase 1 — Auditoría de la Arquitectura Actual

## 1.1 Estructura General

### Hechos Observados
- Raíz: 7 archivos + 4 directorios (.git, .github, data, zoho-survey)
- `template/` referenciado en docs pero NO EXISTE en el filesystem
- `zoho-survey/` contiene: index.html, underconstruction.html, 6 carpetas de dominio (alumni, employers, facultyStaff, nonfacultyStaff, students, shared, scripts)
- `shared/` contiene CSS, JS e imágenes reutilizables
- `scripts/` contiene Python ETL (fuera de `students/`, compartido)
- Cada periodo tiene su propio `index.html` + `json/` con 14 archivos
- 6 de 9 tipos de encuesta son placeholders (solo students/graduate y students/undergraduate activos)

### Inferencias
- La estructura crece horizontalmente por periodo (nuevo dir por cada ciclo)
- No hay mecanismo de herencia de templates (cada index.html es copia independiente)
- La ausencia de `template/` sugiere que el script build_json.py copia de un periodo existente o espera el directorio pero no lo crea
- Los placeholders sugieren un roadmap de expansión pero sin datos aún

### Fortalezas
- Separación clara entre fuente (data/), transformación (scripts/), presentación (shared/) y dominio (students/, alumni/, etc.)
- Shared assets correctamente centralizados
- Documentación exhaustiva para agentes IA

### Debilidades
- **Crítico**: template/index.html no existe → cada nuevo periodo requiere copia manual
- 6/9 módulos son placeholders (sobre-estructura para datos inexistentes)
- index.html de dashboard duplicado 3 veces (100% idéntico entre periodos)
- CSS y JS en shared/ pero HTML de dashboard no (está duplicado en cada periodo)

## 1.2 HTML

### Hechos Observados
- `zoho-survey/index.html` (55 líneas): Contenedor loader con iframe. Sin `<nav>`, sin `<main>`, sin ARIA labels, iframe sin title
- `zoho-survey/underconstruction.html` (40 líneas): Página estática con CSS inline (~20 líneas en `<style>`)
- Dashboards (3 archivos, ~530 líneas cada uno): Excelente semántica, `<nav>`, `<main>`, `<section>`x4, skip-link, ARIA labels, labels explícitos
- Los 3 dashboards son 100% idénticos en estructura HTML
- 80+ IDs por dashboard, 150+ clases
- Solo 1 uso de data-attributes (`data-multiselect="true"`)

### Inferencias
- El loader se desarrolló antes de madurar las prácticas de accesibilidad
- Los dashboards recibieron atención cuidadosa de accesibilidad pero a costa de duplicación
- El equipo probablemente copió el HTML del primer dashboard (2025-2) para crear 2026-1 y graduate/2026
- Bajo uso de data-attributes indica que el JS depende fuertemente de IDs (acoplamiento)

### Fortalezas
- Dashboard HTML semánticamente excelente (reference implementation)
- Accesibilidad muy cuidada: aria-label (15+), aria-labelledby (4+), role="group", aria-live, skip-link
- Screen-reader-only content
- Meta description presente, lang="es-PE", theme-color

### Debilidades
- Duplicación 3x del HTML de dashboard (530 líneas × 3 = 1590 líneas idénticas)
- Loader HTML sin semántica ni accesibilidad
- underconstruction.html con CSS inline (mala práctica)
- Sin Open Graph tags
- Sin canonical tags
- Sin preload de recursos críticos

### Riesgos Técnicos
- **Alto**: Cambio en estructura HTML requiere modificar 3+ archivos idénticos → riesgo de divergencia
- **Medio**: Iframe sin title → falla validación WCAG
- **Bajo**: Sin OG tags → poor social media preview

## 1.3 CSS

### Hechos Observados
- `dashboard.css`: ~1350 líneas. Sistema de design tokens con 25+ variables CSS. Organizado por secciones con comentarios. Flexbox + Grid. 3 breakpoints responsive.
- `loader.css`: ~270 líneas. Tema oscuro. 2 breakpoints. 
- Bloque de 20 líneas duplicado entre ambos: `.survey-tab` + `.survey-select`
- Animación `stackedGrow` aplicada a 3 selectores distintos
- Uso de `#000000` en lugar de `--gray-900` en algunos lugares
- Sin preprocesador, sin post-procesador (Vanilla CSS)

### Inferencias
- Las variables CSS son la estrategia de theming (correcto para el stack)
- La duplicación entre dashboard.css y loader.css sugiere desarrollo en silos
- No hay un sistema de componentes CSS (cada sección define sus propios estilos)
- La organización por secciones es funcional pero no escala bien con más dashboards

### Fortalezas
- Excelente uso de CSS custom properties (design tokens)
- Comentarios de sección claros
- Layout responsive funcional
- Focus outlines accesibles
- Clases sr-only para screen readers

### Debilidades
- Duplicación entre dashboard.css y loader.css
- Sin strategy de componentes (cada sección re-estiliza elementos similares)
- Valores hardcodeados ocasionales
- Selectores de especificidad media-alta (`.filter-container:has(.open)`)
- Sin minificación en producción

### Riesgos Técnicos
- **Medio**: Duplicación CSS crecerá con más dashboards si no se extraen componentes comunes
- **Bajo**: Especificidad de selectores puede causar problemas al extender

## 1.4 JavaScript

### Hechos Observados
- `dashboard.js`: ~2550 líneas. IIFE autoejecutado. 50+ funciones. Cache global con 9 endpoints. DOM registry. Sin dependencias externas.
- `loader.js`: ~200 líneas. IIFE. Manejo de iframe, fetch periodos.json, navegación.
- 6 constantes hardcodeadas: BASE_URL, META_NPS, META_CSAT, CARRERAS_12_CICLOS, FACULTADES_12_CICLOS, PROGRAMA_ESTUDIOS_GENERALES
- 5 grupos de filtros con lógica duplicada (top3, radar, preguntas, detalle, visibilidad, sent)
- adjustSegmentLabels(): ~200 líneas, detecta colisiones, timeout fijo 1200ms
- renderRadarIndependiente(): ~150 líneas, SVG como string HTML
- XSS potencial: `tooltip.innerHTML = content` sin sanitización
- Sin cleanup de event listeners en re-renders
- Sin tests

### Inferencias
- El IIFE fue una decisión consciente para evitar conflictos globales sin build step
- La falta de modularización sugiere que el archivo creció orgánicamente
- Las funciones de renderizado son las más complejas y menos mantenibles
- La duplicación de lógica de filtros (5×) indica que no se abstrajo a tiempo
- El patrón de tooltip es el punto más frágil (XSS + posicionamiento)

### Fortalezas
- Encapsulamiento completo (IIFE)
- Sin dependencias externas (autosuficiente)
- Cache de datos eficiente (9 endpoints, una sola carga)
- Delegación de eventos para filtros
- DOM registry para referencias rápidas
- Funciones de formato utilitarias consistentes

### Debilidades
- **Crítico**: XSS en tooltip (innerHTML sin sanitizar)
- **Alto**: Archivo monolítico (2550 líneas) difícil de mantener
- **Alto**: Sin tests → cambios son riesgosos
- **Medio**: Lógica de filtros duplicada 5 veces
- **Medio**: adjustSegmentLabels demasiado complejo (~200 líneas)
- **Medio**: SVG rendering con string concatenation en lugar de DOM API
- **Medio**: Event listeners sin cleanup (memory leaks potenciales)
- **Medio**: Constantes hardcodeadas que deberían ser configuración
- **Bajo**: Sin manejo de errores visible para el usuario (solo console.error)

### Riesgos Técnicos
- **Crítico**: XSS en tooltip → posible vector de ataque si datos JSON son comprometidos
- **Alto**: Monolito JS → cada cambio requiere entender 2550 líneas
- **Alto**: Sin tests → regresiones no detectadas
- **Medio**: Memory leaks por listeners no limpiados
- **Medio**: Lógica de ciclos hardcodeada → nuevo plan de estudios = código roto

## 1.5 Datos (JSON)

### Hechos Observados
- 51 archivos JSON en total
- 14 archivos por periodo activo (7 obligatorios + 5 legacy + resumen.json + sentimiento.json)
- periodos.json: Array con {id, label, isNew, url?} — 9 instancias (2 activas, 7 placeholder)
- Estructura consistente entre periodos
- Todos los JSON son pretty-printed (no minificados)
- Contracts bien documentados en JSON_SCHEMA.md y CONTRACTS.md

### Inferencias
- La consistencia entre periodos sugiere que build_json.py es efectivamente la única fuente
- Los 5 archivos legacy son deuda técnica reconocida (documentada)
- El pretty-printing es bueno para debugging pero aumenta tamaño de transferencia
- No hay campo de versión en los JSON → si el schema cambia, dashboards viejos rompen

### Fortalezas
- Alta consistencia estructural entre periodos
- Separación clara por granularidad (global → carrera → ciclo → carrera+ciclo)
- filtros.json excelente como configuración de UI
- dashboard_data.json bien estructurado (resumen + hallazgos + distribuciones)
- Datos precomputados (el dashboard no recalcula agregaciones)

### Debilidades
- 5 archivos legacy sin contrato que aún se generan (aumentan build time y confusión)
- Sin campo de versión/schema version → cambios rompen backward compatibility
- Redundancia: nps_ciclo_carrera + csat_ciclo_carrera podrían unificarse
- JSON pretty-printed → ~30-40% más grandes de lo necesario
- Sin compresión en transferencia (GitHub Pages sí aplica gzip)
- dimensiones.json: ~20KB por periodo (el más pesado)

### Riesgos Técnicos
- **Alto**: Sin versionado de schema → cambio en ETL puede romper dashboards antiguos silenciosamente
- **Medio**: Crecimiento lineal de archivos con cada nuevo periodo
- **Bajo**: Archivos legacy generan ruido y confusión para agentes IA

## 1.6 Navegación

### Hechos Observados
- Entry point: `zoho-survey/index.html` → loader.js → pills (desktop) + select (mobile)
- periodos.json controla la navegación
- Navegación entre periodos vía iframe (sin SPA routing)
- Cada dashboard es independiente (no comparte estado con otros periodos)
- Cambio de tipo de encuesta (estudiantes → graduados → etc.) vía loader

### Inferencias
- El modelo iframe es simple pero efectivo para GitHub Pages
- Aislamiento total entre dashboards (no hay riesgo de contaminación de estado)
- La URL no cambia al navegar entre periodos → no se puede compartir enlace directo a un periodo específico
- No hay deep-linking

### Fortalezas
- Navegación simple y funcional
- Aislamiento completo entre periodos
- loader.js ligero y enfocado

### Debilidades
- Sin deep-linking (no se puede linkear a 2026-1 directamente)
- Iframe sin title (accesibilidad)
- URL no refleja estado de navegación
- Sin historial de navegación entre periodos

### Riesgos Técnicos
- **Bajo**: Sin deep-linking limita compartibilidad

## 1.7 Rendimiento

### Hechos Observados
- dashboard.js: ~2550 líneas (~80KB sin comprimir, ~20KB gzipped estimado)
- dashboard.css: ~1350 líneas (~35KB sin comprimir, ~8KB gzipped)
- 7-14 JSON files cargados en paralelo al iniciar (~30-40KB total por periodo)
- Sin lazy loading de secciones
- Sin code splitting
- Google Fonts (Roboto) con preconnect
- Imágenes con loading="lazy"

### Inferencias
- La carga inicial es razonable para dashboards individuales
- El principal costo es dashboard.js (parseo + ejecución)
- Los JSON son pequeños individualmente pero generan múltiples requests
- GitHub Pages sirve con gzip compression (mitiga tamaño)

### Fortalezas
- Zero dependencias externas (no hay que descargar frameworks)
- Preconnect para Google Fonts
- Imágenes lazy-loaded
- CSS y JS locales (sin CDN adicionales)

### Debilidades
- Sin minificación de CSS/JS en producción
- 7-14 requests JSON al iniciar (aunque paralelizables con HTTP/2)
- Sin lazy loading de secciones (todo se renderiza al iniciar)
- Sin preload de recursos críticos (CSS, JSON principales)
- dashboard.js bloquea el parser (no es async/defer)

### Riesgos Técnicos
- **Bajo**: En conexiones lentas, 14 JSON requests pueden degradar experiencia
- **Bajo**: Sin compresión manual (GitHub Pages lo maneja)

## 1.8 SEO Técnico

### Hechos Observados
- Dashboards: meta description presente, lang="es-PE", theme-color
- Loader: sin meta description básica
- Sin Open Graph tags en ninguna página
- Sin canonical tags
- Sin sitemap
- Sin robots.txt
- Sin schema.org structured data

### Inferencias
- SEO no es prioridad (los dashboards son para consumo interno)
- Pero metadata básica es buena práctica incluso para herramientas internas

### Fortalezas
- Meta description en dashboards
- lang attribute correcto
- Estructura semántica indexable

### Debilidades
- Sin OG tags
- Sin sitemap/robots.txt
- Loader sin meta description

### Riesgos Técnicos
- **Bajo**: El proyecto no parece destinado a indexación pública masiva

## 1.9 Accesibilidad (WCAG)

### Hechos Observados
- Dashboards: Excelente. Skip-link, ARIA labels (15+), aria-labelledby, role="group", aria-live, labels explícitos en todos los selects, focus visibles, sr-only content
- Loader: Deficiente. Sin ARIA, iframe sin title, sin skip-link, sin roles semánticos
- underconstruction.html: Deficiente. Sin ARIA, sin roles, solo alt text en img

### Inferencias
- El equipo claramente priorizó accesibilidad en los dashboards pero no en las páginas auxiliares
- La discrepancia sugiere que diferentes personas o momentos desarrollaron cada parte

### Fortalezas
- Dashboard: Accesibilidad de alto nivel (WCAG AA cumplido en gran medida)
- Filtros agrupados con role="group"
- Regiones dinámicas con aria-live
- SVG con aria-label
- Navegación por teclado funcional en filtros

### Debilidades
- Loader sin accesibilidad básica
- Iframe sin title (WCAG fallo crítico)
- underconstruction.html sin estructura semántica

### Riesgos Técnicos
- **Medio**: Iframe sin title → falla WCAG 2.1 nivel A (4.1.2)
- **Bajo**: Loader inaccesible → usuarios de screen readers no pueden navegar entrada

## 1.10 Compatibilidad con IA

### Hechos Observados
- AGENTS.md excelente: prioridades, reglas JSON, ETL, refactor, estándares respuesta
- ARCHITECTURE.md bien estructurado para agentes
- CONTRACTS.md claro y específico
- Múltiples README.md en puntos clave
- FILTER_LOGIC.md documenta lógica compleja
- JSON_SCHEMA.md documenta contratos

### Inferencias
- El proyecto fue diseñado explícitamente para ser mantenido con asistencia de IA
- La documentación es el mejor activo del proyecto

### Fortalezas
- Documentación excepcional para agentes IA
- Contratos claros y explícitos
- Convenciones documentadas
- Deuda técnica reconocida y catalogada
- Instrucciones específicas para IA en múltiples archivos

### Debilidades
- template/index.html no existe (referenciado pero ausente)
- Path inconsistencies documentados en /memories/repo/scripts-folder-analysis.md
- Sin guía de onboarding para nuevos desarrolladores humanos

### Riesgos Técnicos
- **Medio**: Path inconsistencies pueden confundir a agentes IA que sigan referencias documentales
- **Bajo**: Documentación puede desactualizarse si no se mantiene junto con el código

---

## Resumen Fase 1: Matriz de Hallazgos

### Fortalezas Principales
1. Documentación AI-first excepcional
2. Dashboard HTML semánticamente excelente y accesible
3. Sistema de design tokens CSS robusto
4. Contratos JSON consistentes y bien documentados
5. Cero dependencias runtime (autosuficiente)
6. Pipeline ETL idempotente
7. Separación datos/vista estricta
8. Delegación de eventos implementada

### Debilidades Principales
1. HTML de dashboard duplicado 3× (100% idéntico)
2. dashboard.js monolítico (2550 líneas en un archivo)
3. XSS en tooltip (innerHTML sin sanitizar)
4. CSS duplicado entre dashboard.css y loader.css
5. template/index.html no existe
6. Constantes hardcodeadas en JS y Python
7. Sin tests automatizados
8. Sin versionado de schema JSON
9. 5 archivos legacy aún generados
10. Loader sin accesibilidad

### Riesgos Técnicos — Clasificación

| Riesgo | Severidad | Categoría |
|--------|-----------|-----------|
| XSS en tooltip (innerHTML) | 🔴 Crítico | Seguridad |
| HTML dashboard duplicado 3× | 🔴 Crítico | Mantenibilidad |
| dashboard.js monolítico (2550 líneas) | 🟠 Alto | Mantenibilidad |
| Sin tests automatizados | 🟠 Alto | Calidad |
| Sin versionado de schema JSON | 🟠 Alto | Backward compat |
| Constantes hardcodeadas en JS | 🟡 Medio | Configuración |
| Constantes hardcodeadas en Python | 🟡 Medio | Configuración |
| CSS duplicado entre archivos | 🟡 Medio | Mantenibilidad |
| Path inconsistencies CI/CD | 🟡 Medio | Infraestructura |
| Iframe sin title (WCAG) | 🟡 Medio | Accesibilidad |
| 5 archivos legacy generados | 🟡 Medio | Deuda técnica |
| Sin minificación producción | 🟢 Bajo | Rendimiento |
| Sin deep-linking | 🟢 Bajo | UX |
| Sin OG tags / SEO | 🟢 Bajo | SEO |
| 6/9 módulos placeholder | 🟢 Bajo | Planeación |

### Problemas de Mantenibilidad
1. Cambio en HTML requiere editar 3 archivos idénticos
2. Cambio en lógica de filtros requiere modificar 5 bloques duplicados
3. Nueva carrera de 12 ciclos requiere cambiar JS hardcodeado
4. Nueva facultad requiere cambiar catálogo en Python
5. Scripts ETL sin procesamiento incremental (reprocesa todo)

### Problemas de Escalabilidad
1. Cada nuevo periodo agrega directorio con 14 JSONs + HTML duplicado
2. Crecimiento lineal de requests JSON por periodo
3. dashboard.js crecerá si se agregan secciones (ya tiene 2550 líneas)
4. Sin mecanismo de herencia/plantilla para nuevos periodos

### Problemas de Organización
1. template/index.html referenciado pero inexistente
2. Paths inconsistentes entre package.json y GitHub Actions
3. Placeholders para 6 tipos de encuesta sin datos (ruido estructural)
4. zoho-survey/index.html como entry point mezclado con datos de dominio

---

# Fase 2 — Arquitectura Objetivo

## Árbol Completo de Carpetas Recomendado

```
survey-storytelling/
├── .github/
│   └── workflows/
│       ├── build.yml                    # Unificado (era build_students.yml)
│       └── validate.yml                 # Unificado (era validate-survey-json.yml)
├── data/                                # CSVs fuente (sin cambios)
├── scripts/                             # Python ETL (movido de zoho-survey/scripts/)
│   ├── build_json.py
│   ├── validate_json.py
│   └── README.md
├── src/                                 # Fuentes frontend (NUEVO)
│   ├── css/
│   │   ├── tokens.css                   # Design tokens (extraído de dashboard.css)
│   │   ├── reset.css                    # Reset + base (extraído de dashboard.css)
│   │   ├── components.css               # Componentes compartidos (tabs, pills, selects)
│   │   ├── dashboard.css                # Solo estilos específicos del dashboard
│   │   ├── loader.css                   # Solo estilos del loader
│   │   └── underconstruction.css        # Extraído del inline CSS
│   ├── js/
│   │   ├── config.js                    # Configuración externalizada
│   │   ├── utils.js                     # formatInteger, formatDecimal, pct, cortarTexto...
│   │   ├── data.js                      # fetch JSON, cache management
│   │   ├── filters.js                   # Lógica de filtros cascada (UNA vez)
│   │   ├── render/
│   │   │   ├── ejecutivo.js             # Render sección ejecutiva
│   │   │   ├── operativo.js             # Render sección operativa
│   │   │   ├── detallado.js             # Render sección detallada
│   │   │   ├── cualitativo.js           # Render sección cualitativa
│   │   │   └── radar.js                 # Render SVG radar (independiente)
│   │   ├── tooltip.js                   # Tooltip con sanitización
│   │   ├── loader.js                    # Navegación periodos
│   │   └── main.js                      # Entry point (orquestador)
│   ├── img/                             # Imágenes (movido de shared/img/)
│   └── template.html                    # Template dashboard (UNO para todos)
├── public/                              # Sitio desplegable (GENERADO)
│   ├── index.html                       # Loader principal
│   ├── underconstruction.html
│   ├── students/
│   │   ├── undergraduate/
│   │   │   ├── 2025-2/
│   │   │   │   ├── index.html           # Copia de template.html
│   │   │   │   └── json/                # Datos generados
│   │   │   └── 2026-1/
│   │   │       ├── index.html
│   │   │       └── json/
│   │   ├── graduate/
│   │   │   └── 2026/
│   │   │       ├── index.html
│   │   │       └── json/
│   │   └── posgraduate/
│   │       └── periodos.json
│   ├── alumni/ ...
│   ├── employers/ ...
│   ├── facultyStaff/ ...
│   └── nonfacultyStaff/ ...
├── package.json
├── README.md
├── AGENTS.md
├── ARCHITECTURE.md
└── CONTRACTS.md
```

### Qué problema resuelve
- **Separación src/public**: Código fuente vs artefactos generados. Claridad para agentes IA.
- **CSS particionado**: tokens.css como single source of truth. Sin duplicación.
- **JS modular**: Cada archivo < 400 líneas. Responsabilidad única.
- **template.html único**: Un solo HTML para todos los dashboards. Cambios se propagan automáticamente.
- **scripts/ en raíz**: Elimina confusión de paths. Consistente con package.json y CI.

### Qué beneficio aporta
- Modificar un componente JS no requiere entender 2550 líneas
- Agregar un periodo solo requiere: nuevo CSV → ejecutar build → listo
- CSS tokens en un solo archivo → cambios de tema instantáneos
- template.html → 0 duplicación HTML

### Qué riesgo evita
- Divergencia de dashboards (hoy 3 idénticos, mañana podrían divergir)
- XSS en tooltip (tooltip.js con sanitización)
- Rotura de CI por paths inconsistentes
- Crecimiento descontrolado de dashboard.js

### Qué trade-offs introduce
- Más archivos JS → más requests HTTP (mitigable con concatenación simple en build)
- ES modules requieren servidor local (Python http.server ya lo soporta, GitHub Pages también)
- Estructura más profunda → más directorios que navegar
- Build step adicional (copia de template + assets a public/)

### Alternativas posibles
- **Mantener estructura plana con ES modules en mismo directorio**: Más simple pero menos organizado
- **Todo en un solo archivo JS con comentarios de sección**: Menos requests pero mismo problema de mantenibilidad
- **Template HTML como string en JS (SPA pura)**: Elimina HTML duplicado pero requiere reescribir todo el renderizado

## Organización HTML

### Estrategia
- **template.html**: Único archivo HTML para dashboards. Contiene estructura semántica completa con placeholders para datos dinámicos.
- **index.html (loader)**: Reescrito con semántica adecuada (`<nav>`, `<main>`, ARIA labels, iframe title).
- **underconstruction.html**: CSS extraído a archivo externo.

### Qué problema resuelve
- 3 dashboards idénticos → 1 template
- Loader inaccesible → loader semántico

### Qué beneficio aporta
- Cambio de estructura HTML se hace UNA vez
- Nuevos periodos heredan mejoras automáticamente
- Accesibilidad consistente en todo el sitio

## Organización CSS

### Estrategia
- **tokens.css**: Solo variables CSS (design tokens). Sin reglas de estilo.
- **reset.css**: Reset + estilos base (body, headings, links).
- **components.css**: Componentes reutilizables (survey-tab, survey-select, pills, filter-group, KPI cards, tooltip, progress-bar).
- **dashboard.css**: Solo estilos específicos del dashboard (secciones, tablas, radar).
- **loader.css**: Solo estilos del loader (splash, topbar, pills, select).
- **underconstruction.css**: Estilos de página en construcción.

### Qué problema resuelve
- Duplicación `.survey-tab`/`.survey-select` entre dashboard.css y loader.css → extraído a components.css
- Selectores de alta especificidad heredados → alcance limitado por archivo
- Sin guía de dónde poner nuevos estilos → cada archivo tiene propósito claro

### Qué beneficio aporta
- tokens.css como single source of truth para colores, fuentes, espaciados
- Componentes CSS verdaderamente reutilizables
- Menos riesgo de regresión al modificar estilos

## Organización JavaScript

### Estrategia
- **ES modules** (`<script type="module">`). Sin IIFE. Sin globals (excepto loader.js que expone funciones para atributos onclick inline).
- **config.js**: Todas las constantes externalizadas (META_NPS, META_CSAT, CARRERAS_12_CICLOS, SAT_KEYS, etc.). Cargable como JSON también.
- **utils.js**: Funciones puras de formato (formatInteger, formatDecimal, formatPercent, pct, sumKeys, cortarTexto, formatDimensionName).
- **data.js**: Fetch de JSON, cache management, función `loadData()`.
- **filters.js**: Lógica de filtros cascada UNA sola vez. Exporta `setupFilters(prefix, onChange)`.
- **render/*.js**: Cada sección en su propio módulo. Reciben datos filtrados, devuelven void (manipulan DOM).
- **tooltip.js**: showTooltip/hideTooltip con sanitización (textContent o DOMPurify).
- **main.js**: Orquestador. Importa todos los módulos, inicializa cache, configura filtros, renderiza secciones.

### Qué problema resuelve
- Monolito de 2550 líneas → 12 módulos de < 400 líneas cada uno
- Lógica de filtros duplicada 5× → 1 implementación reutilizada
- XSS en tooltip → sanitización centralizada
- Constantes hardcodeadas → configuración externalizada

### Qué beneficio aporta
- Testeo unitario posible (funciones puras exportadas)
- Mantenimiento focalizado (cada módulo tiene responsabilidad única)
- Reutilización real de lógica de filtros
- Onboarding más rápido (no hay que leer 2550 líneas para entender)

### Qué riesgo evita
- Regresiones por modificar archivo monolítico
- XSS por tooltips no sanitizados
- Divergencia de lógica entre secciones que usan filtros

## Organización de Datos

### Estrategia
- **Sin cambios en JSON contracts existentes** (backward compatible).
- **Agregar campo `version`**: `"version": "1.0"` en dashboard_data.json para detectar incompatibilidades.
- **Eliminar generación de archivos legacy** (5 archivos sin contrato).
- **Considerar unificación nps+csat_ciclo_carrera**: Evaluar en fase 2 (requiere cambio en dashboard.js).
- **Minificación de JSON en producción**: Opción en build_json.py (`--compact` flag).

### Qué problema resuelve
- Sin versionado → dashboards no pueden detectar schema incompatible
- Archivos legacy → ruido, confusión, build time innecesario
- JSON pretty-printed → ~30% más pesados de lo necesario

### Qué beneficio aporta
- Versionado permite evolución controlada de contratos
- Menos archivos = menos requests = mejor rendimiento
- Build más rápido sin archivos legacy

## Organización de Recursos

### Estrategia
- **img/**: Mover de `shared/img/` a `src/img/`. Sin cambios en contenido.
- **Iconos**: Actualmente no hay fuente de iconos (usan emojis o SVG inline). Si se añaden, usar SVG sprite o fuente mínima.
- **Fuentes**: Google Fonts Roboto — mantener con preconnect. Evaluar self-hosting para eliminar dependencia externa.
- **Datasets**: Sin cambios (data/ en raíz para CSVs fuente, json/ en cada periodo para generados).

## Estrategia de Componentización (Sin Frameworks)

### Principios
1. **Template HTML + ES Modules**: La componente "dashboard" es template.html + módulos JS que lo manipulan.
2. **Custom Elements mínimos**: No se recomienda Web Components (shadow DOM complica estilos compartidos). Pero se puede evaluar para componentes aislados (KPI card, filter-group).
3. **Componentes CSS**: Clases reutilizables en components.css (`.kpi-card`, `.filter-group`, `.survey-tab`, `.pill`, `.insight-box`).
4. **Funciones factory JS**: `createFilterGroup(prefix)` devuelve {setup, reset, getState}. `createKPICard(config)` devuelve elemento DOM.

### Ejemplo de componente sin framework:
```js
// components/kpi-card.js
export function createKPICard({ id, title, valueId, barId, metaId }) {
  // Devuelve función render que actualiza el DOM
  return {
    render(value, meta, pct) {
      document.getElementById(valueId).textContent = value;
      document.getElementById(barId).style.width = pct + '%';
      document.getElementById(metaId).textContent = meta;
    }
  };
}
```

## Estrategia de Reutilización

1. **HTML**: template.html como base para todos los dashboards (copia por script ETL).
2. **CSS**: components.css con clases reutilizables. tokens.css como API de diseño.
3. **JS**: ES modules con exports explícitos. filters.js usado por 5 secciones. utils.js usado por todos.
4. **Datos**: filtros.json como configuración de UI. periodos.json como manifiesto de navegación.
5. **CI/CD**: Workflows unificados (build.yml, validate.yml) que sirven para todos los tipos de encuesta.

## Convenciones de Nombres

### Archivos
- **CSS**: `kebab-case.css` (ej: `design-tokens.css`, `kpi-card.css`)
- **JS**: `kebab-case.js` (ej: `filter-logic.js`, `render-radar.js`)
- **JSON**: `snake_case.json` (mantener convención actual — ej: `csat_carrera.json`)
- **Directorios**: `kebab-case` para código, `snake_case` para datos generados

### Código
- **Funciones JS**: camelCase (actual, mantener)
- **Clases CSS**: kebab-case (actual, mantener)
- **IDs HTML**: kebab-case (actual, mantener)
- **Variables CSS**: `--kebab-case` (actual, mantener)
- **Constantes JS**: UPPER_SNAKE_CASE (actual, mantener)

### Datos
- **Claves JSON**: snake_case (actual, mantener — legacy de pandas)
- **Nombres de columna internos**: snake_case (consistente con JSON)

## Estrategia Documental

### README.md (raíz)
- Mantener estructura actual
- Agregar: quick start de 3 pasos, arquitectura visual simplificada, enlaces a docs detalladas

### AGENTS.md
- Mantener actual (ya excelente)
- Agregar: nuevo árbol de carpetas, ubicación de template.html, convención de módulos JS

### ARCHITECTURE.md
- Actualizar con nueva estructura
- Agregar: diagrama de módulos JS, flujo de build, estrategia de componentización

### CONTRACTS.md
- Agregar: campo `version` en dashboard_data.json
- Documentar eliminación de archivos legacy
- Agregar: schema de config.js

### Nuevos documentos recomendados:
- **TESTING.md**: Estrategia de testing (qué testear, cómo, herramientas recomendadas)
- **CHANGELOG.md**: Registro de cambios (buena práctica para equipos con IA)

---

# Fase 3 — Comparación: Arquitectura Actual vs Propuesta

## Mantener
| Elemento | Motivo |
|----------|--------|
| Pipeline ETL idempotente (build_json.py) | Funciona bien, bien documentado |
| Contratos JSON actuales (7 obligatorios) | Estables, backward-compatibles |
| Sistema de design tokens CSS | Robusto, completo |
| Delegación de eventos | Patrón correcto para el stack |
| DOM registry | Buena optimización |
| dashboard.js funciones de formato | Bien implementadas, reutilizables |
| loader.js lógica de navegación | Simple, funcional |
| periodos.json como manifiesto | Buen patrón de configuración |
| Estructura de documentación AI-first | Excelente activo del proyecto |
| package.json scripts básicos | Adecuados |

## Reorganizar
| Elemento | De → A | Motivo |
|----------|--------|--------|
| scripts/ Python | `zoho-survey/scripts/` → `scripts/` (raíz) | Eliminar confusión de paths, consistencia con CI |
| CSS dashboard | `shared/css/dashboard.css` → `src/css/` particionado | Componentes reutilizables, sin duplicación |
| JS dashboard | `shared/js/dashboard.js` (2550 líneas) → `src/js/` modular | Mantenibilidad, testabilidad |
| Imágenes | `shared/img/` → `src/img/` | Consistencia con nueva estructura |
| Loader HTML | `zoho-survey/index.html` → `public/index.html` | Semántica, accesibilidad |

## Dividir
| Elemento | En | Motivo |
|----------|-----|--------|
| dashboard.js (2550 líneas) | 12 módulos ES | Responsabilidad única, testabilidad |
| dashboard.css (1350 líneas) | tokens.css + reset.css + components.css + dashboard.css | Reutilización, claridad |
| Lógica de filtros (5× duplicada) | filters.js (1 implementación) | DRY, mantenibilidad |

## Fusionar
| Elementos | En | Motivo |
|-----------|-----|--------|
| 3 index.html de dashboard (idénticos) | template.html (1 archivo) | Cero duplicación |
| build_students.yml + validate-survey-json.yml + deploy-legacy.yml | build.yml + validate.yml | Simplificar CI/CD |
| nps.json + csat.json (legacy) | Eliminar (no se usan) | Reducir ruido |
| Múltiples constantes hardcodeadas en JS | config.js | Configuración centralizada |
| Catálogos hardcodeados en Python | config.py o YAML/JSON externo | Separación código/configuración |

## Eliminar
| Elemento | Motivo |
|----------|--------|
| 5 archivos JSON legacy por periodo | Sin contrato, no consumidos por dashboard.js |
| CSS inline en underconstruction.html | Mala práctica, extraer a archivo |
| deploy-legacy.yml workflow | Si ya no es necesario (verificar) |
| Placeholders vacíos (posgraduate 1.txt) | Ruido, confusión |
| Referencias a template/ inexistente | Actualizar documentación |

## Crear
| Elemento | Motivo |
|----------|--------|
| template.html | Template único para dashboards |
| src/css/tokens.css | Design tokens como archivo independiente |
| src/css/components.css | Componentes CSS reutilizables |
| src/css/reset.css | Reset y estilos base |
| src/css/underconstruction.css | Estilos extraídos del inline |
| src/js/config.js | Configuración externalizada |
| src/js/utils.js | Funciones de formato puras |
| src/js/data.js | Capa de datos (fetch + cache) |
| src/js/filters.js | Lógica de filtros unificada |
| src/js/render/ (5 archivos) | Renderizado por sección |
| src/js/tooltip.js | Tooltip con sanitización |
| src/js/main.js | Entry point orquestador |
| scripts/config.py | Configuración ETL externalizada |
| Campo `version` en dashboard_data.json | Versionado de schema |
| TESTING.md | Estrategia de testing |
| CHANGELOG.md | Registro de cambios |

---

# Fase 4 — Roadmap de Migración

## Fase 4.1: Correcciones de Seguridad (Alta Prioridad)

### Tarea 1: Sanitizar tooltip (XSS)
- **Objetivo**: Eliminar vulnerabilidad XSS en `tooltip.innerHTML`
- **Beneficio**: Seguridad. Previene inyección de scripts si datos JSON son comprometidos.
- **Dependencias**: Ninguna
- **Riesgos**: Cambio mínimo (solo tooltip). Si algún tooltip usaba HTML legítimo, evaluar usar DOMPurify o whitelist de tags.
- **Esfuerzo**: 1-2 horas
- **Archivos**: `zoho-survey/shared/js/dashboard.js` (función showTooltip)

## Fase 4.2: Estabilización Estructural (Alta Prioridad)

### Tarea 2: Crear template.html
- **Objetivo**: Un solo HTML para todos los dashboards. Referenciado desde cada periodo.
- **Beneficio**: Elimina 3× duplicación de 530 líneas. Cambios HTML se propagan automáticamente.
- **Dependencias**: Ninguna
- **Riesgos**: Los paths relativos a CSS/JS cambian (de `../../../shared/` a `../../src/`). Requiere actualizar referencias.
- **Esfuerzo**: 2-3 horas
- **Archivos**: Crear `src/template.html`. Modificar `build_json.py` para copiar template. Actualizar dashboards existentes.

### Tarea 3: Mover scripts/ a raíz y corregir paths CI/CD
- **Objetivo**: `zoho-survey/scripts/` → `scripts/`. Corregir package.json y GitHub Actions.
- **Beneficio**: Elimina confusión documentada en `/memories/repo/scripts-folder-analysis.md`. Paths consistentes para agentes IA.
- **Dependencias**: Ninguna
- **Riesgos**: Medio. Requiere actualizar todos los paths en documentación y CI. build_json.py usa `Path(__file__).resolve().parent` (se adapta solo).
- **Esfuerzo**: 1-2 horas
- **Archivos**: `scripts/` (mover), `package.json`, `.github/workflows/*.yml`, docs

### Tarea 4: Agregar versionado a JSON contracts
- **Objetivo**: Campo `"version": "1.0"` en dashboard_data.json. Dashboard.js verifica versión al cargar.
- **Beneficio**: Previene rotura silenciosa cuando el schema cambia.
- **Dependencias**: Ninguna
- **Riesgos**: Mínimo (campo aditivo, backward compatible).
- **Esfuerzo**: 1 hora
- **Archivos**: `scripts/build_json.py`, `src/js/data.js`

## Fase 4.3: Modularización JS (Media Prioridad)

### Tarea 5: Extraer config.js
- **Objetivo**: Mover constantes hardcodeadas a `src/js/config.js`
- **Beneficio**: Cambiar umbral NPS o lista de carreras 12 ciclos sin tocar lógica.
- **Dependencias**: Ninguna (independiente)
- **Riesgos**: Mínimo. Las constantes mantienen mismos nombres.
- **Esfuerzo**: 1 hora
- **Archivos**: Crear `src/js/config.js`. Modificar `dashboard.js` para importar.

### Tarea 6: Extraer utils.js y tooltip.js
- **Objetivo**: Funciones de formato → utils.js. Tooltip sanitizado → tooltip.js.
- **Beneficio**: Funciones puras testables. Tooltip seguro y reutilizable.
- **Dependencias**: Tarea 5 (config.js útil pero no requerido)
- **Riesgos**: Bajo. Mismas funciones, diferente archivo.
- **Esfuerzo**: 2 horas
- **Archivos**: Crear `src/js/utils.js`, `src/js/tooltip.js`. Modificar `dashboard.js`.

### Tarea 7: Extraer filters.js (unificar lógica de filtros)
- **Objetivo**: Una sola implementación de filtros cascada usada por 5 secciones.
- **Beneficio**: Elimina 5× duplicación de lógica de filtros (~200 líneas ahorradas). Cambios en lógica de filtros se hacen una vez.
- **Dependencias**: Tarea 6 (utils.js)
- **Riesgos**: Medio. Las 5 secciones tienen pequeñas variaciones. Requiere testing cuidadoso.
- **Esfuerzo**: 3-4 horas
- **Archivos**: Crear `src/js/filters.js`. Modificar `dashboard.js` para delegar.

### Tarea 8: Dividir renderizado en módulos por sección
- **Objetivo**: Cada sección (ejecutivo, operativo, detallado, cualitativo) en su propio módulo + radar independiente.
- **Beneficio**: Archivos de < 400 líneas. Responsabilidad única. Testeo independiente.
- **Dependencias**: Tareas 5, 6, 7
- **Riesgos**: Alto (mayor cambio estructural). Requiere definir contratos entre módulos (qué reciben, qué devuelven).
- **Esfuerzo**: 6-8 horas
- **Archivos**: Crear `src/js/render/*.js`. Crear `src/js/data.js`. Crear `src/js/main.js`. Convertir dashboard.js a entry point.

## Fase 4.4: Modularización CSS (Media Prioridad)

### Tarea 9: Particionar CSS
- **Objetivo**: dashboard.css → tokens.css + reset.css + components.css + dashboard.css
- **Beneficio**: Componentes reutilizables. Sin duplicación con loader.css.
- **Dependencias**: Tarea 2 (template.html debe referenciar nuevos archivos)
- **Riesgos**: Medio. La cascada CSS puede comportarse diferente si cambia el orden. Testear visualmente.
- **Esfuerzo**: 3-4 horas
- **Archivos**: Crear `src/css/tokens.css`, `reset.css`, `components.css`. Modificar `dashboard.css`. Actualizar `loader.css`. Actualizar template.html.

## Fase 4.5: Mejoras de Infraestructura (Media-Baja Prioridad)

### Tarea 10: Unificar GitHub Actions workflows
- **Objetivo**: 3 workflows → 2 (build.yml + validate.yml). Eliminar deploy-legacy.yml si no se usa.
- **Beneficio**: CI más simple. Menos puntos de falla.
- **Dependencias**: Tarea 3 (paths corregidos)
- **Riesgos**: Bajo. Es solo reorganización de YAML.
- **Esfuerzo**: 2 horas
- **Archivos**: `.github/workflows/*.yml`

### Tarea 11: Eliminar archivos legacy y placeholders
- **Objetivo**: 5 JSON legacy por periodo dejan de generarse. 1.txt placeholders eliminados.
- **Beneficio**: Menos ruido. Build más rápido. Menos confusión para agentes IA.
- **Dependencias**: Verificar que ningún consumer use archivos legacy (documentado que no).
- **Riesgos**: Bajo (documentado que no se usan). Pero verificar dashboard.js no los referencia.
- **Esfuerzo**: 1 hora
- **Archivos**: `scripts/build_json.py` (desactivar generación legacy)

## Fase 4.6: Mejoras de Calidad (Baja Prioridad)

### Tarea 12: Agregar tests unitarios
- **Objetivo**: Tests para utils.js, filters.js, data.js con Vitest o similar.
- **Beneficio**: Prevenir regresiones. Documentar comportamiento esperado.
- **Dependencias**: Tareas 5-8 (módulos existen)
- **Riesgos**: Bajo. Solo agrega valor.
- **Esfuerzo**: 8-16 horas (depende de cobertura deseada)

### Tarea 13: Mejorar accesibilidad del loader
- **Objetivo**: Agregar `<nav>`, `<main>`, ARIA labels, iframe title a `public/index.html`.
- **Beneficio**: WCAG compliance. Consistencia con dashboards.
- **Dependencias**: Ninguna
- **Riesgos**: Bajo
- **Esfuerzo**: 1-2 horas

### Tarea 14: Externalizar catálogos Python a archivos de configuración
- **Objetivo**: `carrera_facultad`, `TOPICOS`, `STOPWORDS`, `CATEGORIA_DIM` → `scripts/config.py` o YAML.
- **Beneficio**: Agregar facultad/carrera no requiere modificar lógica ETL.
- **Dependencias**: Ninguna
- **Riesgos**: Medio. Cambio en build_json.py. Probar idempotencia.
- **Esfuerzo**: 2-3 horas

### Tarea 15: Agregar modo compacto de JSON
- **Objetivo**: Flag `--compact` en build_json.py para minificar JSON en producción.
- **Beneficio**: Reducción ~30% en tamaño de transferencia.
- **Dependencias**: Ninguna
- **Riesgos**: Mínimo (solo cambia formato, no estructura)
- **Esfuerzo**: 1 hora

---

# Fase 5 — Recomendación Ejecutiva

## Los 5 cambios con mayor retorno de inversión

1. **Sanitizar tooltip (XSS)** — Esfuerzo: 1-2h. Impacto: Crítico (seguridad). Sin dependencias. Hacer YA.
2. **Crear template.html único** — Esfuerzo: 2-3h. Impacto: Alto (elimina 3× duplicación HTML). Base para todo lo demás.
3. **Extraer config.js + utils.js** — Esfuerzo: 2-3h. Impacto: Alto (externaliza configuración, habilita testing). Abre camino a modularización.
4. **Dividir dashboard.js en módulos** — Esfuerzo: 12-16h total. Impacto: Alto (mantenibilidad, testabilidad). Hacer incremental (filters.js primero, renders después).
5. **Particionar CSS** — Esfuerzo: 3-4h. Impacto: Medio (reutilización, sin duplicación). Mejora calidad general.

## Los cambios que NO recomendarías realizar

1. **Unificar nps_ciclo_carrera + csat_ciclo_carrera en un solo JSON** — Aunque reduciría requests, requiere cambiar dashboard.js significativamente y el beneficio es marginal (HTTP/2 maneja bien múltiples requests pequeños).
2. **Migrar a Web Components (Custom Elements)** — El shadow DOM complica los estilos compartidos y requeriría reescribir todo el CSS. No aporta suficiente valor sobre ES modules + template.html.
3. **Agregar Service Worker para offline** — Complejidad innecesaria para dashboards que requieren datos frescos.
4. **Reescribir build_json.py en otro lenguaje** — Python funciona bien. No hay justificación para migrar.
5. **Agregar analytics/tracking** — Los dashboards son para consumo interno universitario. Privacidad > analytics.

## Riesgos de sobreingeniería

1. **Demasiados archivos CSS**: Si components.css crece sin control, se vuelve otro monolito. Mantener granularidad con criterio.
2. **Demasiados módulos JS**: 12 módulos está bien. 30 sería excesivo. Agrupar por responsabilidad, no por función individual.
3. **Build pipeline complejo**: Un simple script que copia template + assets a public/ es suficiente. No introducir Webpack/Vite solo para esto.
4. **TypeScript**: Añadiría tipos pero requiere build step. Para este tamaño de proyecto, JSDoc en Vanilla JS es suficiente.
5. **Testing exhaustivo**: 100% cobertura no es necesario. Testear utils.js, filters.js, y funciones de formato. El renderizado DOM se prueba mejor con tests visuales/aceptación.

## Arquitectura mínima recomendable

Si el equipo tiene recursos muy limitados, implementar SOLO:
1. Sanitizar tooltip (XSS) — innegociable
2. Crear template.html — elimina la duplicación inmediata
3. Mover scripts a raíz + corregir paths CI
4. Agregar campo version a JSON
5. Extraer config.js

Esto resuelve los problemas críticos y de alto riesgo con ~8 horas de trabajo.

## Arquitectura óptima recomendable

Implementar el roadmap completo (Fases 4.1 a 4.6) en orden de prioridad. Esto produce:
- Cero duplicación HTML
- JS modular y mantenible (< 400 líneas por archivo)
- CSS particionado y reutilizable
- CI/CD simplificado y correcto
- Tests unitarios para lógica core
- Documentación actualizada

Esfuerzo total estimado: 40-60 horas (2-3 semanas a tiempo parcial).
El proyecto resultante es óptimo para mantenimiento asistido por IA a largo plazo.

---

# Notas Finales

- Este plan NO modifica archivos. Es solo diagnóstico y recomendación.
- La arquitectura propuesta respeta TODAS las restricciones: estático, GitHub Pages, Vanilla JS, Python solo ETL, JSON como intercambio.
- Las alternativas mencionadas son informativas, no vinculantes.
- El orden de las fases en el roadmap es intencional: cada fase habilita la siguiente.
- Las tareas dentro de una misma fase pueden paralelizarse (ej: Tareas 5+6, Tareas 9+13).
