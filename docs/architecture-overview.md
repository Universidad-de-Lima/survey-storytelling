# Architecture Overview v2.0

**Version:** 2.0.0  
**Updated:** 2026-06-02  
**Status:** Production-ready architecture  
**Migration:** See `MIGRATION.md`

---

## System Architecture

The survey-storytelling system is a **static site generator** that transforms survey data (CSV) into interactive visualizations (HTML/CSS/JavaScript) deployable to GitHub Pages.

### High-Level Data Flow

```
CSV Survey Data (Zoho)
    ↓
[ETL Pipeline: Python scripts/build_json.py]
    ├─ Column normalization
    ├─ KPI calculations (NPS, CSAT)
    ├─ Dimension aggregation
    └─ Sentiment analysis
    ↓
JSON Data Contracts
    ├─ dashboard_data.json (KPIs, summary)
    ├─ dimensiones.json (by dimension)
    ├─ filtros.json (filter options)
    ├─ sentimiento.json (qualitative)
    └─ ... (12+ total)
    ↓
[Frontend SPA: JavaScript surveys/shared/js/]
    ├─ Load JSON from ./json/
    ├─ Initialize filter engine
    ├─ Apply cascading filters
    └─ Render 4 sections
    ↓
Interactive Dashboard (HTML/CSS)
    ├─ Section: Ejecutivo (KPIs, trends)
    ├─ Section: Operativo (dimensions, faculties)
    ├─ Section: Detallado (by career, by cycle)
    └─ Section: Cualitativo (sentiment analysis)
    ↓
GitHub Pages Static Site
```

---

## Directory Structure v2.0

```
survey-storytelling/
│
├── surveys/                          # All survey modules
│   ├── shared/                       # Shared across all survey types
│   │   ├── css/
│   │   │   ├── tokens.css           # Design system (colors, typography, spacing)
│   │   │   ├── layout.css           # Grid/flexbox, responsive breakpoints
│   │   │   ├── components.css       # Reusable components (KPI, filters, tooltip)
│   │   │   ├── sections.css         # Section-specific styles
│   │   │   └── dashboard.css        # Entry point, imports all above
│   │   ├── js/
│   │   │   ├── config/
│   │   │   │   └── dom-registry.js  # Centralized DOM ID validation
│   │   │   ├── utils/
│   │   │   │   ├── formatters.js    # Text formatting functions
│   │   │   │   ├── math.js          # Calculations (NPS, CSAT)
│   │   │   │   ├── dom-helpers.js   # DOM manipulation utilities
│   │   │   │   └── validators.js    # Data validation
│   │   │   ├── data-loader.js       # Fetch & load JSON contracts
│   │   │   ├── filter-engine.js     # FilterEngine class, cascade logic
│   │   │   ├── render-engine.js     # RenderEngine class, section rendering
│   │   │   └── core.js              # Orchestrator, initialization sequence
│   │   ├── template/
│   │   │   └── index.html           # Dashboard template for all periods
│   │   └── img/
│   │       ├── logo-horizontal.png
│   │       ├── logo-vertical.png
│   │       ├── logo-isotipo.png
│   │       └── favicon.png
│   │
│   ├── students/
│   │   ├── undergraduate/
│   │   │   ├── 2025-2/
│   │   │   │   ├── index.html       # Iframe entry point
│   │   │   │   └── json/            # Period-specific data
│   │   │   │       ├── dashboard_data.json
│   │   │   │       ├── dimensiones.json
│   │   │   │       ├── filtros.json
│   │   │   │       └── ... (12+ files)
│   │   │   ├── 2026-1/
│   │   │   └── periodos.json        # All periods for this level
│   │   │
│   │   ├── graduate/
│   │   │   ├── 2026/
│   │   │   ├── periodos.json
│   │   │   └── ...
│   │   │
│   │   └── postgraduate/
│   │       ├── 2026/
│   │       └── periodos.json
│   │
│   ├── alumni/
│   │   ├── 2026/
│   │   └── periodos.json
│   │
│   ├── employers/
│   │   ├── 2025-2/
│   │   └── periodos.json
│   │
│   └── [others]/
│
├── scripts/                          # ETL pipeline (root level)
│   ├── lib/                          # Reusable library modules
│   │   ├── __init__.py
│   │   ├── csv_normalizer.py         # Column mapping, data coercion
│   │   ├── aggregator.py             # KPI calculations
│   │   ├── topic_analyzer.py         # Sentiment analysis
│   │   └── validators.py             # JSON schema validation
│   │
│   ├── schemas/                      # JSON Schema v7 contracts
│   │   ├── dashboard_data.schema.json
│   │   ├── dimensiones.schema.json
│   │   ├── filtros.schema.json
│   │   ├── resumen.schema.json
│   │   ├── sentimiento.schema.json
│   │   └── top_dimensiones.schema.json
│   │
│   ├── build_json.py                 # Main ETL orchestrator
│   └── validate_generated_json.py    # Schema validation CLI
│
├── docs/                             # Comprehensive documentation
│   ├── architecture-overview.md      # This file
│   ├── development-guide.md          # How to contribute
│   ├── adding-new-surveys.md         # Add new survey types
│   ├── deployment.md                 # GitHub Pages deployment
│   ├── ai-agent-guide.md             # For AI agents
│   ├── data-contracts.md             # JSON schema docs
│   └── filter-logic.md               # Filter cascade spec
│
├── tests/                            # Test suite
│   ├── unit/
│   │   ├── test_formatters.test.js
│   │   ├── test_math.test.js
│   │   └── test_validators.test.js
│   └── integration/
│
├── data/                             # Raw CSV survey data (ignored by git)
│   └── ENCUESTA_*.csv
│
├── .github/
│   └── workflows/
│       ├── build-and-deploy.yml      # Builds JSON, deploys to GitHub Pages
│       └── validate-json.yml         # Validates schema on PR
│
├── index.html                        # Main entry point with survey type tabs
├── underconstruction.html            # Placeholder pages
├── MIGRATION.md                      # Migration plan v1.0 → v2.0
├── README.md                         # Project overview
├── package.json                      # Project metadata
└── .gitignore
```

---

## Module Responsibilities

### Frontend Modules

#### `surveys/shared/js/config/dom-registry.js`
**Responsibility:** Centralized DOM element ID validation  
**Exports:** `validateDOMStructure()`, `getDOMElement()`, `REQUIRED_DOM_IDS`, `DOM_REGISTRY`  
**Why:** Prevents HTML-JS desynchronization by catching missing IDs at startup

#### `surveys/shared/js/utils/formatters.js`
**Responsibility:** Text formatting utilities (numbers, percentages, dates)  
**Functions:**
- `formatInteger(value)` — adds thousands separators
- `formatDecimal(value, decimals)`
- `formatPercent(value)`
- `formatDate(dateString)`
- `truncateText(text, maxLength)`
- `formatNPSType(score)` — "Excelente", "Bueno", etc.

#### `surveys/shared/js/utils/math.js`
**Responsibility:** Mathematical calculations for KPIs  
**Functions:**
- `calculatePercentage(value, total)`
- `calculateNPS(promoters, passives, detractors)`
- `calculateCSAT(satisfied, total)`
- `sumObject(obj)`
- `getCareerCycleCount(career)` — returns 12 or 10 depending on career
- `isGeneralStudies(carrera)`

#### `surveys/shared/js/utils/dom-helpers.js`
**Responsibility:** DOM manipulation shortcuts  
**Functions:**
- `$(id)` — shortcut for `document.getElementById()`
- `setElementText(id, text)`
- `setElementHTML(id, html)`
- `getSelectValue(id)`
- `enableElement(id)`, `disableElement(id)`
- `addClass(id, className)`, `removeClass(id, className)`

#### `surveys/shared/js/data-loader.js`
**Responsibility:** Load and merge JSON contracts from `./json/` directory  
**Exports:** `loadDashboardData()` async function  
**Returns:** Merged object with keys: `resumen`, `hallazgos`, `dimensiones`, `filtros`, `sentimiento`  
**Why:** Fetches 4 JSON files in parallel; validates data structure before returning

#### `surveys/shared/js/filter-engine.js`
**Responsibility:** Filter state management and cascade logic  
**Class:** `FilterEngine`  
**Key Methods:**
- `setFacultad(facultad)` → returns available carreras
- `setCarrera(carrera)` → returns available ciclos
- `getState()` → returns current filter state
- `applyFilters(rawData)` → filters data array
- `getAvailableCarreras()`, `getAvailableCiclos()` → dependent options

#### `surveys/shared/js/render-engine.js`
**Responsibility:** Render all 4 dashboard sections based on filter state  
**Class:** `RenderEngine`  
**Key Methods:**
- `renderExecutive()` — KPIs, NPS/CSAT trends
- `renderOperational()` — dimensions, faculties
- `renderDetailed()` — by career, by cycle
- `renderQualitative()` — sentiment analysis
- `renderAll()` — calls all 4 in sequence

#### `surveys/shared/js/core.js`
**Responsibility:** Orchestrator; initializes dashboard in correct sequence  
**Initialization Sequence:**
1. Validate DOM structure
2. Load JSON data
3. Initialize FilterEngine and RenderEngine
4. Initial render of all sections
5. Bind event listeners
6. Show dashboard

### CSS Modules

#### `surveys/shared/css/tokens.css`
**Responsibility:** Design system tokens (colors, typography, spacing, shadows)  
**Contents:** 40+ CSS variables at `:root` level  
**Example:** `--ulima-orange: #ff5117`, `--text-2xl: 1.5rem`, `--space-lg: 1.5rem`

#### `surveys/shared/css/layout.css`
**Responsibility:** Grid/flexbox layouts, responsive breakpoints  
**Contents:**
- Grid layout for dashboard sections
- Flexbox for filter containers
- Media queries for tablet/mobile
- Breakpoints: 1024px (tablet), 768px (mobile), 480px (small mobile)

#### `surveys/shared/css/components.css`
**Responsibility:** Reusable component styles  
**Components:**
- `.kpi-card` — metric display card
- `.filter-select` — dropdown styling
- `.tooltip` — hover tooltips
- `.badge` — semantic badges
- `.chart-container` — chart wrapper

#### `surveys/shared/css/sections.css`
**Responsibility:** Section-specific styles  
**Sections:**
- `#ejecutivo` — Executive (KPIs)
- `#operativo` — Operational (dimensions, faculties)
- `#detallado` — Detailed (by career)
- `#sentimiento` — Qualitative (sentiment analysis)

#### `surveys/shared/css/dashboard.css`
**Responsibility:** Stylesheet entry point  
**Contents:** `@import` statements for all 4 modules + global styles

### Python ETL Modules

#### `scripts/lib/csv_normalizer.py`
**Responsibility:** Column mapping and type coercion  
**Functions:**
- `get_column_mapping(survey_type)` — returns mapping dict
- `normalize_column_names(df, survey_type)` — renames columns
- `coerce_types(df)` — converts to correct types

#### `scripts/lib/aggregator.py`
**Responsibility:** KPI calculations and aggregations  
**Functions:**
- `calculate_nps(promoters, passives, detractors)` → NPS score
- `calculate_csat(satisfied, total)` → CSAT score
- `aggregate_by_dimension(df, dimension_col)` → dict of scores by dimension
- `calculate_summary(df)` → overall statistics

#### `scripts/lib/topic_analyzer.py`
**Responsibility:** Sentiment analysis and keyword extraction  
**Functions:**
- `analyze_sentiment_topics(text)` → returns `{sentiment, keywords, confidence}`
- `aggregate_sentiments(df)` → counts by sentiment
- `SENTIMENT_KEYWORDS` dict with 40+ keywords per sentiment

#### `scripts/lib/validators.py`
**Responsibility:** JSON schema validation  
**Functions:**
- `load_schema(schema_name)` → loads .schema.json file
- `validate_json_against_schema(data, schema_name)` → validates or raises
- `validate_all_contracts(output_dir)` → validates all JSON files

#### `scripts/build_json.py`
**Responsibility:** Main ETL orchestrator  
**Execution:**
1. Parse CSV files from `data/` directory
2. Detect survey type and period from filename
3. Import and use lib modules for processing
4. Generate 12+ JSON files in `surveys/{type}/{period}/json/`
5. Validate all output against schemas
6. Create/update `periodos.json` for period navigation

---

## Data Contracts (JSON Schemas)

All output JSON files are validated against JSON Schema v7 schemas in `scripts/schemas/`.

### `dashboard_data.json`
**Purpose:** Summary KPIs and overall statistics  
**Schema File:** `scripts/schemas/dashboard_data.schema.json`  
**Structure:**
```json
{
  "resumen": {
    "encuestas": 255,
    "carreras": 5,
    "facultades": 3,
    "nps": { "score": 85.88, "promotores": 224, ... },
    "csat": { "score": 99.22, "t3b": 253, ... }
  },
  "hallazgos": { "csat_pct": 99, "nps_score": 85, ... },
  "nps": { "Promotores": 224, "Pasivos": 26, ... },
  "csat": { "Totalmente satisfecho": 151, ... }
}
```

### `dimensiones.json`
**Purpose:** Scores by dimension (e.g., "Calidad de la formación", "Aulas de clase")  
**Structure:** Array of `{ "nombre": "...", "score": 99.61 }`

### `filtros.json`
**Purpose:** Filter options and cascade mappings  
**Structure:**
```json
{
  "has_ciclo": true/false,
  "facultades": ["Facultad de Ingeniería", ...],
  "carreras": ["Ingeniería Civil", ...],
  "facultad_carrera": { "Facultad de Ingeniería": ["Ing. Civil", ...], ... }
}
```

### `sentimiento.json`
**Purpose:** Qualitative analysis (sentiment, keywords)  
**Structure:**
```json
{
  "positivo": { "count": 150, "keywords": ["excelente", "muy bueno", ...] },
  "negativo": { "count": 25, "keywords": ["malo", "mejorar", ...] },
  "neutro": { "count": 80, "keywords": ["ok", "regular", ...] }
}
```

---

## Configuration & Constants

### Per-Survey-Type Configuration
Each survey type has its own configuration file (planned enhancement):
- `surveys/shared/config/students.json`
- `surveys/shared/config/alumni.json`
- `surveys/shared/config/employers.json`

**Example Structure:**
```json
{
  "type": "students",
  "levels": ["undergraduate", "graduate", "postgraduate"],
  "facultades": ["Facultad de Ingeniería", ...],
  "carreras": ["Ingeniería Civil", ...],
  "carreras_12_ciclos": ["Derecho", "Psicología"],
  "meta_nps": 50,
  "meta_csat": 93,
  "dimensions": ["Calidad de la formación", "Aulas de clase", ...]
}
```

### Hardcoded Constants (for future extraction)
Currently in `surveys/shared/js/utils/math.js`:
```javascript
const CARRERAS_12_CICLOS = ['Derecho', 'Psicología'];
const META_NPS = 50;
const META_CSAT = 93;
```

---

## Frontend SPA Initialization Flow

```
1. User navigates to surveys/index.html
   ├─ loader.js executes (IIFE)
   ├─ Fetches periodos.json
   ├─ Renders period pills (desktop) or select (mobile)
   └─ Waits for user selection

2. User clicks period
   ├─ loadPeriod() sets iframe.src to {period}/index.html
   └─ iframe loads

3. Period index.html loads
   ├─ imports core.js (ES6 module)
   ├─ DOM fully ready
   └─ core.js auto-executes IIFE

4. core.js initialization
   ├─ validateDOMStructure() → throws if IDs missing
   ├─ loadDashboardData() → parallel fetch 4 JSON files
   ├─ new FilterEngine(data)
   ├─ new RenderEngine(data, filterEngine)
   ├─ renderAll() → renders Ejecutivo, Operativo, Detallado, Cualitativo
   ├─ bindFilterEvents() → adds event listeners
   └─ Dashboard ready

5. User interacts
   ├─ Selects filter → change event
   ├─ filter-engine updates state
   ├─ render-engine.renderAll()
   └─ Sections re-render with new data
```

---

## Filter Cascade Logic

Filters work in strict hierarchy:

```
1. Facultad selection
   → Available Carreras = facultad_carrera[selectedFacultad]
   → Clear selected Carrera

2. Carrera selection
   → Available Ciclos = 1..12 (or 1..10 based on career)
   → Clear selected Ciclo

3. Ciclo selection
   → Final data filtered by: facultad, carrera, ciclo

4. Dimension selection
   → Shows detailed analysis for this dimension

5. Satisfaction filter
   → Shows only responses with this satisfaction level

6. NPS Type filter
   → Shows only: Promoters, Passives, or Detractors
```

---

## Performance Characteristics

- **Initial Load:** ~2-3 seconds (parallel JSON fetching)
- **Filter Change:** <200ms (re-render only affected sections)
- **Memory:** ~10-15MB (typical dashboard in browser)
- **Bundle Size:** ~120KB total (CSS + JS gzipped)

---

## Backward Compatibility

All changes are **internal** (no breaking changes to:
- JSON output formats (identical structure)
- HTML element IDs (same 50+ IDs required)
- CSV input format (same column structure)
- Relative paths (updated in T3.1)

The system is **100% backward-compatible** after migration.

---

## Future Enhancement Ideas

1. **Config-Driven Architecture** — Move hardcoded constants to JSON configs
2. **Component Library** — Publish KPICard, BarChart, etc. as reusable components
3. **Data Export** — Add CSV/Excel export for dashboard data
4. **Dark Mode** — Add theme toggle using CSS variables
5. **Accessibility** — Add ARIA labels, keyboard navigation
6. **Real-Time Updates** — Integrate with Zoho API for live data
7. **PDF Export** — Add report generation
8. **Multi-Language** — i18n support for Spanish/English

---

See `docs/development-guide.md` for how to extend and contribute to this architecture.
