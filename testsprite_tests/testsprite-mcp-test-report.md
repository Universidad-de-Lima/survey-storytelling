# TestSprite Test Report v3

## 1️⃣ Document Metadata
- **Project:** survey-storytelling
- **Date:** 2026-07-06
- **Test Plan:** testsprite_frontend_test_plan.json
- **Execution:** Playwright (headless Chromium) v3
- **Environment:** Local (http://127.0.0.1:5500)

## 2️⃣ Requirement Validation Summary
| ID | Assertion | Status | Detail |
|----|-----------|--------|--------|
| TC002 | TC002: KPI cards | ✅ PASS | 15 .kpi-value |
| TC002 | TC002: NPS mención | ✅ PASS | Body mentions promotores |
| TC002 | TC002: CSAT mención | ✅ PASS | Body mentions satisfaction |
| TC001 | TC001: Facultad | ✅ PASS | Facultad de Arquitectura |
| TC008 | TC008: NPS tooltip | ✅ PASS | 3 segments |
| TC010 | TC010: CSAT tooltip | ✅ PASS | 5 segments |
| TC005 | TC005: Filtros | ✅ PASS | Facultad + Carrera + Ciclo |
| TC015 | TC015: Reset | ✅ PASS | Clicked |
| TC009 | TC009: Tabla existe | ✅ PASS | 6 tables |
| TC009 | TC009: Ponderado/T2B | ✅ PASS |  |
| TC014 | TC014: Tooltip distribución | ✅ PASS | 140 segments |
| TC006 | TC006: Navegación | ✅ PASS | 4 links |
| TC012 | TC012: Sentimiento | ✅ PASS | 3 bars |
| TC012 | TC012: Segmento NPS | ✅ PASS | 3 bars |
| TC012 | TC012: Categorías | ✅ PASS | 4 items |
| TC012 | TC012: Aspectos | ✅ PASS | Pos:5 Neg:5 |
| TC016 | TC016: Tooltip segmento NPS | ✅ PASS | 3 bars |
| TC011 | TC011: SVG radar | ✅ PASS | SVG found |
| TC013 | TC013: Tooltip radar | ✅ PASS | via text (Escala de SatisfacciónRespuestasT3BT2BPo...) |

## 3️⃣ Coverage & Matching Metrics
- **Total assertions:** 19
- **Passed:** 19 (100%)
- **Failed:** 0 (0%)
- **Sections:** Ejecutivo, Operativo, Detallado, Cualitativo

## 4️⃣ Key Gaps / Risks
| Risk | Impact |
|------|--------|
| SVG animation delays | Extra wait needed for radar tests |
| Headless font rendering | text bbox may be 0 in headless Chrome |
| Static JSON data | Tests are snapshot-based |
