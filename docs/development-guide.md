# Development Guide

**Version:** 2.0  
**Status:** Production-ready  
**Target Audience:** Full-stack developers, Python developers, frontend engineers, AI agents

---

## Getting Started

### Prerequisites

- **Node.js** ≥ 18.0.0
- **Python** 3.8+
- **Git**
- A text editor (VS Code recommended)

### First-Time Setup

```bash
# Clone the repository
git clone https://github.com/Universidad-de-Lima/survey-storytelling.git
cd survey-storytelling

# Install dependencies
npm install

# Create virtual environment for Python (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install pandas jsonschema

# Start local development server
npm start

# In browser: http://localhost:8080
```

---

## Development Workflow

### Scenario: Fixing a Bug in the Dashboard

**Example:** "Filters aren't cascading correctly from facultad to carrera"

#### Step 1: Identify the Issue
- Likely location: `surveys/shared/js/filter-engine.js`
- Method: `setFacultad()` or `getAvailableCarreras()`

#### Step 2: Create a Feature Branch
```bash
git checkout -b fix/facultad-carrera-cascade
```

#### Step 3: Make Changes
```javascript
// surveys/shared/js/filter-engine.js
setFacultad(facultad) {
  this.state.facultad = facultad;
  this.state.carrera = null;  // Reset carrera
  
  const available = this.getAvailableCarreras();
  console.log(`Availble carreras for ${facultad}:`, available);
  
  return available;  // Return for testing
}
```

#### Step 4: Test in Browser
```bash
npm start
# Navigate to http://localhost:8080
# Open DevTools (F12)
# Select facultad → check console output
# Verify carrera options update
```

#### Step 5: Run Unit Tests
```bash
npm test

# Or test specific module:
npm test -- test_math.test.js
```

#### Step 6: Commit & Push
```bash
git add surveys/shared/js/filter-engine.js
git commit -m "fix: facultad-carrera cascade now updates available options

- setFacultad() now resets carrera before fetching available options
- getAvailableCarreras() correctly returns options from facultad_carrera mapping
- Tested in browser: filter cascade works for all 3 faculties"

git push origin fix/facultad-carrera-cascade
```

#### Step 7: Create Pull Request
- Go to GitHub
- Create PR from `fix/facultad-carrera-cascade` → `main`
- Reference issue (e.g., "Fixes #42")
- Wait for CI/CD to pass

---

### Scenario: Adding a New Survey Type

**Example:** "Add 'External Stakeholders' survey"

#### Step 1: Create Directory Structure
```bash
mkdir -p surveys/external-stakeholders/{2026}/json
mkdir -p data/

# Copy template
cp surveys/shared/template/index.html surveys/external-stakeholders/2026/index.html
```

#### Step 2: Update CSV Normalizer
```python
# scripts/lib/csv_normalizer.py

COLUMN_MAPPING_EXTERNAL_STAKEHOLDERS = {
    'Organization': 'organizacion',
    'Contact Name': 'nombre_contacto',
    'Overall Satisfaction': 'satisfaccion_general',
    'Recommendation Score': 'nps_score',
    'Comments': 'comentarios',
    # ... map all columns from your CSV
}

def get_column_mapping(survey_type):
    mappings = {
        'students': COLUMN_MAPPING_STUDENTS,
        'alumni': COLUMN_MAPPING_ALUMNI,
        'external_stakeholders': COLUMN_MAPPING_EXTERNAL_STAKEHOLDERS,  # Add this
    }
    return mappings.get(survey_type, {})
```

#### Step 3: Add Survey Config
```json
// surveys/shared/config/external-stakeholders.json
{
  "type": "external_stakeholders",
  "levels": ["2026"],
  "has_ciclo": false,
  "facultades": [],
  "facultad_carrera": {},
  "meta_nps": 50,
  "meta_csat": 93,
  "dimensions": [
    "Calidad del servicio",
    "Responsividad",
    "Profesionalismo"
  ]
}
```

#### Step 4: Place CSV File
```bash
# Place your CSV in data/ directory with naming convention:
# ENCUESTA_EXTERNAL_STAKEHOLDERS_{PERIOD}.csv

cp my_data.csv "data/ENCUESTA_EXTERNAL_STAKEHOLDERS_2026.csv"
```

#### Step 5: Generate JSON
```bash
# From project root
python scripts/build_json.py --type external_stakeholders --level 2026
```

#### Step 6: Test Dashboard
```bash
npm start
# Navigate to http://localhost:8080/surveys/external-stakeholders/index.html
# Verify period loads and data displays correctly
```

#### Step 7: Commit
```bash
git add surveys/external-stakeholders/ scripts/lib/csv_normalizer.py \
         surveys/shared/config/external-stakeholders.json
git commit -m "feat: add External Stakeholders survey type

- Created surveys/external-stakeholders/ module
- Added COLUMN_MAPPING_EXTERNAL_STAKEHOLDERS
- Added external-stakeholders.json config
- Generated 2026 period data
- Tested dashboard loads without errors"

git push origin feature/external-stakeholders
```

---

## Code Style Guidelines

### JavaScript

**Module structure:**
```javascript
// Always use ES6 modules
import { something } from './utils/formatters.js';
import { ClassA } from './classes.js';

// Export at end of file
export { functionA, ClassA };

// Arrow functions for callbacks
const handleClick = (event) => {
  console.log(event);
};

// Async/await for promises
async function loadData() {
  try {
    const data = await fetch('./data.json');
    return data.json();
  } catch (error) {
    console.error('Failed to load:', error);
  }
}
```

**Naming conventions:**
- `const MY_CONSTANT = 123;` — SCREAMING_SNAKE_CASE for constants
- `const myVariable = 'value';` — camelCase for variables
- `function myFunction() {}` — camelCase for functions
- `class MyClass {}` — PascalCase for classes

**No comments needed for:**
```javascript
// ❌ DON'T: This explains WHAT, not WHY
const nps = ((p - d) / total) * 100;  // Calculate NPS

// ✅ DO: Omit if code is clear
const nps = calculateNPS(promoters, detractors, total);

// ✅ DO: Comment only WHY if non-obvious
// NPS score for careers with 12 cycles gets +5 weight bonus per university policy
const adjustedNps = nps + (carreras12Ciclos.includes(carrera) ? 5 : 0);
```

### Python

```python
"""Module docstring at top of file."""

def calculate_nps(promoters: int, detractors: int, total: int) -> float:
    """
    Calculate Net Promoter Score.
    
    Args:
        promoters: Count of promoter responses
        detractors: Count of detractor responses
        total: Total responses
    
    Returns:
        NPS score (-100 to 100)
    """
    if total == 0:
        return 0
    return round(((promoters - detractors) / total) * 100, 2)

# Type hints for clarity
survey_data: dict[str, any] = load_csv('data.csv')

# Snake_case for variables/functions
my_variable_name = 123
def my_function_name(): pass

# SCREAMING_SNAKE_CASE for constants
MAX_CICLOS = 12
SENTIMENT_KEYWORDS = {...}
```

### CSS

```css
/* Use design tokens for all values */
.kpi-card {
  padding: var(--space-lg);
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

/* Don't hardcode colors, use tokens */
.section-header {
  color: var(--ulima-orange);  /* ✅ Good */
  /* color: #ff5117;  ❌ Avoid hardcoding */
}

/* kebab-case for class names */
.section-header, .kpi-card, .filter-select { }
/* Not: .sectionHeader, .kpiCard */
```

---

## Testing

### Unit Tests (JavaScript)

Run tests:
```bash
npm test

# Or with watch mode:
npm test -- --watch
```

Write tests:
```javascript
// tests/unit/test_math.test.js
import { describe, it, expect } from 'vitest';
import { calculateNPS } from '../../surveys/shared/js/utils/math.js';

describe('Math Utilities', () => {
  describe('calculateNPS', () => {
    it('calculates correct NPS for standard inputs', () => {
      const nps = calculateNPS(80, 20, 100);  // 80 promoters, 20 detractors, 100 total
      expect(nps).toBe(60);
    });
    
    it('returns 0 for zero total', () => {
      expect(calculateNPS(0, 0, 0)).toBe(0);
    });
  });
});
```

### Manual Testing Checklist

After any changes, verify:
- [ ] All 4 dashboards load
- [ ] Filters work (facultad, carrera, ciclo, dimension)
- [ ] Charts render correctly
- [ ] Mobile responsive (test at 320px, 768px, 1024px)
- [ ] No console errors (F12 → Console tab)
- [ ] No 404s in Network tab
- [ ] Tooltips work on hover

---

## Debugging

### JavaScript Debugging

```javascript
// 1. Use console for quick checks
console.log('Filter state:', filterEngine.getState());

// 2. Use debugger keyword to pause execution
function renderChart() {
  debugger;  // Execution stops here when DevTools open
  const data = prepareChartData();
  renderSVG(data);
}

// 3. Inspect DOM elements
const element = document.getElementById('kpi-nps');
console.log('Element:', element);
console.log('Classes:', element.className);
console.log('Content:', element.textContent);
```

### Python Debugging

```python
# 1. Print debug info
print(f'Processing {len(df)} rows')
print(f'Column names: {df.columns.tolist()}')

# 2. Use pdb debugger
import pdb

def process_survey():
    data = load_csv('data.csv')
    pdb.set_trace()  # Execution stops here
    # ... rest of code
    
# Run: python scripts/build_json.py

# 3. Inspect dataframe
print(df.head())  # First 5 rows
print(df.info())  # Column types
print(df.describe())  # Statistics
```

### Network Debugging

Open DevTools (F12) → Network tab:
- Check all CSS/JS/JSON files load (Status 200)
- Check load times for each file
- If 404: Update relative path in HTML or fix JSON file location

---

## Performance Optimization

### Frontend

```javascript
// ❌ Bad: Fetches data every render
function render() {
  const data = await fetch('./data.json');  // Fetches every time!
  // render...
}

// ✅ Good: Cache data
const data = await loadDashboardData();  // Once at startup
function render() {
  // Use cached data
}

// ❌ Bad: DOM queries in loop
for (let i = 0; i < 100; i++) {
  document.getElementById('item-' + i).textContent = data[i];  // 100 DOM queries
}

// ✅ Good: Batch DOM updates
const html = data.map((item, i) => `<div id="item-${i}">${item}</div>`).join('');
document.getElementById('container').innerHTML = html;
```

### Backend

```python
# ❌ Bad: Calculates same thing repeatedly
for row in df.iterrows():
    nps = calculate_nps(row.promoters, row.detractors, row.total)  # Recalculates

# ✅ Good: Vectorized operations
df['nps'] = (df.promoters - df.detractors) / df.total * 100

# ❌ Bad: Loops with string concatenation
result = ''
for item in items:
    result += '<div>' + item + '</div>'  # Creates new string each iteration

# ✅ Good: Use join()
result = ''.join(f'<div>{item}</div>' for item in items)
```

---

## Troubleshooting

### Problem: "Dashboard loads but no data shows"

**Check:**
1. Open DevTools (F12) → Console tab
2. Look for red error messages (e.g., "Failed to load ./json/dashboard_data.json")
3. Check Network tab → look for 404s
4. Verify JSON files exist in `surveys/{type}/{period}/json/`

**Solution:**
```bash
# Regenerate JSON files
python scripts/build_json.py

# Or for specific type:
python scripts/build_json.py --type students --level graduate
```

### Problem: "Filters don't update available options"

**Check:**
1. Open DevTools → Console
2. Click filter → check for errors
3. Inspect filter state: `console.log(window.filterEngine.getState())`

**Solution:**
- Check `filter-engine.js` cascade logic
- Verify `filtros.json` has correct `facultad_carrera` mapping
- Run tests: `npm test -- test_math.test.js`

### Problem: "CSS not loading or styles broken"

**Check:**
1. DevTools → Network tab → look for 404 on CSS files
2. Check relative path in HTML (should be `../../../shared/css/`)
3. DevTools → Console → check for CSS parse errors

**Solution:**
```bash
# Rebuild CSS (if using preprocessor)
npm run build:css

# Or manually check relative path
# cd surveys/students/graduate/2026/
# Check if ../../../shared/css/dashboard.css resolves correctly
```

### Problem: "JSON validation fails"

**Check:**
```bash
python scripts/validate_generated_json.py students

# Check specific file:
python scripts/lib/validators.py
```

**Solution:**
- Check `scripts/schemas/` for schema definition
- Compare generated JSON against schema requirements
- Fix data in `build_json.py` if schema is correct

---

## Deployment

### Development
```bash
npm start
# http://localhost:8080
```

### Staging (before release)
```bash
# Build all JSON files
python scripts/build_json.py

# Run all tests
npm test

# Run JSON validation
python scripts/validate_generated_json.py students
python scripts/validate_generated_json.py alumni
```

### Production (GitHub Pages)
Automatically deployed via `.github/workflows/build-and-deploy.yml` on push to main:

```yaml
# .github/workflows/build-and-deploy.yml
- name: Build JSON
  run: python scripts/build_json.py

- name: Validate JSON
  run: python scripts/validate_generated_json.py students

- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./
```

---

## Common Tasks

### Add a New CSS Component

1. Create in `surveys/shared/css/components.css`:
```css
.my-component {
  padding: var(--space-md);
  background: var(--gray-50);
  border-radius: var(--radius-md);
}
```

2. Use in `surveys/shared/template/index.html`:
```html
<div class="my-component">Content</div>
```

### Add a New Calculation Function

1. Create in `surveys/shared/js/utils/math.js`:
```javascript
function myCalculation(input1, input2) {
  return input1 + input2;
}

export { myCalculation };
```

2. Use in any module:
```javascript
import { myCalculation } from './utils/math.js';

const result = myCalculation(5, 10);
```

### Add a New API Endpoint (Future)

When moving from static to dynamic:
1. Create backend endpoint in your API
2. Update `surveys/shared/js/data-loader.js` to fetch from API instead of local JSON
3. Keep JSON fallback for offline support

---

## Getting Help

- **Architecture Questions:** See `docs/architecture-overview.md`
- **Adding New Features:** See `docs/adding-new-surveys.md`
- **Data Contracts:** See `docs/data-contracts.md`
- **Filter Logic:** See `docs/filter-logic.md`
- **AI Agents:** See `docs/ai-agent-guide.md`

---

See `MIGRATION.md` for architectural changes in v2.0.
