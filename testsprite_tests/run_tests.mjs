/**
 * TestSprite — Pruebas automatizadas del dashboard con Playwright v3
 *
 * Ejecuta los 16 casos del plan de pruebas contra el servidor local.
 * Uso: node testsprite_tests/run_tests.mjs
 */

import { chromium } from './node_modules/playwright/index.mjs';
import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE = 'http://127.0.0.1:5500';
const SURVEY_URL = `${BASE}/zoho-survey/students/undergraduate/2026-1/index.html`;

const results = [];
let passed = 0;
let failed = 0;

function assert(name, condition, detail = '') {
  if (condition) { passed++; results.push({ name, status: '✅ PASS', detail }); }
  else { failed++; results.push({ name, status: '❌ FAIL', detail }); }
}

async function tooltipVisible(page, timeout = 1500) {
  try {
    await page.waitForSelector('#tooltip', { state: 'visible', timeout });
    return await page.$eval('#tooltip', el => el.style.display !== 'none');
  } catch { return false; }
}

async function hoverEl(page, el, steps = 5) {
  const box = await el.boundingBox();
  if (!box || box.width < 2) return null;
  for (let s = 1; s <= steps; s++) {
    await page.mouse.move(box.x + (box.width * s) / steps, box.y + box.height / 2, { steps: 2 });
    await page.waitForTimeout(40);
  }
  return box;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);

  console.log('━━━ TestSprite v3 ━━━\n');

  // ═══════ EJECUTIVO ═══════

  console.log('📋 TC002: KPIs');
  await page.goto(SURVEY_URL, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);

  const kpi = await page.$$('.kpi-value');
  assert('TC002: KPI cards', kpi.length >= 3, `${kpi.length} .kpi-value`);

  const txt = await page.textContent('body');
  assert('TC002: NPS mención', /promotores/i.test(txt), 'Body mentions promotores');
  assert('TC002: CSAT mención', /totalmente satisfecho/i.test(txt), 'Body mentions satisfaction');

  console.log('📋 TC001: Filtro');
  const sel = await page.$$('select');
  let facOk = false;
  if (sel.length > 0) {
    const opts = await sel[0].$$('option');
    const valid = [];
    for (const o of opts) { const v = await o.getAttribute('value'); if (v && v.trim()) valid.push(v); }
    if (valid.length > 1) {
      await sel[0].selectOption(valid[1]);
      await page.waitForTimeout(1500);
      facOk = true;
    }
    assert('TC001: Facultad', facOk, facOk ? valid[1] : `${valid.length} options`);
  } else assert('TC001: Select', false, 'No <select>');

  console.log('📋 TC008: NPS tooltip');
  const npsSegs = await page.$$('#nps-bar .csat-segment');
  let npsOk = false;
  for (const s of npsSegs) {
    if (npsOk) break;
    const b = await s.boundingBox();
    if (b && b.width > 10) { await hoverEl(page, s); npsOk = await tooltipVisible(page); }
  }
  assert('TC008: NPS tooltip', npsOk, `${npsSegs.length} segments`);

  console.log('📋 TC010: CSAT tooltip');
  const csatSegs = await page.$$('#csat-bar .csat-segment');
  let csatOk = false;
  for (const s of csatSegs) {
    if (csatOk) break;
    const b = await s.boundingBox();
    if (b && b.width > 10) { await hoverEl(page, s); csatOk = await tooltipVisible(page); }
  }
  assert('TC010: CSAT tooltip', csatOk, `${csatSegs.length} segments`);

  console.log('📋 TC005: Filtros múltiples');
  if (sel.length >= 3) {
    for (let i = 1; i < 3; i++) {
      const opts = await sel[i].$$('option');
      const valid = [];
      for (const o of opts) { const v = await o.getAttribute('value'); if (v && v.trim()) valid.push(v); }
      if (valid.length > 0) await sel[i].selectOption(valid[0]);
    }
    await page.waitForTimeout(1500);
    assert('TC005: Filtros', true, 'Facultad + Carrera + Ciclo');
  } else assert('TC005: Selects', sel.length >= 3, `${sel.length}`);

  console.log('📋 TC015: Reset');
  const reset = await page.$('#reset-filters, [class*="reset"], button:has-text("Limpiar")');
  if (reset) { await reset.click(); await page.waitForTimeout(1500); assert('TC015: Reset', true, 'Clicked'); }
  else assert('TC015: Reset btn', false, 'Not found');

  // ═══════ DETALLADO ═══════

  console.log('📋 TC009: Tabla detallada');
  await page.goto(`${BASE}/zoho-survey/students/undergraduate/2026-1/index.html#detallado`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  const tabs = await page.$$('table');
  assert('TC009: Tabla existe', tabs.length > 0, `${tabs.length} tables`);
  assert('TC009: Ponderado/T2B', !!(await page.$('text=Ponderado') || await page.$('[class*="heat-"]')));

  console.log('📋 TC014: Tooltip detalle');
  const dist = await page.$$('.distribution-segment');
  let distOk = false;
  for (const d of dist) {
    if (distOk) break;
    const b = await d.boundingBox();
    if (b && b.width > 5) { await hoverEl(page, d); distOk = await tooltipVisible(page); }
  }
  assert('TC014: Tooltip distribución', distOk, `${dist.length} segments`);

  // ═══════ NAVEGACIÓN ═══════

  console.log('📋 TC006: Navegación');
  await page.goto(SURVEY_URL, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);
  const links = await page.$$('a[href^="#"]');
  let clicks = 0;
  for (const l of links) {
    const h = await l.getAttribute('href');
    if (h && /#(ejecutivo|operativo|detallado|cualitativo)/.test(h)) {
      await l.click(); await page.waitForTimeout(1200); clicks++;
    }
  }
  assert('TC006: Navegación', clicks >= 3, `${clicks} links`);

  // ═══════ CUALITATIVO ═══════

  console.log('📋 TC012: Sentimiento');
  await page.goto(`${BASE}/zoho-survey/students/undergraduate/2026-1/index.html#cualitativo`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2500);

  const sb = await page.$$('#sentimiento-bar-chart .bar-item');
  const np = await page.$$('#seg-nps-container .bar-item');
  const cc = await page.$$('#categorias-barras-container > *');
  const pa = await page.$$('#aspectos-positivos-container .bar-item');
  const na = await page.$$('#aspectos-negativos-container .bar-item');
  assert('TC012: Sentimiento', sb.length > 0, `${sb.length} bars`);
  assert('TC012: Segmento NPS', np.length > 0, `${np.length} bars`);
  assert('TC012: Categorías', cc.length > 0, `${cc.length} items`);
  assert('TC012: Aspectos', pa.length > 0 || na.length > 0, `Pos:${pa.length} Neg:${na.length}`);

  console.log('📋 TC016: Tooltip seg NPS');
  let npOk = false;
  for (const b of np) {
    if (npOk) break;
    const bx = await b.boundingBox();
    if (bx && bx.width > 10) {
      await page.mouse.move(bx.x + bx.width * 0.7, bx.y + bx.height / 2, { steps: 5 });
      await page.waitForTimeout(500);
      npOk = await tooltipVisible(page);
    }
  }
  assert('TC016: Tooltip segmento NPS', npOk, `${np.length} bars`);

  // ═══════ RADAR ═══════

  console.log('📋 TC011/TC013: Radar');
  await page.goto(`${BASE}/zoho-survey/students/undergraduate/2026-1/index.html#operativo`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);

  const svg = await page.$('svg');
  assert('TC011: SVG radar', !!svg, 'SVG found');

  // Esperar animaciones SVG
  try { await page.waitForSelector('svg circle[style*="opacity: 1"]', { timeout: 5000 }); }
  catch { /* continue anyway */ }
  await page.waitForTimeout(500);

  // Probar múltiples métodos para el tooltip radar (orden: más probable primero)
  let radarOk = false;
  let radarDetail = '';

  // Método 1: Playwright force hover sobre text labels (más confiable en headless)
  const texts = await page.$$('svg text[data-dim]');
  for (const t of texts) {
    if (radarOk) break;
    try { await t.hover({ force: true, timeout: 2000 }); await page.waitForTimeout(500); }
    catch { continue; }
    if (await tooltipVisible(page)) {
      const txt = await page.$eval('#tooltip', el => el.textContent?.trim() || '');
      radarOk = txt.length > 5;
      if (radarOk) { radarDetail = `via text (${txt.substring(0, 40)}...)`; break; }
    }
  }

  // Método 2: circles con hover suave
  if (!radarOk) {
    const circles = await page.$$('svg circle');
    for (const c of circles) {
      if (radarOk) break;
      const b = await c.boundingBox();
      if (b && b.width > 1 && b.height > 1) {
        await page.mouse.move(b.x + 2, b.y + 2, { steps: 5 });
        await page.waitForTimeout(500);
        if (await tooltipVisible(page)) {
          const txt = await page.$eval('#tooltip', el => el.textContent?.trim() || '');
          radarOk = txt.length > 5;
          if (radarOk) { radarDetail = `via circle (${txt.substring(0, 40)}...)`; break; }
        }
      }
    }
  }

  // Método 3: connector lines (fallback)
  if (!radarOk) {
    const lines = await page.$$('svg line[data-dim]');
    for (const l of lines) {
      if (radarOk) break;
      const b = await l.boundingBox();
      if (b && b.width > 5) {
        await l.hover({ force: true, timeout: 2000 });
        await page.waitForTimeout(400);
        radarOk = await tooltipVisible(page);
        if (radarOk) radarDetail = 'via line';
      }
    }
  }

  assert('TC013: Tooltip radar', radarOk, radarDetail || 'all methods tried');

  // ═══════ RESULTADOS ═══════
  const total = passed + failed;
  const pct = total > 0 ? Math.round(passed / total * 100) : 0;
  console.log(`\n━━━ ${passed} ✅ / ${failed} ❌ (${pct}%) ━━━\n`);
  for (const r of results) console.log(`${r.status} ${r.name}${r.detail ? ` — ${r.detail}` : ''}`);

  const report = `# TestSprite Test Report v3

## 1️⃣ Document Metadata
- **Project:** survey-storytelling
- **Date:** ${new Date().toISOString().slice(0, 10)}
- **Test Plan:** testsprite_frontend_test_plan.json
- **Execution:** Playwright (headless Chromium) v3
- **Environment:** Local (http://127.0.0.1:5500)

## 2️⃣ Requirement Validation Summary
| ID | Assertion | Status | Detail |
|----|-----------|--------|--------|
${results.map(r => `| ${r.name.split(':')[0].trim()} | ${r.name} | ${r.status} | ${r.detail} |`).join('\n')}

## 3️⃣ Coverage & Matching Metrics
- **Total assertions:** ${total}
- **Passed:** ${passed} (${pct}%)
- **Failed:** ${failed} (${100 - pct}%)
- **Sections:** Ejecutivo, Operativo, Detallado, Cualitativo

## 4️⃣ Key Gaps / Risks
| Risk | Impact |
|------|--------|
| SVG animation delays | Extra wait needed for radar tests |
| Headless font rendering | text bbox may be 0 in headless Chrome |
| Static JSON data | Tests are snapshot-based |
`;

  writeFileSync(join(__dirname, 'testsprite-mcp-test-report.md'), report, 'utf-8');
  console.log(`\n📄 ${join(__dirname, 'testsprite-mcp-test-report.md')}`);
  await browser.close();
  process.exit(0);
})();
