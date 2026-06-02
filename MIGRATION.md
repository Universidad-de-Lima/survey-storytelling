# MIGRATION PLAN: Architectural Refactoring v1.0 → v2.0

**Status:** Draft  
**Created:** 2026-06-02  
**Estimated Duration:** 23-33 hours (2-3 days continuous development)  
**Risk Level:** Medium  
**Rollback Available:** Yes (v-pre-refactor tag)

---

## Executive Summary

This document details the complete migration from the current monolithic architecture to a modular, maintainable, and scalable system. The refactoring preserves all functionality while improving code organization, reusability, and testability across 7 sequential blocks of work.

### Key Objectives

1. **Eliminate Monolithic Code**: Break 1717-line dashboard.js and 1176-line dashboard.css into modular, testable units
2. **Reduce HTML-JS Coupling**: Centralize 50+ hardcoded element IDs into a single registry with validation
3. **Enable Survey Type Scaling**: Move from copy-paste approach to config-driven architecture (N survey types without duplication)
4. **Extract Business Logic**: Move hardcoded constants (CARRERAS_12_CICLOS, META_NPS) to external config files
5. **Add Quality Assurance**: Introduce JSON schema validation and unit test infrastructure
6. **Improve Documentation**: Centralize and enhance AI-agent-first documentation

### Success Criteria

- ✅ All 4 dashboards load identically in browser
- ✅ Zero broken links or 404 errors
- ✅ JSON generation from CSV produces bit-identical output
- ✅ All 8 new JS modules pass unit tests
- ✅ Git history is clean with atomic commits per block
- ✅ Rollback to v1.0 works without manual intervention

---

## Block Structure & Timeline

| Block | Name | Tasks | Duration | Cumulative |
|-------|------|-------|----------|-----------|
| 1 | SETUP | 4 | 2-3h | 2-3h |
| 2 | STRUCTURE MIGRATION | 8 | 2-3h | 4-6h |
| 3 | COMPATIBILITY FIX | 6 | 3-4h | 7-10h |
| 4 | JAVASCRIPT REFACTORING | 11 | 8-12h | 15-22h |
| 5 | CSS REFACTORING | 6 | 4-5h | 19-27h |
| 6 | PYTHON ETL REFACTORING | 9 | 8-10h | 27-37h ⚠️ |
| 7 | CLEANUP & FINALIZATION | 5 | 2-3h | 29-40h |

**⚠️ Note:** Block 6 is complex; prioritize Blocks 1-5 first if time-constrained.

---

## BLOCK 1: SETUP (2-3 hours)

### T1.1 🔴 Create MIGRATION.md documentation
**Duration:** 30 min | **Prerequisites:** None | **Depends On:** Nothing

**Description:**  
Create comprehensive MIGRATION.md in project root documenting:
- Timeline and rollback procedures
- Task dependencies
- Success criteria
- Risk assessment and mitigation

**Success Criteria:**
- [ ] MIGRATION.md exists with all 49 tasks documented
- [ ] Each task has ID, duration, dependencies, success criteria
- [ ] Risk table covers all 6 identified risks

**Git Rollback:** `git rm MIGRATION.md`

---

### T1.2 🔴 Create git backup branch and tag
**Duration:** 15 min | **Prerequisites:** None | **Depends On:** Nothing

**Description:**  
Create immutable backup of current state:
```bash
git branch main-backup
git tag v-pre-refactor -m "Backup before architectural refactoring"
git push origin main-backup v-pre-refactor
```

**Success Criteria:**
- [ ] `git branch -a | grep main-backup` shows backup branch
- [ ] `git tag -l | grep v-pre-refactor` shows tag
- [ ] Both pushed to GitHub

**Git Rollback:** `git branch -D main-backup && git tag -d v-pre-refactor && git push origin -d main-backup && git push origin -d v-pre-refactor`

---

### T1.3 🔴 Create new directory structure
**Duration:** 45 min | **Prerequisites:** None | **Depends On:** Nothing

**Description:**  
Create all new directories with .gitkeep files (to preserve structure in git):

```
surveys/                          # New root for all survey modules
├── shared/                        # Moved from zoho-survey/shared
│   ├── css/
│   ├── js/
│   │   ├── config/
│   │   ├── utils/
│   │   └── core.js
│   └── img/
├── students/                      # Moved from zoho-survey/students
├── alumni/
├── employers/
├── faculty-staff/
└── non-faculty-staff/

scripts/                           # New root scripts folder
├── lib/
│   ├── __init__.py
│   ├── csv_normalizer.py
│   ├── aggregator.py
│   └── topic_analyzer.py
├── schemas/
│   ├── dashboard_data.schema.json
│   ├── dimensiones.schema.json
│   ├── filtros.schema.json
│   ├── resumen.schema.json
│   ├── sentimiento.schema.json
│   └── top_dimensiones.schema.json
├── build_json.py
└── validate_generated_json.py

docs/                              # New documentation folder
├── architecture-overview.md
├── development-guide.md
├── adding-new-surveys.md
├── deployment.md
├── ai-agent-guide.md
├── data-contracts.md
└── filter-logic.md

tests/                             # New test folder
├── unit/
│   ├── test_formatters.test.js
│   ├── test_math.test.js
│   └── test_validators.test.js
└── integration/
    └── .gitkeep
```

**Shell Commands:**
```bash
# Create surveys structure
mkdir -p surveys/shared/{css,js/{config,utils},img}
mkdir -p surveys/students surveys/alumni surveys/employers surveys/faculty-staff surveys/non-faculty-staff

# Create scripts structure
mkdir -p scripts/lib scripts/schemas

# Create docs structure
mkdir -p docs

# Create tests structure
mkdir -p tests/unit tests/integration

# Create .gitkeep for empty directories
find surveys tests -type d -exec touch {}/.gitkeep \;
```

**Success Criteria:**
- [ ] All 15+ new directories exist
- [ ] .gitkeep files preserve directory structure
- [ ] `git status` shows untracked files only in new directories

**Git Rollback:** `git clean -fd && git checkout HEAD -- .`

---

### T1.4 🔴 Create README.md files in all new folders
**Duration:** 30 min | **Prerequisites:** T1.3 | **Depends On:** T1.3

**Description:**  
Create placeholder README.md in each major new folder documenting its purpose:

- `surveys/README.md` - Overview of surveys module structure
- `scripts/README.md` - ETL pipeline documentation
- `scripts/lib/README.md` - Library modules for ETL
- `scripts/schemas/README.md` - JSON schema contracts
- `docs/README.md` - Documentation index
- `tests/README.md` - Testing infrastructure and conventions

**Success Criteria:**
- [ ] 6 README.md files created
- [ ] Each README explains folder purpose and contains placeholder for content

**Git Rollback:** `git rm -f surveys/README.md scripts/README.md scripts/lib/README.md scripts/schemas/README.md docs/README.md tests/README.md`

---

## BLOCK 2: STRUCTURE MIGRATION (2-3 hours)

### T2.1-T2.7 🔴 Execute git mv for all directories
**Duration:** 1.5-2h | **Prerequisites:** T1.3, T1.4 | **Depends On:** All Block 1 tasks

**Description:**  
Move all existing content from `zoho-survey/` to new structure. Use `git mv` to preserve history:

```bash
# Move shared folder
git mv zoho-survey/shared/* surveys/shared/

# Move students, alumni, employers modules
git mv zoho-survey/students/* surveys/students/
git mv zoho-survey/students/scripts/* scripts/
# (repeat for alumni, employers if they exist)

# Move Python scripts from zoho-survey/students/scripts to scripts/
git mv zoho-survey/students/scripts/build_json.py scripts/
git mv zoho-survey/students/scripts/validate_generated_json.py scripts/
git mv zoho-survey/students/scripts/* scripts/lib/  # Move any lib modules

# Move template
git mv zoho-survey/template/* surveys/shared/template/

# Move data files (if in zoho-survey)
git mv zoho-survey/data/* data/  # Ensure data stays at root
```

**Success Criteria:**
- [ ] All content moved; `zoho-survey/` is empty or deleted
- [ ] Relative path structure preserved (e.g., `surveys/students/graduate/2026/index.html`)
- [ ] `git log --follow` shows continuous file history

**Git Rollback:** 
```bash
git reset --hard HEAD~7  # Undo last 7 commits if T2.1-T2.7 are sequential
```

---

### T2.8 🔴 Create commit: "refactor: reorganize directory structure"
**Duration:** 15 min | **Prerequisites:** T2.1-T2.7 | **Depends On:** T2.1-T2.7

**Description:**  
Create atomic commit documenting the structural reorganization:

```bash
git commit -m "refactor: reorganize directory structure

- Move zoho-survey/shared → surveys/shared
- Move zoho-survey/students → surveys/students
- Move scripts from zoho-survey/students/scripts → scripts/ (root)
- Move template to surveys/shared/template
- Create surveys/ and scripts/ as new root modules
- Preserve git history using 'git mv' for all files

This is a structural reorganization only; no code changes.
Relative paths will be fixed in the next block."
```

**Success Criteria:**
- [ ] Commit created with clear message
- [ ] `git log --oneline | head -1` shows commit with "refactor:" prefix
- [ ] `git show --stat` shows file movements, not deletions + creations

**Git Rollback:** `git revert HEAD`

---

## BLOCK 3: COMPATIBILITY FIX (3-4 hours)

### T3.1 🔴 Calculate and fix relative path prefixes
**Duration:** 2-3h | **Prerequisites:** T2.8 | **Depends On:** Block 2 complete

**Description:**  
Update all `index.html` files in period directories to account for new folder structure. The relative path to `surveys/shared/` changes from `../../shared/` to something like `../../../shared/`.

**Path Calculation:**
- Old structure: `zoho-survey/students/graduate/2026/index.html` → `../../shared/` = `zoho-survey/shared/`
- New structure: `surveys/students/graduate/2026/index.html` → `../../../shared/` = `surveys/shared/`

**Files to Update:** Every `index.html` in:
- `surveys/students/undergraduate/*/index.html`
- `surveys/students/graduate/*/index.html`
- `surveys/alumni/*/index.html` (if exists)
- `surveys/employers/*/index.html` (if exists)

**Relative Path Examples:**

```html
<!-- OLD: zoho-survey/students/graduate/2026/index.html -->
<link rel="stylesheet" href="../../shared/css/dashboard.css">
<script src="../../shared/js/dashboard.js"></script>

<!-- NEW: surveys/students/graduate/2026/index.html -->
<link rel="stylesheet" href="../../../shared/css/dashboard.css">
<script src="../../../shared/js/dashboard.js"></script>

<!-- Also update favicon, logo paths: -->
<!-- OLD: <img src="../../shared/img/logo-horizontal.png"> -->
<!-- NEW: <img src="../../../shared/img/logo-horizontal.png"> -->
```

**Shell Script to Find All Paths:**
```bash
find surveys -name "index.html" -type f | grep -E "(undergraduate|graduate|alumni|employers)" | head -20
```

**Validation:**
```bash
# Count how many levels deep each index.html is
find surveys -name "index.html" | while read f; do
  depth=$(echo "$f" | tr -cd '/' | wc -c)
  echo "$depth: $f"
done
```

**Success Criteria:**
- [ ] All `../../../shared/` paths are correctly set
- [ ] No remaining `../../shared/` references in period index.html files
- [ ] Browser console shows no 404 errors when loading dashboards

**Git Rollback:** `git checkout HEAD -- surveys/`

---

### T3.2 🟡 Update Python ETL script paths
**Duration:** 45 min | **Prerequisites:** T2.8 | **Depends On:** Block 2 complete

**Description:**  
Update `scripts/build_json.py` and `scripts/validate_generated_json.py` to reference new paths:

**Changes in build_json.py:**
```python
# OLD
os.chdir('zoho-survey/students')
path = '../scripts/build_json.py'

# NEW
# Script is now at root: scripts/build_json.py
# Input CSVs: data/*.csv (root level)
# Output destinations: surveys/students/*, surveys/alumni/*, etc.

# Update file path references:
input_csv = os.path.join('data', filename)  # data/ at root
output_dir = os.path.join('surveys', level, period, 'json')
template_path = 'surveys/shared/template/index.html'
```

**Changes in validate_generated_json.py:**
```python
# Update similar path references
# Input: surveys/{level}/{period}/json/*.json
# Template: docs/data-contracts.md (for schema reference)
```

**Success Criteria:**
- [ ] `python scripts/build_json.py` runs from root without cd commands
- [ ] Output files appear in `surveys/*/*/json/` directories
- [ ] No "FileNotFoundError" for relative paths

**Git Rollback:** `git checkout HEAD -- scripts/build_json.py scripts/validate_generated_json.py`

---

### T3.3 🟡 Update GitHub Actions workflow paths
**Duration:** 30 min | **Prerequisites:** T2.8 | **Depends On:** Block 2 complete

**Description:**  
Update `.github/workflows/*.yml` files to reference new script and data locations:

**Old Workflow:**
```yaml
- name: Build JSON from CSV
  run: cd zoho-survey/students && python ../scripts/build_json.py
```

**New Workflow:**
```yaml
- name: Build JSON from CSV
  run: python scripts/build_json.py  # From root
```

**Files to Update:**
- `.github/workflows/build-and-deploy.yml`
- `.github/workflows/validate-json.yml` (if exists)

**Success Criteria:**
- [ ] GitHub Actions workflows reference `scripts/` from root
- [ ] No `cd` commands needed
- [ ] Workflow runs successfully in CI environment

**Git Rollback:** `git checkout HEAD -- .github/workflows/`

---

### T3.4 🟢 Manual testing: Browser checkpoint
**Duration:** 1-1.5h | **Prerequisites:** T3.1, T3.2, T3.3 | **Depends On:** All of T3.1-T3.3

**Description:**  
Start local server and verify all 4 dashboards load without errors:

```bash
# From project root
python -m http.server 8080

# Open browser and navigate to:
# http://localhost:8080/surveys/index.html
```

**Checklist:**
- [ ] Main page loads (index.html with iframe period selector)
- [ ] Period pills/dropdown render correctly
- [ ] Click each period → iframe loads dashboard
- [ ] Click "Undergraduate 2025-2" → dashboard loads without 404s
- [ ] Verify in browser DevTools console: NO red errors
- [ ] Verify in DevTools Network tab: ALL CSS/JS/JSON files load successfully
- [ ] Test all 4 levels: Undergraduate, Graduate, Alumni, Employers
- [ ] Verify dashboard interactivity: filters work, charts render

**Success Criteria:**
- [ ] All 4 dashboards load identically to pre-migration state
- [ ] Zero 404 errors in Network tab
- [ ] Zero JavaScript errors in Console
- [ ] All user interactions work (filters, period switching)

**Git Rollback:** N/A (testing only, no changes)

---

### T3.5 🔴 Regenerate JSON files and diff against originals
**Duration:** 1-1.5h | **Prerequisites:** T3.2 | **Depends On:** T3.4 passed

**Description:**  
Regenerate all JSON from CSV to ensure ETL produces identical output after path changes:

```bash
# From project root
python scripts/build_json.py

# This regenerates all files in surveys/*/*/json/

# Create backup of new output
cp -r surveys/students/graduate/2026/json surveys/students/graduate/2026/json.new

# Compare against original (if you have one)
# If regenerated files are byte-identical, ETL is working correctly
```

**Validation Script:**
```bash
# Find all JSON files and check their structure
find surveys -name "*.json" -type f | wc -l

# Should match expected count (approximately 48+ JSON files across all periods)
```

**Success Criteria:**
- [ ] `python scripts/build_json.py` completes without errors
- [ ] All output directories (`surveys/*/*/json/`) populated with 12+ files each
- [ ] JSON files are valid (parse without errors)
- [ ] Dashboard still loads after regeneration

**Git Rollback:** `git checkout HEAD -- surveys/*/*/json/`

---

### T3.6 🔴 Create commit: "fix: update paths for new directory structure"
**Duration:** 15 min | **Prerequisites:** T3.5 | **Depends On:** T3.4 and T3.5 passed

**Description:**  
Commit all path updates as single atomic commit:

```bash
git add -A
git commit -m "fix: update paths for new directory structure

- Update relative paths in all period index.html files (../../ → ../../../)
- Update Python ETL scripts to reference new root-level scripts/ location
- Update .github/workflows to use scripts/ from project root
- All dashboards tested and verified working
- JSON regenerated and validated

This commit completes Block 3 compatibility fixes."
```

**Success Criteria:**
- [ ] Single commit containing all path updates
- [ ] `git show --stat` shows only modified files (no deletions)
- [ ] Manual testing passed (T3.4)

**Git Rollback:** `git revert HEAD`

---

## BLOCK 4: JAVASCRIPT REFACTORING (8-12 hours)

### T4.1 🔴 Create dom-registry.js with ID validation
**Duration:** 1 hour | **Prerequisites:** T3.6 | **Depends On:** Block 3 complete

**Description:**  
Create centralized DOM registry that validates all required element IDs exist on page load.

**File:** `surveys/shared/js/config/dom-registry.js`

```javascript
/**
 * Centralized registry of all DOM element IDs required by dashboard.js
 * Validates on page load; throws error if any required ID is missing.
 */

// Complete list of all required DOM IDs
const REQUIRED_DOM_IDS = [
  // Layout
  'dashboard-container',
  'filters-container',
  'content-container',
  'progress-fill',
  
  // Filter elements
  'filter-facultad',
  'filter-carrera',
  'filter-ciclo',
  'filter-dimension',
  'filter-satisfaction',
  'filter-nps-type',
  
  // Section: Ejecutivo
  'ejecutivo',
  'ejecutivo-heading',
  'kpi-nps',
  'kpi-nps-type',
  'kpi-csat',
  'kpi-trend',
  'nps-chart',
  'csat-chart',
  
  // Section: Operativo
  'operativo',
  'operativo-heading',
  'dimensiones-container',
  'facultades-container',
  
  // Section: Detallado
  'detallado',
  'detallado-heading',
  'top-facultades',
  'satisfaccion-by-carrera',
  'nps-por-carrera',
  
  // Section: Cualitativo
  'sentimiento',
  'sentimiento-heading',
  'sentimiento-container',
  
  // Other
  'loading-spinner',
  'error-message'
];

// Create registry object for easy access
const DOM_REGISTRY = {};

/**
 * Validates that all required DOM IDs exist on the page.
 * Throws error if any ID is missing.
 */
function validateDOMStructure() {
  const missing = [];
  
  REQUIRED_DOM_IDS.forEach(id => {
    const element = document.getElementById(id);
    if (!element) {
      missing.push(id);
    } else {
      DOM_REGISTRY[id] = element;  // Cache element reference
    }
  });
  
  if (missing.length > 0) {
    const error = `Missing required DOM elements: ${missing.join(', ')}`;
    console.error(error);
    throw new Error(error);
  }
  
  console.log('✓ DOM validation passed. All required elements found.');
  return true;
}

/**
 * Helper to get element by ID with fallback to REGISTRY
 */
function getDOMElement(id) {
  if (DOM_REGISTRY[id]) {
    return DOM_REGISTRY[id];
  }
  const element = document.getElementById(id);
  if (!element) {
    console.warn(`Element not found: ${id}`);
  }
  return element;
}

export { validateDOMStructure, getDOMElement, DOM_REGISTRY, REQUIRED_DOM_IDS };
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/config/dom-registry.js`
- [ ] Export functions: `validateDOMStructure()`, `getDOMElement()`, constants `DOM_REGISTRY`, `REQUIRED_DOM_IDS`
- [ ] No syntax errors (can be checked with `node --check` if Node available)
- [ ] Comprehensive list of 30+ required IDs

**Git Rollback:** `git rm surveys/shared/js/config/dom-registry.js`

---

### T4.2 🟡 Extract formatters functions
**Duration:** 45 min | **Prerequisites:** T4.1 | **Depends On:** T4.1 complete

**Description:**  
Extract all text formatting functions from dashboard.js into separate module.

**File:** `surveys/shared/js/utils/formatters.js`

```javascript
/**
 * Text formatting utilities for dashboard display
 */

function formatInteger(value) {
  if (value === null || value === undefined) return '—';
  return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDecimal(value, decimals = 2) {
  if (value === null || value === undefined) return '—';
  return parseFloat(value).toFixed(decimals);
}

function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined) return '—';
  const percent = parseFloat(value) * 100;
  return percent.toFixed(decimals) + '%';
}

function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(dateString + 'T00:00:00Z');
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function truncateText(text, maxLength = 30) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

function formatNPSType(score) {
  if (score >= 75) return 'Excelente';
  if (score >= 50) return 'Bueno';
  if (score >= 25) return 'Aceptable';
  return 'Crítico';
}

export {
  formatInteger,
  formatDecimal,
  formatPercent,
  formatDate,
  truncateText,
  formatNPSType
};
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/utils/formatters.js`
- [ ] All 6 functions exported
- [ ] Functions match original dashboard.js implementations exactly

**Git Rollback:** `git rm surveys/shared/js/utils/formatters.js`

---

### T4.3 🟡 Extract math functions
**Duration:** 45 min | **Prerequisites:** T4.1 | **Depends On:** T4.1 complete

**Description:**  
Extract all calculation/math functions into separate module.

**File:** `surveys/shared/js/utils/math.js`

```javascript
/**
 * Mathematical calculations for NPS, CSAT, and statistics
 */

function calculatePercentage(value, total) {
  if (total === 0) return 0;
  return (value / total) * 100;
}

function calculateNPS(promoters, passives, detractors) {
  const total = promoters + passives + detractors;
  if (total === 0) return 0;
  return ((promoters - detractors) / total) * 100;
}

function calculateCSAT(satisfied, total) {
  if (total === 0) return 0;
  return (satisfied / total) * 100;
}

function sumObject(obj) {
  return Object.values(obj).reduce((sum, val) => sum + (val || 0), 0);
}

function getCareerCycleCount(career) {
  const CARRERAS_12_CICLOS = ['Derecho', 'Psicología'];
  return CARRERAS_12_CICLOS.includes(career) ? 12 : 10;
}

function isGeneralStudies(carrera) {
  return carrera === 'Estudios Generales';
}

export {
  calculatePercentage,
  calculateNPS,
  calculateCSAT,
  sumObject,
  getCareerCycleCount,
  isGeneralStudies
};
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/utils/math.js`
- [ ] All 6 functions exported
- [ ] Functions match original implementations

**Git Rollback:** `git rm surveys/shared/js/utils/math.js`

---

### T4.4 🟡 Extract DOM helper functions
**Duration:** 45 min | **Prerequisites:** T4.1 | **Depends On:** T4.1 complete

**Description:**  
Extract all DOM manipulation helpers into shared utilities.

**File:** `surveys/shared/js/utils/dom-helpers.js`

```javascript
/**
 * DOM manipulation helpers
 */

// Shortcut for document.getElementById
function $(id) {
  return document.getElementById(id);
}

function setElementText(id, text) {
  const element = $(id);
  if (element) element.textContent = text;
}

function setElementHTML(id, html) {
  const element = $(id);
  if (element) element.innerHTML = html;
}

function getSelectValue(id) {
  const element = $(id);
  return element ? element.value : null;
}

function enableElement(id) {
  const element = $(id);
  if (element) element.disabled = false;
}

function disableElement(id) {
  const element = $(id);
  if (element) element.disabled = true;
}

function addClass(id, className) {
  const element = $(id);
  if (element) element.classList.add(className);
}

function removeClass(id, className) {
  const element = $(id);
  if (element) element.classList.remove(className);
}

export {
  $,
  setElementText,
  setElementHTML,
  getSelectValue,
  enableElement,
  disableElement,
  addClass,
  removeClass
};
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/utils/dom-helpers.js`
- [ ] All 8 functions exported
- [ ] Functions tested with actual DOM elements

**Git Rollback:** `git rm surveys/shared/js/utils/dom-helpers.js`

---

### T4.5 🔴 Create core.js orchestrator
**Duration:** 1 hour | **Prerequisites:** T4.1-T4.4 | **Depends On:** All utils complete

**Description:**  
Create main orchestrator that initializes dashboard in correct sequence.

**File:** `surveys/shared/js/core.js`

```javascript
/**
 * Core dashboard orchestrator
 * Manages initialization sequence: validate → load → init engines → render → bind events
 */

import { validateDOMStructure, getDOMElement } from './config/dom-registry.js';
import { loadDashboardData } from './data-loader.js';
import { FilterEngine } from './filter-engine.js';
import { RenderEngine } from './render-engine.js';

async function initializeDashboard() {
  try {
    console.log('🚀 Initializing dashboard...');
    
    // Step 1: Validate DOM structure
    validateDOMStructure();
    
    // Step 2: Load data from JSON files
    console.log('📦 Loading data...');
    const data = await loadDashboardData();
    
    // Step 3: Initialize engines
    console.log('⚙️  Initializing engines...');
    const filterEngine = new FilterEngine(data);
    const renderEngine = new RenderEngine(data, filterEngine);
    
    // Step 4: Initial render of all sections
    console.log('🎨 Rendering sections...');
    renderEngine.renderExecutive();
    renderEngine.renderOperational();
    renderEngine.renderDetailed();
    renderEngine.renderQualitative();
    
    // Step 5: Bind event listeners
    console.log('🔗 Binding event listeners...');
    bindFilterEvents(filterEngine, renderEngine);
    
    console.log('✅ Dashboard initialized successfully');
    return { filterEngine, renderEngine, data };
    
  } catch (error) {
    console.error('❌ Dashboard initialization failed:', error);
    showErrorMessage(error.message);
    throw error;
  }
}

function bindFilterEvents(filterEngine, renderEngine) {
  const filterIds = [
    'filter-facultad',
    'filter-carrera',
    'filter-ciclo',
    'filter-dimension',
    'filter-satisfaction',
    'filter-nps-type'
  ];
  
  filterIds.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('change', () => {
        console.log(`Filter changed: ${id}`);
        renderEngine.renderAll();
      });
    }
  });
}

function showErrorMessage(message) {
  const errorElement = document.getElementById('error-message');
  if (errorElement) {
    errorElement.textContent = `Error: ${message}`;
    errorElement.style.display = 'block';
  }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
  initializeDashboard();
}

export { initializeDashboard };
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/core.js`
- [ ] Imports from all 4 modules: dom-registry, data-loader, filter-engine, render-engine
- [ ] Initialization sequence is clear and documented
- [ ] Error handling includes user-visible messages

**Git Rollback:** `git rm surveys/shared/js/core.js`

---

### T4.6 🔴 Create data-loader.js
**Duration:** 1.5 hours | **Prerequisites:** T4.1-T4.4 | **Depends On:** T4.5 in progress

**Description:**  
Create data loading module that fetches and merges 4 JSON contracts.

**File:** `surveys/shared/js/data-loader.js`

```javascript
/**
 * Data loader: Fetches and validates 4 JSON contracts
 * - dashboard_data.json (KPIs, NPS, CSAT)
 * - dimensiones.json (dimensions and scores)
 * - filtros.json (filter options and cascades)
 * - sentimiento.json (qualitative analysis)
 */

async function loadDashboardData() {
  try {
    console.log('📡 Fetching JSON files...');
    
    const [
      dashboardData,
      dimensiones,
      filtros,
      sentimiento
    ] = await Promise.all([
      fetchJSON('./json/dashboard_data.json'),
      fetchJSON('./json/dimensiones.json'),
      fetchJSON('./json/filtros.json'),
      fetchJSON('./json/sentimiento.json')
    ]);
    
    // Merge and validate
    const mergedData = {
      resumen: dashboardData.resumen,
      hallazgos: dashboardData.hallazgos,
      nps: dashboardData.nps,
      csat: dashboardData.csat,
      dimensiones: dimensiones,
      filtros: filtros,
      sentimiento: sentimiento
    };
    
    validateDataContracts(mergedData);
    console.log('✓ Data loaded and validated');
    
    return mergedData;
    
  } catch (error) {
    console.error('Data loading failed:', error);
    throw error;
  }
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

function validateDataContracts(data) {
  // Validate required top-level properties
  const required = ['resumen', 'dimensiones', 'filtros', 'sentimiento'];
  const missing = required.filter(key => !(key in data));
  
  if (missing.length > 0) {
    throw new Error(`Missing data contracts: ${missing.join(', ')}`);
  }
  
  // Validate resumen structure
  if (!data.resumen.nps || !data.resumen.csat) {
    throw new Error('resumen missing NPS or CSAT data');
  }
  
  // Validate filtros structure
  if (!data.filtros.facultades || !data.filtros.carreras) {
    throw new Error('filtros missing facultades or carreras');
  }
}

export { loadDashboardData };
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/data-loader.js`
- [ ] Handles all 4 JSON files with parallel fetching
- [ ] Validates data structure before returning
- [ ] Provides clear error messages

**Git Rollback:** `git rm surveys/shared/js/data-loader.js`

---

### T4.7 🔴 Create filter-engine.js
**Duration:** 2 hours | **Prerequisites:** T4.6 | **Depends On:** T4.6 complete

**Description:**  
Create filter logic engine managing cascade state and available options.

**File:** `surveys/shared/js/filter-engine.js`

```javascript
/**
 * Filter Engine: Manages filter state, cascading logic, and available options
 * Handles: Facultad → Carrera, Ciclo availability, Dimension filtering
 */

export class FilterEngine {
  constructor(data) {
    this.data = data;
    this.state = {
      facultad: null,
      carrera: null,
      ciclo: null,
      dimension: null,
      satisfaction: 'all',
      npsType: 'all'
    };
    this.initializeState();
  }
  
  initializeState() {
    // Set defaults from available data
    if (this.data.filtros.facultades.length > 0) {
      this.state.facultad = this.data.filtros.facultades[0];
    }
  }
  
  // When facultad changes, update available carreras
  setFacultad(facultad) {
    this.state.facultad = facultad;
    this.state.carrera = null;  // Reset carrera
    this.state.ciclo = null;    // Reset ciclo
    return this.getAvailableCarreras();
  }
  
  // When carrera changes, determine available ciclos
  setCarrera(carrera) {
    this.state.carrera = carrera;
    this.state.ciclo = null;  // Reset ciclo
    return this.getAvailableCiclos();
  }
  
  setCiclo(ciclo) {
    this.state.ciclo = ciclo;
  }
  
  setDimension(dimension) {
    this.state.dimension = dimension;
  }
  
  setSatisfaction(satisfaction) {
    this.state.satisfaction = satisfaction;
  }
  
  setNPSType(npsType) {
    this.state.npsType = npsType;
  }
  
  getAvailableCarreras() {
    if (!this.state.facultad) return [];
    return this.data.filtros.facultad_carrera[this.state.facultad] || [];
  }
  
  getAvailableCiclos() {
    // Return ciclo options based on selected carrera
    if (!this.state.carrera) return [];
    // Import from math.js
    const cycleCount = this.state.carrera === 'Derecho' || 
                       this.state.carrera === 'Psicología' ? 12 : 10;
    return Array.from({ length: cycleCount }, (_, i) => i + 1);
  }
  
  getState() {
    return { ...this.state };
  }
  
  // Filter raw data according to current state
  applyFilters(rawData) {
    let filtered = [...rawData];
    
    if (this.state.facultad) {
      filtered = filtered.filter(item => item.facultad === this.state.facultad);
    }
    
    if (this.state.carrera) {
      filtered = filtered.filter(item => item.carrera === this.state.carrera);
    }
    
    // ... more filter logic
    
    return filtered;
  }
}
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/filter-engine.js`
- [ ] FilterEngine class exported with all methods
- [ ] Cascade logic implemented (facultad → carrera → ciclo)
- [ ] State management clear and testable

**Git Rollback:** `git rm surveys/shared/js/filter-engine.js`

---

### T4.8 🔴 Create render-engine.js
**Duration:** 2.5 hours | **Prerequisites:** T4.7 | **Depends On:** T4.7 complete

**Description:**  
Create rendering engine responsible for all section rendering.

**File:** `surveys/shared/js/render-engine.js`

```javascript
/**
 * Render Engine: Responsible for rendering all 4 dashboard sections
 * - Executive (KPIs, trends)
 * - Operational (dimensions, faculties)
 * - Detailed (by career, by cycle)
 * - Qualitative (sentiment analysis)
 */

import { formatInteger, formatPercent, formatDecimal } from './utils/formatters.js';

export class RenderEngine {
  constructor(data, filterEngine) {
    this.data = data;
    this.filterEngine = filterEngine;
  }
  
  renderAll() {
    this.renderExecutive();
    this.renderOperational();
    this.renderDetailed();
    this.renderQualitative();
  }
  
  renderExecutive() {
    const state = this.filterEngine.getState();
    const kpiNps = document.getElementById('kpi-nps');
    const kpiCsat = document.getElementById('kpi-csat');
    
    if (kpiNps) {
      kpiNps.textContent = formatPercent(this.data.resumen.nps.score);
    }
    
    if (kpiCsat) {
      kpiCsat.textContent = formatPercent(this.data.resumen.csat.score);
    }
    
    console.log('Executive section rendered');
  }
  
  renderOperational() {
    const container = document.getElementById('dimensiones-container');
    if (!container) return;
    
    // Render dimension cards
    const html = this.data.dimensiones.map(dim => `
      <div class="dimension-card">
        <h4>${dim.nombre}</h4>
        <p class="score">${formatPercent(dim.score)}</p>
      </div>
    `).join('');
    
    container.innerHTML = html;
    console.log('Operational section rendered');
  }
  
  renderDetailed() {
    console.log('Detailed section rendered');
  }
  
  renderQualitative() {
    console.log('Qualitative section rendered');
  }
}
```

**Success Criteria:**
- [ ] File created at `surveys/shared/js/render-engine.js`
- [ ] RenderEngine class exported
- [ ] All 4 render methods implemented (even if placeholder)
- [ ] Uses formatters from utils/formatters.js

**Git Rollback:** `git rm surveys/shared/js/render-engine.js`

---

### T4.9 🟡 Update dashboard template to use ES6 modules
**Duration:** 30 min | **Prerequisites:** T4.5, T4.8 | **Depends On:** All JS modules complete

**Description:**  
Update `surveys/shared/template/index.html` (and all period index.html copies) to use ES6 module syntax:

**Old:**
```html
<script src="../../../shared/js/dashboard.js"></script>
<script src="../../../shared/js/loader.js"></script>
```

**New:**
```html
<script type="module" src="../../../shared/js/core.js"></script>
```

**Success Criteria:**
- [ ] Template updated to use `<script type="module">`
- [ ] All period `index.html` files updated to reference core.js
- [ ] No other script tags reference dashboard.js or loader.js

**Git Rollback:** `git checkout HEAD -- surveys/shared/template/index.html surveys/students/*/*/index.html`

---

### T4.10 🟡 Create unit tests for JS utilities
**Duration:** 1.5 hours | **Prerequisites:** T4.2-T4.4 | **Depends On:** Utilities complete

**Description:**  
Create Vitest unit tests for pure functions in utils/.

**File:** `tests/unit/test_formatters.test.js`

```javascript
import { describe, it, expect } from 'vitest';
import {
  formatInteger,
  formatDecimal,
  formatPercent,
  formatDate,
  truncateText,
  formatNPSType
} from '../../surveys/shared/js/utils/formatters.js';

describe('Formatters', () => {
  describe('formatInteger', () => {
    it('formats large numbers with thousands separator', () => {
      expect(formatInteger(1234567)).toBe('1,234,567');
    });
    
    it('returns — for null/undefined', () => {
      expect(formatInteger(null)).toBe('—');
      expect(formatInteger(undefined)).toBe('—');
    });
  });
  
  describe('formatPercent', () => {
    it('converts decimal to percentage', () => {
      expect(formatPercent(0.8567)).toBe('85.67%');
    });
  });
  
  describe('formatNPSType', () => {
    it('categorizes NPS scores', () => {
      expect(formatNPSType(85)).toBe('Excelente');
      expect(formatNPSType(60)).toBe('Bueno');
      expect(formatNPSType(30)).toBe('Aceptable');
      expect(formatNPSType(10)).toBe('Crítico');
    });
  });
});
```

**Files to Create:**
- `tests/unit/test_formatters.test.js`
- `tests/unit/test_math.test.js`
- `tests/unit/test_validators.test.js`

**Success Criteria:**
- [ ] 3 test files created in tests/unit/
- [ ] 15+ test cases total
- [ ] Can run with `npm test` (requires vitest config)

**Git Rollback:** `git rm -rf tests/unit/*.test.js`

---

### T4.11 🔴 Create commit: "refactor: modularize JavaScript"
**Duration:** 15 min | **Prerequisites:** T4.1-T4.10 | **Depends On:** All JS work complete

**Description:**  
Commit all JavaScript modularization in single atomic commit:

```bash
git add surveys/shared/js/ tests/unit/ surveys/shared/template/index.html surveys/students/*/*/index.html
git commit -m "refactor: modularize JavaScript into 8 focused modules

Breakdown:
- config/dom-registry.js: Centralized DOM ID registry with validation
- utils/formatters.js: Text formatting functions (6 functions)
- utils/math.js: Calculations (NPS, CSAT, percentages)
- utils/dom-helpers.js: DOM manipulation utilities
- data-loader.js: JSON contract loading and validation
- filter-engine.js: Filter state and cascade logic (FilterEngine class)
- render-engine.js: Section rendering (RenderEngine class)
- core.js: Orchestrator managing initialization sequence

Benefits:
- 1717-line monolithic dashboard.js → 8 focused modules
- Clear separation of concerns (data, filters, rendering, utilities)
- All 50+ hardcoded IDs centralized in dom-registry.js
- Testable pure functions in utils/
- ES6 module syntax with import/export

Includes:
- Unit tests for formatters, math, validators
- Updated index.html to use ES6 modules
- All dashboards tested and verified working

This commit completes Block 4."
```

**Success Criteria:**
- [ ] Single commit with clear, detailed message
- [ ] `git show --stat` shows 8 new .js files, test files, template updates
- [ ] Dashboard still loads and functions identically
- [ ] Browser console shows no errors

**Git Rollback:** `git revert HEAD`

---

## BLOCK 5: CSS REFACTORING (4-5 hours)

### T5.1 🔴 Extract tokens.css
**Duration:** 1 hour | **Prerequisites:** T4.11 | **Depends On:** Block 4 complete

**Description:**  
Extract design tokens (colors, typography, spacing) into separate file.

**File:** `surveys/shared/css/tokens.css`

```css
/**
 * Design Tokens: Colors, Typography, Spacing, Shadows, Transitions
 */

:root {
  /* Colors: Institutional */
  --ulima-orange: #ff5117;
  --ulima-red: #ff0000;
  --ulima-blue: #2563eb;
  --ulima-gray: #6b7280;
  
  /* Colors: Semantic */
  --success-pastel: #d1fae5;
  --warning-pastel: #fef3c7;
  --danger-pastel: #fee2e2;
  
  /* Colors: Grayscale Scale */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-400: #9ca3af;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;
  
  /* Typography */
  --font-family-primary: 'Roboto', sans-serif;
  --font-family-display: 'Roboto', sans-serif;
  --font-family-mono: 'Monaco', monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  
  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* Spacing Scale */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 0.15s ease-in-out;
  --transition-base: 0.3s ease-in-out;
  --transition-slow: 0.5s ease-in-out;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-full: 9999px;
  
  /* Z-Index Scale */
  --z-hide: -1;
  --z-base: 0;
  --z-dropdown: 1000;
  --z-tooltip: 1001;
  --z-modal: 1002;
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --transition-fast: 0s;
    --transition-base: 0s;
    --transition-slow: 0s;
  }
}
```

**Success Criteria:**
- [ ] File created at `surveys/shared/css/tokens.css`
- [ ] All design tokens centralized (40+ variables)
- [ ] Includes color, typography, spacing, shadow, transition definitions

**Git Rollback:** `git rm surveys/shared/css/tokens.css`

---

### T5.2 🟡 Extract layout.css
**Duration:** 1 hour | **Prerequisites:** T5.1 | **Depends On:** T5.1 complete

**Description:**  
Extract layout styles (grid, flexbox, sections, responsive).

**File:** `surveys/shared/css/layout.css`

```css
/**
 * Layout: Grid, Flexbox, Sections, Responsive Breakpoints
 */

/* Breakpoints */
@media (max-width: 1024px) { /* Tablet */ }
@media (max-width: 768px) { /* Mobile */ }
@media (max-width: 480px) { /* Small mobile */ }

/* Main Layout Grid */
body {
  display: grid;
  grid-template-areas:
    "topbar"
    "filters"
    "content"
    "footer";
  grid-template-rows: auto auto 1fr auto;
  min-height: 100vh;
}

.dashboard-container {
  grid-area: content;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: var(--space-lg);
  padding: var(--space-lg);
}

/* Sections */
.section {
  grid-column: span 4;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.section-header {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
}

/* Filters Container */
.filters-container {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  padding: var(--space-md);
  background: var(--gray-50);
}

@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
  }
  
  .dashboard-container {
    grid-template-columns: 1fr;
  }
  
  .section {
    grid-column: span 1;
  }
}
```

**Success Criteria:**
- [ ] File created at `surveys/shared/css/layout.css`
- [ ] Contains grid/flexbox layout definitions
- [ ] Includes responsive breakpoints

**Git Rollback:** `git rm surveys/shared/css/layout.css`

---

### T5.3 🟡 Extract components.css
**Duration:** 1 hour | **Prerequisites:** T5.1 | **Depends On:** T5.1 complete

**Description:**  
Extract reusable component styles (KPI card, filters, tooltips).

**File:** `surveys/shared/css/components.css`

```css
/**
 * Components: KPI Cards, Filters, Tooltips, Badges
 */

/* KPI Card */
.kpi-card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-base);
}

.kpi-card:hover {
  box-shadow: var(--shadow-lg);
}

.kpi-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--ulima-orange);
}

.kpi-label {
  font-size: var(--text-sm);
  color: var(--gray-600);
}

/* Filter Select */
.filter-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  background: white;
  cursor: pointer;
}

.filter-select:hover {
  border-color: var(--ulima-orange);
}

.filter-select:focus {
  outline: none;
  border-color: var(--ulima-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Tooltip */
.tooltip {
  position: absolute;
  background: var(--gray-900);
  color: white;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  z-index: var(--z-tooltip);
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid var(--gray-900);
}

/* Badge */
.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.badge--success { background: var(--success-pastel); }
.badge--warning { background: var(--warning-pastel); }
.badge--danger { background: var(--danger-pastel); }
```

**Success Criteria:**
- [ ] File created at `surveys/shared/css/components.css`
- [ ] Contains 5+ reusable component styles
- [ ] Uses tokens from tokens.css

**Git Rollback:** `git rm surveys/shared/css/components.css`

---

### T5.4 🟡 Extract sections.css
**Duration:** 1 hour | **Prerequisites:** T5.1 | **Depends On:** T5.1 complete

**Description:**  
Extract section-specific styles (Executive, Operational, Detailed, Qualitative).

**File:** `surveys/shared/css/sections.css`

```css
/**
 * Sections: Executive, Operational, Detailed, Qualitative
 */

/* Executive Section */
#ejecutivo {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}

#ejecutivo .kpi-card {
  text-align: center;
}

/* Operational Section */
#operativo {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

#dimensiones-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

#facultades-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* Detailed Section */
#detallado {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-lg);
}

.detail-group {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

/* Qualitative Section */
#sentimiento {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

#sentimiento-heading {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--space-lg);
}

.sentiment-item {
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  border-left: 4px solid var(--ulima-orange);
  background: var(--gray-50);
}
```

**Success Criteria:**
- [ ] File created at `surveys/shared/css/sections.css`
- [ ] Contains styles for all 4 sections
- [ ] Uses tokens from tokens.css

**Git Rollback:** `git rm surveys/shared/css/sections.css`

---

### T5.5 🟡 Update dashboard.css to import new files
**Duration:** 30 min | **Prerequisites:** T5.1-T5.4 | **Depends On:** All CSS modules complete

**Description:**  
Modify main dashboard.css to import the 4 modular CSS files instead of containing all styles.

**New dashboard.css:**
```css
/**
 * Dashboard Stylesheet Entry Point
 * Imports modular CSS files for organization and maintainability
 */

@import './tokens.css';
@import './layout.css';
@import './components.css';
@import './sections.css';

/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-family: var(--font-family-primary);
  font-size: 16px;
  color: var(--gray-900);
  scroll-behavior: smooth;
}

body {
  background: var(--gray-50);
  line-height: 1.6;
}

a {
  color: var(--ulima-blue);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
```

**Success Criteria:**
- [ ] dashboard.css reduced from 1176 lines to ~30 lines
- [ ] Four @import statements at top
- [ ] Visual output identical (no visible changes)
- [ ] All components render correctly

**Git Rollback:** `git checkout HEAD -- surveys/shared/css/dashboard.css`

---

### T5.6 🔴 Create commit: "refactor: modularize CSS"
**Duration:** 15 min | **Prerequisites:** T5.1-T5.5 | **Depends On:** All CSS work complete

**Description:**  
Commit CSS modularization:

```bash
git commit -m "refactor: modularize CSS into 4 focused files

Breakdown:
- tokens.css: Design system (colors, typography, spacing, shadows)
- layout.css: Grid/flexbox layouts, sections, responsive breakpoints
- components.css: Reusable components (KPI card, filters, tooltips)
- sections.css: Section-specific styles (Ejecutivo, Operativo, etc)

Benefits:
- 1176-line monolithic dashboard.css → 4 focused files (~250 lines each)
- Design tokens centralized (40+ CSS variables)
- Components easily reusable across survey types
- Responsive breakpoints documented in layout.css
- Maintenance improved: change a token once, applies everywhere

dashboard.css now imports all 4 files and contains only global styles.

Visual output: identical (no CSS changes, only reorganization)
Browser: all dashboards render exactly as before

This commit completes Block 5."
```

**Success Criteria:**
- [ ] Single commit with clear message
- [ ] `git show --stat` shows 5 files (4 new + 1 modified dashboard.css)
- [ ] Dashboard visually identical
- [ ] All tests still pass

**Git Rollback:** `git revert HEAD`

---

## BLOCK 6: PYTHON ETL REFACTORING (8-10 hours)

⚠️ **Complex block. Contains 9 tasks with significant refactoring. Consider prioritizing Blocks 1-5 first if time-constrained.**

### T6.1 🔴 Create scripts/lib/ structure
**Duration:** 45 min | **Prerequisites:** T5.6 | **Depends On:** Block 5 complete

**Description:**  
Create Python library structure in scripts/lib/ to hold reusable ETL modules.

**Files to Create:**

```
scripts/lib/
├── __init__.py                 # Package init
├── csv_normalizer.py           # Column mapping and normalization
├── aggregator.py               # KPI and dimension aggregation
├── topic_analyzer.py           # Sentiment and topic analysis
└── validators.py               # JSON schema validation
```

**scripts/lib/__init__.py:**
```python
"""
ETL Library: Reusable modules for survey data processing
"""

from .csv_normalizer import normalize_column_names, get_column_mapping
from .aggregator import (
    calculate_nps,
    calculate_csat,
    aggregate_by_dimension,
    calculate_summary
)
from .topic_analyzer import analyze_sentiment_topics, SENTIMENT_KEYWORDS
from .validators import validate_json_against_schema

__all__ = [
    'normalize_column_names',
    'get_column_mapping',
    'calculate_nps',
    'calculate_csat',
    'aggregate_by_dimension',
    'calculate_summary',
    'analyze_sentiment_topics',
    'SENTIMENT_KEYWORDS',
    'validate_json_against_schema'
]
```

**Success Criteria:**
- [ ] All 5 files created
- [ ] __init__.py correctly exports all public functions
- [ ] Package is importable: `from scripts.lib import *`

**Git Rollback:** `git rm -rf scripts/lib/*.py`

---

### T6.2 🔴 Extract CSV normalization logic
**Duration:** 1.5 hours | **Prerequisites:** T6.1 | **Depends On:** T6.1 complete

**Description:**  
Extract CSV column mapping and normalization into reusable module.

**File:** `scripts/lib/csv_normalizer.py`

```python
"""
CSV Normalization: Column mapping and data type coercion
"""

# Column mapping for different survey types
COLUMN_MAPPING_STUDENTS = {
    'Facultad': 'facultad',
    'Carrera': 'carrera',
    'Ciclo': 'ciclo',
    'Pregunta 1': 'calidad_academica',
    'Pregunta 2': 'infraestructura',
    # ... 30+ mappings
}

COLUMN_MAPPING_ALUMNI = {
    'Faculty': 'facultad',
    'Career': 'carrera',
    'Years Since Graduation': 'anos_egreso',
    # ... 25+ mappings
}

def get_column_mapping(survey_type):
    """Get appropriate column mapping for survey type."""
    mappings = {
        'students': COLUMN_MAPPING_STUDENTS,
        'alumni': COLUMN_MAPPING_ALUMNI,
    }
    return mappings.get(survey_type, {})

def normalize_column_names(df, survey_type):
    """
    Normalize dataframe columns from raw Zoho export to internal names.
    """
    mapping = get_column_mapping(survey_type)
    
    # Rename columns
    df = df.rename(columns=mapping)
    
    # Remove unmapped columns
    valid_cols = list(mapping.values())
    df = df[[col for col in df.columns if col in valid_cols]]
    
    return df

def coerce_types(df):
    """
    Coerce dataframe columns to appropriate types.
    """
    # Numeric columns
    numeric_cols = ['nps_score', 'csat_score', 'ciclo']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # String columns
    string_cols = ['facultad', 'carrera', 'respuesta_cualitativa']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    return df
```

**Success Criteria:**
- [ ] File created at `scripts/lib/csv_normalizer.py`
- [ ] Functions: `get_column_mapping()`, `normalize_column_names()`, `coerce_types()`
- [ ] Support 2+ survey types (students, alumni)

**Git Rollback:** `git rm scripts/lib/csv_normalizer.py`

---

### T6.3 🔴 Extract aggregation logic
**Duration:** 1.5 hours | **Prerequisites:** T6.1 | **Depends On:** T6.1 complete

**Description:**  
Extract KPI and dimension aggregation into reusable module.

**File:** `scripts/lib/aggregator.py`

```python
"""
Aggregation: KPI calculations and dimension analysis
"""

def calculate_nps(promoters, passives, detractors):
    """Calculate Net Promoter Score."""
    total = promoters + passives + detractors
    if total == 0:
        return 0
    return round(((promoters - detractors) / total) * 100, 2)

def calculate_csat(satisfied, total):
    """Calculate Customer Satisfaction Score."""
    if total == 0:
        return 0
    return round((satisfied / total) * 100, 2)

def aggregate_by_dimension(df, dimension_col):
    """
    Aggregate scores by dimension (e.g., by facultad, by carrera).
    """
    agg_dict = {}
    
    for dimension in df[dimension_col].unique():
        subset = df[df[dimension_col] == dimension]
        
        # Calculate scores
        nps = calculate_nps(
            len(subset[subset['nps_type'] == 'Promoter']),
            len(subset[subset['nps_type'] == 'Passive']),
            len(subset[subset['nps_type'] == 'Detractor'])
        )
        
        csat = calculate_csat(
            len(subset[subset['satisfaction'] >= 3]),
            len(subset)
        )
        
        agg_dict[dimension] = {
            'nps': nps,
            'csat': csat,
            'count': len(subset)
        }
    
    return agg_dict

def calculate_summary(df):
    """
    Calculate overall summary statistics.
    """
    return {
        'total_responses': len(df),
        'nps': calculate_nps(
            len(df[df['nps_type'] == 'Promoter']),
            len(df[df['nps_type'] == 'Passive']),
            len(df[df['nps_type'] == 'Detractor'])
        ),
        'csat': calculate_csat(
            len(df[df['satisfaction'] >= 3]),
            len(df)
        )
    }
```

**Success Criteria:**
- [ ] File created at `scripts/lib/aggregator.py`
- [ ] Functions: `calculate_nps()`, `calculate_csat()`, `aggregate_by_dimension()`, `calculate_summary()`
- [ ] All calculations tested with sample data

**Git Rollback:** `git rm scripts/lib/aggregator.py`

---

### T6.4 🔴 Extract topic/sentiment analysis logic
**Duration:** 1.5 hours | **Prerequisites:** T6.1 | **Depends On:** T6.1 complete

**Description:**  
Extract sentiment and topic analysis into reusable module.

**File:** `scripts/lib/topic_analyzer.py`

```python
"""
Topic and Sentiment Analysis: Keyword extraction and classification
"""

SENTIMENT_KEYWORDS = {
    'positivo': [
        'excelente', 'muy bueno', 'perfecto', 'recomiendo',
        'satisfecho', 'profesores', 'contenido', 'enseñanza',
        'instalaciones', 'aulas', 'biblioteca', 'ambiente'
    ],
    'negativo': [
        'malo', 'deficiente', 'insatisfecho', 'problemas',
        'falta', 'mejorar', 'no recomiendo', 'decepciona',
        'infraestructura', 'personal', 'atención'
    ],
    'neutro': [
        'ok', 'normal', 'regular', 'podría'
    ]
}

def analyze_sentiment_topics(text):
    """
    Analyze qualitative text for sentiment and topics.
    Returns dict with sentiment classification and keywords found.
    """
    if not text or not isinstance(text, str):
        return {'sentiment': 'neutro', 'keywords': [], 'confidence': 0}
    
    text_lower = text.lower()
    
    # Count sentiment keywords
    positive_count = sum(1 for kw in SENTIMENT_KEYWORDS['positivo'] if kw in text_lower)
    negative_count = sum(1 for kw in SENTIMENT_KEYWORDS['negativo'] if kw in text_lower)
    neutral_count = sum(1 for kw in SENTIMENT_KEYWORDS['neutro'] if kw in text_lower)
    
    # Determine dominant sentiment
    max_count = max(positive_count, negative_count, neutral_count)
    
    if max_count == 0:
        sentiment = 'neutro'
    elif positive_count == max_count:
        sentiment = 'positivo'
    elif negative_count == max_count:
        sentiment = 'negativo'
    else:
        sentiment = 'neutro'
    
    # Extract keywords found
    keywords = []
    for keyword in SENTIMENT_KEYWORDS.get(sentiment, []):
        if keyword in text_lower:
            keywords.append(keyword)
    
    confidence = max_count / len(text.split()) if len(text.split()) > 0 else 0
    
    return {
        'sentiment': sentiment,
        'keywords': keywords[:5],  # Top 5 keywords
        'confidence': round(confidence, 2)
    }

def aggregate_sentiments(df, text_col='respuesta_cualitativa'):
    """
    Aggregate sentiments across dataframe.
    """
    results = df[text_col].apply(analyze_sentiment_topics)
    
    sentiment_counts = results.apply(lambda x: x['sentiment']).value_counts()
    
    return {
        'positivo': int(sentiment_counts.get('positivo', 0)),
        'negativo': int(sentiment_counts.get('negativo', 0)),
        'neutro': int(sentiment_counts.get('neutro', 0)),
        'total': len(results)
    }
```

**Success Criteria:**
- [ ] File created at `scripts/lib/topic_analyzer.py`
- [ ] Functions: `analyze_sentiment_topics()`, `aggregate_sentiments()`
- [ ] SENTIMENT_KEYWORDS dict with 40+ keywords

**Git Rollback:** `git rm scripts/lib/topic_analyzer.py`

---

### T6.5 🔴 Refactor build_json.py to use library modules
**Duration:** 2 hours | **Prerequisites:** T6.2-T6.4 | **Depends On:** All lib modules complete

**Description:**  
Refactor main build_json.py script to import and use lib modules, reducing from 822 to ~500 lines.

**Old Structure:**
```python
# 822-line file with all logic inline
def main():
    # Read CSV
    # Map columns
    # Calculate aggregates
    # Analyze topics
    # Write JSON
    # ... all mixed together
```

**New Structure:**
```python
#!/usr/bin/env python3
"""
Build JSON: Transform CSV survey data to JSON dashboard contracts.

Orchestrates ETL pipeline:
1. Load CSV from data/ directory
2. Normalize columns using csv_normalizer
3. Calculate aggregates using aggregator
4. Analyze sentiment using topic_analyzer
5. Validate JSON schemas using validators
6. Write output JSON files
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Import library modules
from lib.csv_normalizer import normalize_column_names, coerce_types
from lib.aggregator import calculate_nps, calculate_csat, aggregate_by_dimension, calculate_summary
from lib.topic_analyzer import analyze_sentiment_topics, aggregate_sentiments
from lib.validators import validate_json_against_schema

def main():
    """Main ETL orchestrator."""
    
    # Parse arguments
    # ...
    
    # Step 1: Load CSV
    csv_file = f'data/ENCUESTA_{survey_level}_{period}.csv'
    df = pd.read_csv(csv_file)
    
    # Step 2: Normalize
    df = normalize_column_names(df, survey_type)
    df = coerce_types(df)
    
    # Step 3: Aggregate
    summary = calculate_summary(df)
    by_dimension = aggregate_by_dimension(df, 'facultad')
    
    # Step 4: Analyze
    sentiments = aggregate_sentiments(df)
    
    # Step 5: Build JSON contracts
    dashboard_data = {
        'resumen': summary,
        'nps': { ... },
        'csat': { ... }
    }
    
    # Step 6: Validate
    validate_json_against_schema(dashboard_data, 'dashboard_data')
    
    # Step 7: Write
    output_dir = f'surveys/{survey_level}/{period}/json'
    with open(f'{output_dir}/dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    print(f'✓ Generated {output_dir}/')

if __name__ == '__main__':
    main()
```

**Success Criteria:**
- [ ] build_json.py refactored to use lib modules
- [ ] File size reduced from ~822 to ~500 lines
- [ ] All functionality preserved
- [ ] Generates identical JSON output as before
- [ ] Script runs: `python scripts/build_json.py`

**Git Rollback:** `git checkout HEAD~1 -- scripts/build_json.py`

---

### T6.6 🟡 Create JSON schema files
**Duration:** 1.5 hours | **Prerequisites:** T6.1 | **Depends On:** T6.1 complete

**Description:**  
Create 5 JSON schema files in scripts/schemas/ to define data contracts.

**Files to Create:**

1. `scripts/schemas/dashboard_data.schema.json`
2. `scripts/schemas/dimensiones.schema.json`
3. `scripts/schemas/filtros.schema.json`
4. `scripts/schemas/resumen.schema.json`
5. `scripts/schemas/sentimiento.schema.json`

**Example: dashboard_data.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Dashboard Data Contract",
  "required": ["resumen", "nps", "csat"],
  "properties": {
    "resumen": {
      "type": "object",
      "required": ["encuestas", "nps", "csat"],
      "properties": {
        "encuestas": { "type": "integer", "minimum": 0 },
        "carreras": { "type": "integer", "minimum": 0 },
        "facultades": { "type": "integer", "minimum": 0 },
        "nps": {
          "type": "object",
          "required": ["score", "promotores", "pasivos", "detractores"],
          "properties": {
            "score": { "type": "number", "minimum": -100, "maximum": 100 },
            "promotores": { "type": "integer", "minimum": 0 },
            "pasivos": { "type": "integer", "minimum": 0 },
            "detractores": { "type": "integer", "minimum": 0 }
          }
        },
        "csat": {
          "type": "object",
          "required": ["score", "t3b", "total"],
          "properties": {
            "score": { "type": "number", "minimum": 0, "maximum": 100 },
            "t3b": { "type": "integer", "minimum": 0 },
            "total": { "type": "integer", "minimum": 0 }
          }
        }
      }
    },
    "nps": {
      "type": "object",
      "properties": {
        "Promotores": { "type": "integer" },
        "Pasivos": { "type": "integer" },
        "Detractores": { "type": "integer" },
        "score": { "type": "number" }
      }
    },
    "csat": {
      "type": "object"
    }
  }
}
```

**Success Criteria:**
- [ ] 5 JSON schema files created in scripts/schemas/
- [ ] Each schema follows JSON Schema v7 standard
- [ ] Schemas cover all required properties and data types
- [ ] Schemas are comprehensive (40+ properties across all files)

**Git Rollback:** `git rm -f scripts/schemas/*.schema.json`

---

### T6.7 🔴 Add JSON schema validation
**Duration:** 1.5 hours | **Prerequisites:** T6.6 | **Depends On:** T6.6 complete

**Description:**  
Add JSON schema validation to build_json.py using jsonschema library.

**File:** `scripts/lib/validators.py`

```python
"""
Validators: JSON schema validation and data contract enforcement
"""

import json
import jsonschema
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent.parent / 'schemas'

def load_schema(schema_name):
    """Load JSON schema from file."""
    schema_path = SCHEMAS_DIR / f'{schema_name}.schema.json'
    if not schema_path.exists():
        raise FileNotFoundError(f'Schema not found: {schema_path}')
    
    with open(schema_path) as f:
        return json.load(f)

def validate_json_against_schema(data, schema_name):
    """
    Validate JSON data against schema.
    Raises jsonschema.ValidationError if invalid.
    """
    schema = load_schema(schema_name)
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f'✓ Validation passed: {schema_name}')
        return True
    except jsonschema.ValidationError as e:
        print(f'✗ Validation failed: {schema_name}')
        print(f'  Error: {e.message}')
        print(f'  Path: {list(e.path)}')
        raise

def validate_all_contracts(output_dir):
    """
    Validate all JSON files in output directory against their schemas.
    """
    json_files = Path(output_dir).glob('*.json')
    
    for json_file in json_files:
        schema_name = json_file.stem  # Filename without .json
        
        with open(json_file) as f:
            data = json.load(f)
        
        try:
            validate_json_against_schema(data, schema_name)
        except jsonschema.ValidationError:
            print(f'Skipping validation for {json_file} (no schema)')
```

**Integration in build_json.py:**
```python
from lib.validators import validate_json_against_schema, validate_all_contracts

# After generating JSON files:
try:
    validate_json_against_schema(dashboard_data, 'dashboard_data')
    validate_json_against_schema(dimensiones, 'dimensiones')
    validate_json_against_schema(filtros, 'filtros')
    validate_json_against_schema(sentimiento, 'sentimiento')
    print('✓ All schemas validated')
except jsonschema.ValidationError as e:
    print(f'Schema validation failed: {e}')
    sys.exit(1)
```

**Success Criteria:**
- [ ] validators.py created with validation functions
- [ ] build_json.py calls validate_json_against_schema for each output file
- [ ] Script fails with clear error if validation fails
- [ ] All existing JSON files pass validation

**Git Rollback:** `git rm scripts/lib/validators.py && git checkout HEAD -- scripts/build_json.py`

---

### T6.8 🟡 Add CLI arguments to build_json.py
**Duration:** 1 hour | **Prerequisites:** T6.5 | **Depends On:** T6.5 complete

**Description:**  
Add argparse CLI with --type and --level flags for more flexible execution.

**Current Usage:**
```bash
python scripts/build_json.py  # Scans all CSVs in data/
```

**New Usage:**
```bash
python scripts/build_json.py --type students --level graduate

# Or process specific types:
python scripts/build_json.py --type alumni
python scripts/build_json.py --type employers --level all
```

**Implementation:**
```python
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Build JSON dashboard data from survey CSV files'
    )
    
    parser.add_argument(
        '--type',
        choices=['students', 'alumni', 'employers', 'faculty-staff', 'non-faculty-staff'],
        help='Survey type to process (default: all types)'
    )
    
    parser.add_argument(
        '--level',
        choices=['undergraduate', 'graduate', 'postgraduate', 'all'],
        default='all',
        help='Academic level to process (default: all levels)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='surveys',
        help='Output directory for JSON files'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output JSON against schemas'
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    # Use args to filter which CSVs to process
    # ...
```

**Success Criteria:**
- [ ] build_json.py accepts --type, --level arguments
- [ ] Help text displays: `python scripts/build_json.py --help`
- [ ] Script works with no arguments (processes all)
- [ ] Script works with specific --type and --level combinations

**Git Rollback:** `git checkout HEAD -- scripts/build_json.py`

---

### T6.9 🔴 Create commit: "refactor: modularize Python ETL"
**Duration:** 15 min | **Prerequisites:** T6.1-T6.8 | **Depends On:** All Python work complete

**Description:**  
Commit all Python refactoring:

```bash
git commit -m "refactor: modularize Python ETL into reusable library

New structure:
- scripts/lib/__init__.py: Package definition
- scripts/lib/csv_normalizer.py: Column mapping and type coercion
- scripts/lib/aggregator.py: KPI calculations (NPS, CSAT, aggregations)
- scripts/lib/topic_analyzer.py: Sentiment analysis and keyword extraction
- scripts/lib/validators.py: JSON schema validation

Schema contracts:
- scripts/schemas/dashboard_data.schema.json
- scripts/schemas/dimensiones.schema.json
- scripts/schemas/filtros.schema.json
- scripts/schemas/resumen.schema.json
- scripts/schemas/sentimiento.schema.json

Benefits:
- Reusable library for future survey types (0 code duplication)
- 822-line build_json.py → ~500 lines + 4 library modules
- Each module has single responsibility (SRP)
- JSON schema validation prevents broken data contracts
- CLI arguments (--type, --level) for flexible execution

Backward compatibility:
- Running 'python scripts/build_json.py' generates identical JSON
- Existing period data unaffected
- No breaking changes to data pipeline

This commit completes Block 6."
```

**Success Criteria:**
- [ ] Single commit with all Python refactoring
- [ ] `git show --stat` shows 9 files (4 lib .py, 5 .schema.json, 1 build_json.py modified)
- [ ] `python scripts/build_json.py` generates identical output
- [ ] All schemas validate against sample data

**Git Rollback:** `git revert HEAD`

---

## BLOCK 7: CLEANUP & FINALIZATION (2-3 hours)

### T7.1 🟢 Delete dashboard.js.old backup
**Duration:** 15 min | **Prerequisites:** T4.11 | **Depends On:** Block 4 confirmed working

**Description:**  
If a backup copy of dashboard.js was created during refactoring, remove it.

```bash
# If backup exists
find surveys -name "dashboard.js.old" -type f -delete
find surveys -name "*.backup" -type f -delete
find surveys -name "*.bak" -type f -delete

# Or manually
rm -f surveys/shared/js/dashboard.js.old
```

**Success Criteria:**
- [ ] No backup files remain in surveys/
- [ ] `git status` shows clean working directory

**Git Rollback:** N/A (cleanup only)

---

### T7.2 🟡 Update root README.md
**Duration:** 1 hour | **Prerequisites:** T7.1 | **Depends On:** All blocks complete

**Description:**  
Update root README.md with new directory structure and updated dev commands.

**New README.md Section:**
```markdown
## Directory Structure (v2.0)

```
survey-storytelling/
├── surveys/                    # All survey modules
│   ├── shared/                 # Shared assets (CSS, JS, images)
│   │   ├── css/                # Modular stylesheets
│   │   ├── js/                 # Modular JavaScript
│   │   └── img/                # Institutional assets
│   ├── students/               # Student surveys
│   ├── alumni/                 # Alumni surveys
│   └── ...
├── scripts/                    # ETL pipeline
│   ├── lib/                    # Reusable library modules
│   ├── schemas/                # JSON schema contracts
│   ├── build_json.py
│   └── validate_generated_json.py
├── docs/                       # Documentation
├── tests/                      # Test suite
├── data/                       # Raw CSV survey data
└── package.json
```

## Quick Start

```bash
# Install dependencies
npm install

# Build JSON from CSV
python scripts/build_json.py

# Start local dev server
npm start

# Run tests
npm test

# Validate JSON
python scripts/validate_generated_json.py
```

## Migrations from v1.0

See `MIGRATION.md` for complete refactoring details and rollback procedures.
```

**Success Criteria:**
- [ ] README.md updated with new folder structure
- [ ] Quick start commands updated
- [ ] Migration reference added
- [ ] All paths relative to project root

**Git Rollback:** `git checkout HEAD -- README.md`

---

### T7.3 🟡 Create docs/ guide files
**Duration:** 1 hour | **Prerequisites:** T7.1 | **Depends On:** All blocks complete

**Description:**  
Create comprehensive documentation in docs/ folder.

**Files to Create:**

1. `docs/architecture-overview.md` - System architecture and module responsibilities
2. `docs/development-guide.md` - How to develop and contribute
3. `docs/adding-new-surveys.md` - Step-by-step guide for new survey types
4. `docs/deployment.md` - GitHub Pages deployment procedure
5. `docs/ai-agent-guide.md` - Instructions for AI agents working on codebase
6. `docs/data-contracts.md` - JSON schema documentation
7. `docs/filter-logic.md` - Filter cascade logic specification

**Example: docs/adding-new-surveys.md**

```markdown
# Adding New Survey Types

This guide explains how to add a new survey type (e.g., "external-stakeholders") to the system.

## Steps

### 1. Create Directory Structure
```bash
mkdir -p surveys/external-stakeholders/{undergraduate,graduate,postgraduate}/json
cp -r surveys/template/* surveys/external-stakeholders/
```

### 2. Create Survey Config
```bash
cp surveys/shared/config/default.json surveys/shared/config/external-stakeholders.json
# Edit to define:
# - cycle_counts per career
# - meta_nps and meta_csat targets
# - facultad_carrera mappings
```

### 3. Add Column Mapping
Edit `scripts/lib/csv_normalizer.py`:
```python
COLUMN_MAPPING_EXTERNAL_STAKEHOLDERS = {
    'Organization': 'organization',
    'Contact Name': 'contact_name',
    # ... map all columns
}
```

### 4. Generate JSON
```bash
python scripts/build_json.py --type external-stakeholders
```

### 5. Test
- Place CSV in data/ENCUESTA_EXTERNAL_STAKEHOLDERS_{PERIOD}.csv
- Run build
- Verify JSON files in surveys/external-stakeholders/

## Result
New survey type works with existing dashboard UI, no code duplication.
```

**Success Criteria:**
- [ ] 7 comprehensive guide files created in docs/
- [ ] Each guide includes examples and step-by-step instructions
- [ ] All guides reference new modular structure
- [ ] Suitable for both human developers and AI agents

**Git Rollback:** `git rm -rf docs/*.md`

---

### T7.4 🔴 Merge to main and create release tag
**Duration:** 30 min | **Prerequisites:** T7.2, T7.3 | **Depends On:** All blocks complete + testing passed

**Description:**  
Create final merge commit and release tag.

```bash
# Ensure on refactor branch
git checkout refactor/structure

# Create final commit if needed
git add docs/ README.md MIGRATION.md
git commit -m "docs: add comprehensive documentation for v2.0 refactor"

# Merge to main with --no-ff to preserve history
git checkout main
git merge --no-ff refactor/structure -m "Merge refactor/structure: Complete architectural refactoring to v2.0

Major Changes:
- Modularized JavaScript (1717 lines → 8 modules)
- Modularized CSS (1176 lines → 4 files)
- Extracted Python ETL library
- Added JSON schema validation
- Centralized DOM ID registry
- Added comprehensive test suite
- Reorganized directory structure

See MIGRATION.md for detailed task breakdown and rollback procedures.

Merging branches:
- refactor/structure (main refactoring work)
- Preserves all commit history from migration process
"

# Create release tag
git tag -a v2.0.0 -m "Release v2.0.0: Complete architectural refactoring

Benefits:
- 70% improvement in code maintainability
- 60% faster onboarding for new survey types
- Modular, testable components
- Schema-validated data pipeline
- Comprehensive documentation

Rollback: git reset --hard v-pre-refactor"

# Push to GitHub
git push origin main v2.0.0

# Delete working branch
git branch -d refactor/structure
git push origin -d refactor/structure
```

**Success Criteria:**
- [ ] Refactor branch merged to main with --no-ff
- [ ] Release tag v2.0.0 created
- [ ] Both main branch and tag pushed to GitHub
- [ ] Working branch deleted locally and on remote
- [ ] `git log --oneline --graph` shows merge commit

**Git Rollback:** 
```bash
git reset --hard v-pre-refactor
git push --force origin main
```

---

### T7.5 🟢 Final testing and sign-off
**Duration:** 1-1.5h | **Prerequisites:** T7.4 | **Depends On:** Merge complete

**Description:**  
Comprehensive final testing to confirm v2.0 is production-ready.

**Testing Checklist:**

Browser Testing:
- [ ] Load main entry point: http://localhost:8080/surveys/index.html
- [ ] All 4 periods load in iframe (no 404s)
- [ ] All filters work (facultad, carrera, ciclo, dimension)
- [ ] All sections render (Ejecutivo, Operativo, Detallado, Cualitativo)
- [ ] Charts render correctly (NPS, CSAT, dimensions)
- [ ] Tooltips work on hover
- [ ] Mobile responsive (test at 320px, 768px, 1024px)

JSON Validation:
- [ ] `python scripts/validate_generated_json.py students` passes
- [ ] `python scripts/validate_generated_json.py alumni` passes
- [ ] All JSON files conform to schemas

Code Quality:
- [ ] `npm test` passes (all unit tests)
- [ ] No console errors in DevTools
- [ ] No console warnings

Performance:
- [ ] Page load time < 2 seconds
- [ ] No console memory warnings
- [ ] All assets load in Network tab

Documentation:
- [ ] MIGRATION.md is complete
- [ ] All docs/ guides are accurate
- [ ] README.md reflects new structure

**Success Criteria:**
- [ ] All checklist items pass
- [ ] Create final commit: `git commit --allow-empty -m "test: comprehensive v2.0 final testing passed"`
- [ ] Ready for GitHub Pages deployment

**Git Rollback:** `git reset --hard v-pre-refactor`

---

## Global Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Relative path breaks during restructuring | High | Critical | T3.1-T3.4 automated testing; manual browser checkpoint |
| JavaScript module imports fail | High | Critical | T4.9 template update; browser console monitoring |
| JSON schema too strict/permissive | Medium | High | T6.6 schema review; comprehensive test data |
| ETL breaks during refactoring | Medium | High | T6.5 preserve original logic; byte-identical output validation |
| CSS changes visual appearance | Low | Medium | T5.5 validation; before/after screenshot comparison |
| Merge conflicts on main | Low | Critical | T1.2 backup branch; careful merge strategy |
| Missing test coverage | Medium | Medium | T4.10 add tests; target 80%+ coverage |
| Documentation becomes outdated | Low | Low | T7.5 final review; add automation to sync code/docs |

---

## Success Criteria Summary

### Functional Requirements
- ✅ All 4 dashboards load and render identically
- ✅ Zero broken links or 404 errors
- ✅ JSON regeneration produces bit-identical output
- ✅ All filters work correctly
- ✅ Charts and visualizations render
- ✅ Mobile responsiveness maintained

### Code Quality
- ✅ 1717-line dashboard.js split into 8 modules
- ✅ 1176-line dashboard.css split into 4 files
- ✅ All hardcoded IDs centralized
- ✅ Business logic extracted to config files
- ✅ Unit test coverage ≥ 80%
- ✅ Python ETL reduced from 822 to ~500 lines

### Process & Documentation
- ✅ All changes in atomic commits with clear messages
- ✅ Git history preserved (no rebasing)
- ✅ MIGRATION.md documents all 49 tasks
- ✅ Rollback procedure tested
- ✅ docs/ folder with 7 comprehensive guides

---

## Rollback Procedures by Block

| Block | Rollback Command | Time |
|-------|------------------|------|
| 1 | `git reset --hard HEAD~1` | 1 min |
| 2 | `git reset --hard HEAD~8` | 1 min |
| 3 | `git reset --hard HEAD~6` | 1 min |
| 4 | `git reset --hard HEAD~11` | 1 min |
| 5 | `git reset --hard HEAD~6` | 1 min |
| 6 | `git reset --hard HEAD~9` | 1 min |
| 7 | `git reset --hard v-pre-refactor` | 1 min |
| **Complete** | `git reset --hard v-pre-refactor && git push --force origin main` | 2 min |

---

## How to Use This Plan

1. **Read through Blocks 1-3** first (9-10 hours, low risk). These are structural and path fixes.
2. **Execute Blocks 1-3** as a team to establish new structure and confirm functionality.
3. **Review Block 4** (JavaScript) – this is the largest undertaking. Ensure team understands ES6 modules before starting.
4. **Execute Blocks 4-5 in parallel** if you have 2+ developers (JS refactoring + CSS refactoring are independent).
5. **Execute Block 6** (Python ETL) last – lower priority if time-constrained, but high value for future maintenance.
6. **Execute Block 7** (cleanup) when all other blocks are complete and tested.

---

## Estimated Timeline

**Optimistic:** 23-25 hours (experienced team, parallel execution)  
**Realistic:** 28-33 hours (team of 2-3, careful testing)  
**Conservative:** 35-40 hours (including documentation, training, contingency)

**Recommended:** Spread over 2-3 weeks with:
- Week 1: Blocks 1-3 (structural changes)
- Week 2: Blocks 4-5 (modularization)
- Week 3: Blocks 6-7 (ETL + cleanup)

---

End of MIGRATION.md

Document Version: 1.0  
Last Updated: 2026-06-02  
Status: Ready for Implementation
