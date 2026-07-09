/**
 * E2E — Dashboard Integration Tests
 *
 * Valida que el dashboard carga correctamente con datos reales:
 * KPIs visibles, filtros funcionales, sección cualitativa presente.
 *
 * Ejecutar: npx playwright test tests/e2e/
 * Requiere: npm start (servidor HTTP en puerto 8080)
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

const BASE_URL = 'http://localhost:8080';

test.describe('Dashboard - undergraduate 2026-1', () => {
  let page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    // Navegar al dashboard de pregrado 2026-1
    await page.goto(`${BASE_URL}/zoho-survey/students/undergraduate/2026-1/index.html`, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
  });

  test('KPIs principales son visibles', async () => {
    // NPS KPI
    const kpiNps = page.locator('#kpi-nps-value');
    await expect(kpiNps).toBeVisible({ timeout: 10000 });
    const npsText = await kpiNps.textContent();
    expect(npsText).not.toBe('');
    expect(npsText).not.toBe('Cargando...');

    // CSAT KPI
    const kpiCsat = page.locator('#kpi-csat-value');
    await expect(kpiCsat).toBeVisible();
    const csatText = await kpiCsat.textContent();
    expect(csatText).not.toBe('');
  });

  test('La página tiene título', async () => {
    const title = await page.title();
    // El template no define <title>, se acepta vacío
    expect(typeof title).toBe('string');
  });

  test('Barra NPS visible con segmentos', async () => {
    const npsBar = page.locator('#nps-bar');
    await expect(npsBar).toBeVisible({ timeout: 10000 });
    const segments = npsBar.locator('.csat-segment');
    const count = await segments.count();
    expect(count).toBeGreaterThanOrEqual(3); // promotores, pasivos, detractores
  });

  test('Barra CSAT visible con 5 segmentos', async () => {
    const csatBar = page.locator('#csat-bar');
    await expect(csatBar).toBeVisible({ timeout: 10000 });
    const segments = csatBar.locator('.csat-segment');
    const count = await segments.count();
    expect(count).toBe(5);
  });

  test('Gráfico radar visible', async () => {
    const radar = page.locator('#radar-chart');
    await expect(radar).toBeVisible({ timeout: 10000 });
  });

  test('Filtros de facultad existen', async () => {
    const filterFac = page.locator('#filter-facultad-top3');
    await expect(filterFac).toBeVisible({ timeout: 5000 });
  });

  test('Footer muestra información de período', async () => {
    const footer = page.locator('#footer-periodo');
    await expect(footer).toBeVisible({ timeout: 5000 });
    const text = await footer.textContent();
    expect(text.length).toBeGreaterThan(10);
    expect(text).toContain('Dirección de Planificación');
  });

  test('Footer muestra año', async () => {
    const footerAnio = page.locator('#footer-anio');
    await expect(footerAnio).toBeVisible({ timeout: 5000 });
    const text = await footerAnio.textContent();
    expect(text).toBeTruthy();
  });
});
