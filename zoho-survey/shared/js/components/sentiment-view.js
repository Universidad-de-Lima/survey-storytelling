window.SurveySentimentView = (() => {
  'use strict';

  // Utils
  const $ = (id) => document.getElementById(id);
  const _fmt = window.SurveyFormatters;
  const _san = window.SurveySanitizer;

  let dataset = null;
  let cacheCarreras = [];
  let cacheSegmentos = [];
  let cacheCategorias = [];
  let cacheFragmentos = [];

  const COLORS = {
    pos: 'var(--gray-700)',
    neu: 'var(--gray-400)',
    neg: 'var(--ulima-orange)',
    prom: 'var(--gray-700)',
    pas: 'var(--gray-400)',
    det: 'var(--ulima-orange)'
  };

  async function loadData() {
    try {
      const response = await fetch('./data/dataset_cualitativo.json');
      if (!response.ok) {
        // Fallback a ./json por si la estructura de carpetas cambia
        const fallback = await fetch('./json/dataset_cualitativo.json');
        if (!fallback.ok) throw new Error('Network error');
        dataset = await fallback.json();
      } else {
        dataset = await response.json();
      }
      
      cacheCarreras = dataset.carreras || [];
      cacheSegmentos = dataset.segmentos || [];
      cacheCategorias = dataset.categorias || [];
      cacheFragmentos = dataset.fragmentos || [];

      initFilters();
      renderAll();
    } catch (error) {
      console.warn('Error loading dataset_cualitativo.json', error);
      const kpis = $('cualitativo-kpis');
      if (kpis) kpis.innerHTML = '<div style="color:var(--ulima-red);">No se pudo cargar el archivo dataset_cualitativo.json</div>';
    }
  }

  function initFilters() {
    const selCarrera = $('filter-carrera-cualitativo');
    const selSegmento = $('filter-segmento-cualitativo');
    const selSentimiento = $('filter-sentimiento-cualitativo');
    
    if (selCarrera) {
      selCarrera.innerHTML = '<option value="">Todas las carreras</option>' + 
        cacheCarreras.map(c => `<option value="${_san ? _san.escapeHTML(c.id) : c.id}">${_san ? _san.escapeHTML(c.id) : c.id}</option>`).join('');
      selCarrera.addEventListener('change', renderFiltered);
    }
    
    if (selSegmento) {
      selSegmento.innerHTML = '<option value="">Todos los segmentos</option>' + 
        ['Promotor', 'Pasivo', 'Detractor'].map(s => `<option value="${s}">${s}</option>`).join('');
      selSegmento.addEventListener('change', renderFiltered);
    }
    
    if (selSentimiento) {
      selSentimiento.innerHTML = '<option value="">Todos los sentimientos</option>' + 
        ['pos', 'neu', 'neg'].map(s => `<option value="${s}">${s === 'pos' ? 'Positivo' : s === 'neu' ? 'Neutro' : 'Negativo'}</option>`).join('');
      selSentimiento.addEventListener('change', renderFiltered);
    }
  }

  function renderFiltered() {
    renderAll();
  }

  function getActiveFilters() {
    return {
      carrera: $('filter-carrera-cualitativo')?.value || '',
      segmento: $('filter-segmento-cualitativo')?.value || '',
      sentimiento: $('filter-sentimiento-cualitativo')?.value || ''
    };
  }

  function formatInt(val) {
    return _fmt ? _fmt.formatInteger(val) : val;
  }
  
  function escapeHTML(str) {
    return _san ? _san.escapeHTML(str) : str;
  }

  function renderAll() {
    if (!dataset) return;
    const filters = getActiveFilters();
    
    // Filtro iterativo sobre fragmentos
    let frags = cacheFragmentos;
    if (filters.carrera || filters.segmento || filters.sentimiento) {
      frags = cacheFragmentos.filter(f => {
        if (filters.carrera && f.car !== filters.carrera) return false;
        if (filters.segmento && f.seg !== filters.segmento) return false;
        if (filters.sentimiento && f.sen !== filters.sentimiento) return false;
        return true;
      });
    }

    renderKPIs(frags, filters);
    renderSentimientosDist(frags);
    renderIdeasNps(frags);
    renderTopCategorias(frags);
    renderRankings(frags);
    renderCarrerasTabla(cacheCarreras, filters);
    renderIdeasDetalle(frags);
  }

  function renderKPIs(frags, filters) {
    const container = $('cualitativo-kpis');
    if (!container) return;

    let totIdeas = 0, totPos = 0, totNeg = 0, totNeu = 0, sumInt = 0;
    frags.forEach(f => {
      totIdeas++;
      if (f.sen === 'pos') totPos++;
      else if (f.sen === 'neg') totNeg++;
      else totNeu++;
      sumInt += (f.int || 0);
    });

    const intProm = totIdeas > 0 ? (sumInt / totIdeas).toFixed(2) : '0.00';
    const hasFilters = filters.carrera || filters.segmento || filters.sentimiento;

    if (!hasFilters && dataset.meta) {
      totIdeas = dataset.meta.fragmentos || totIdeas;
      totPos = dataset.meta.positivos || totPos;
      totNeg = dataset.meta.negativos || totNeg;
      totNeu = dataset.meta.neutros || totNeu;
    }

    container.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-value color-csat">${formatInt(totIdeas)}</div>
        <div class="kpi-label color-csat">Total Ideas</div>
        <div class="kpi-meta color-csat">Fragmentos analizados</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value color-csat">${formatInt(totPos)}</div>
        <div class="kpi-label color-csat">Ideas Positivas</div>
        <div class="kpi-meta color-csat">${totIdeas > 0 ? ((totPos/totIdeas)*100).toFixed(1) : 0}% del total</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value color-nps">${formatInt(totNeg)}</div>
        <div class="kpi-label color-nps">Ideas Negativas</div>
        <div class="kpi-meta color-nps">${totIdeas > 0 ? ((totNeg/totIdeas)*100).toFixed(1) : 0}% del total</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value color-emplea">${intProm}</div>
        <div class="kpi-label color-emplea">Intensidad Promedio</div>
        <div class="kpi-meta color-emplea">Escala 1 al 5</div>
      </div>
    `;
  }

  function renderSentimientosDist(frags) {
    const container = $('chart-sentimientos-dist');
    if (!container) return;

    let totPos = 0, totNeg = 0, totNeu = 0;
    frags.forEach(f => {
      if (f.sen === 'pos') totPos++;
      else if (f.sen === 'neg') totNeg++;
      else totNeu++;
    });
    const total = totPos + totNeg + totNeu;
    
    if (total === 0) {
      container.innerHTML = '<div>Sin datos</div>';
      return;
    }

    container.innerHTML = `
      <div class="csat-bar-row">
        ${totPos > 0 ? \`<div class="csat-segment" style="width:\${(totPos/total)*100}%; background:\${COLORS.pos};"><span class="csat-label">\${((totPos/total)*100).toFixed(1)}%</span></div>\` : ''}
        ${totNeu > 0 ? \`<div class="csat-segment" style="width:\${(totNeu/total)*100}%; background:\${COLORS.neu};"><span class="csat-label">\${((totNeu/total)*100).toFixed(1)}%</span></div>\` : ''}
        ${totNeg > 0 ? \`<div class="csat-segment" style="width:\${(totNeg/total)*100}%; background:\${COLORS.neg};"><span class="csat-label">\${((totNeg/total)*100).toFixed(1)}%</span></div>\` : ''}
      </div>
      <div class="legend" style="margin-top:12px;">
        <div class="legend-item"><div class="legend-dot" style="background:\${COLORS.pos};"></div>Positivos: \${totPos}</div>
        <div class="legend-item"><div class="legend-dot" style="background:\${COLORS.neu};"></div>Neutros: \${totNeu}</div>
        <div class="legend-item"><div class="legend-dot" style="background:\${COLORS.neg};"></div>Negativos: \${totNeg}</div>
      </div>
    `;
  }

  function renderIdeasNps(frags) {
    const container = $('chart-ideas-nps');
    if (!container) return;

    const npsMap = {
      'Promotor': { pos: 0, neu: 0, neg: 0, tot: 0 },
      'Pasivo': { pos: 0, neu: 0, neg: 0, tot: 0 },
      'Detractor': { pos: 0, neu: 0, neg: 0, tot: 0 }
    };

    frags.forEach(f => {
      const seg = f.seg;
      if (npsMap[seg] && f.sen) {
        npsMap[seg].tot++;
        if (npsMap[seg][f.sen] !== undefined) npsMap[seg][f.sen]++;
      }
    });

    let html = '';
    ['Promotor', 'Pasivo', 'Detractor'].forEach(seg => {
      const d = npsMap[seg];
      if (d.tot === 0) return;
      html += \`
        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="font-size:12px; font-weight:600;">\${seg} (\${d.tot} ideas)</div>
          <div class="csat-bar-row">
            \${d.pos > 0 ? \`<div class="csat-segment" style="width:\${(d.pos/d.tot)*100}%; background:\${COLORS.pos};"><span class="csat-label">\${d.pos}</span></div>\` : ''}
            \${d.neu > 0 ? \`<div class="csat-segment" style="width:\${(d.neu/d.tot)*100}%; background:\${COLORS.neu};"><span class="csat-label">\${d.neu}</span></div>\` : ''}
            \${d.neg > 0 ? \`<div class="csat-segment" style="width:\${(d.neg/d.tot)*100}%; background:\${COLORS.neg};"><span class="csat-label">\${d.neg}</span></div>\` : ''}
          </div>
        </div>
      \`;
    });
    
    if(!html) html = '<div>Sin datos</div>';
    container.innerHTML = html;
  }

  function renderTopCategorias(frags) {
    const container = $('chart-top-categorias');
    if (!container) return;

    const catMap = {};
    frags.forEach(f => {
      if (!f.cat) return;
      if (!catMap[f.cat]) catMap[f.cat] = { pos: 0, neu: 0, neg: 0, tot: 0 };
      catMap[f.cat].tot++;
      if (f.sen && catMap[f.cat][f.sen] !== undefined) catMap[f.cat][f.sen]++;
    });

    const cats = Object.entries(catMap)
      .map(([cat, d]) => ({ cat, ...d }))
      .sort((a, b) => b.tot - a.tot)
      .slice(0, 10);

    let html = '';
    cats.forEach(d => {
      html += \`
        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="font-size:12px; font-weight:600; display:flex; justify-content:space-between;">
            <span>\${escapeHTML(d.cat)}</span>
            <span>\${d.tot} ideas</span>
          </div>
          <div class="csat-bar-row">
            \${d.pos > 0 ? \`<div class="csat-segment" style="width:\${(d.pos/d.tot)*100}%; background:\${COLORS.pos};"></div>\` : ''}
            \${d.neu > 0 ? \`<div class="csat-segment" style="width:\${(d.neu/d.tot)*100}%; background:\${COLORS.neu};"></div>\` : ''}
            \${d.neg > 0 ? \`<div class="csat-segment" style="width:\${(d.neg/d.tot)*100}%; background:\${COLORS.neg};"></div>\` : ''}
          </div>
        </div>
      \`;
    });
    if(!html) html = '<div>Sin datos</div>';
    container.innerHTML = html;
  }

  function renderRankings(frags) {
    const cPos = $('ranking-positivos');
    const cNeg = $('ranking-negativos');
    if (!cPos || !cNeg) return;

    const catIntPos = {};
    const catIntNeg = {};

    frags.forEach(f => {
      if (!f.cat) return;
      if (f.sen === 'pos') {
        if (!catIntPos[f.cat]) catIntPos[f.cat] = { sum: 0, count: 0 };
        catIntPos[f.cat].sum += (f.int || 0);
        catIntPos[f.cat].count++;
      } else if (f.sen === 'neg') {
        if (!catIntNeg[f.cat]) catIntNeg[f.cat] = { sum: 0, count: 0 };
        catIntNeg[f.cat].sum += (f.int || 0);
        catIntNeg[f.cat].count++;
      }
    });

    const rankPos = Object.entries(catIntPos)
      .map(([cat, d]) => ({ cat, avg: d.sum / d.count }))
      .sort((a, b) => b.avg - a.avg)
      .slice(0, 5);

    const rankNeg = Object.entries(catIntNeg)
      .map(([cat, d]) => ({ cat, avg: d.sum / d.count }))
      .sort((a, b) => b.avg - a.avg)
      .slice(0, 5);

    cPos.innerHTML = \`<h5 style="font-size:12px; margin-bottom:8px;">Top Positivos</h5>\` +
      rankPos.map(d => \`<div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; border-bottom:1px solid var(--border); padding-bottom:4px;">
        <span style="color:\${COLORS.pos}; font-weight:600;">\${escapeHTML(d.cat)}</span>
        <span style="font-weight:700;">\${d.avg.toFixed(1)}</span>
      </div>\`).join('');

    cNeg.innerHTML = \`<h5 style="font-size:12px; margin-bottom:8px;">Top Negativos</h5>\` +
      rankNeg.map(d => \`<div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; border-bottom:1px solid var(--border); padding-bottom:4px;">
        <span style="color:\${COLORS.neg}; font-weight:600;">\${escapeHTML(d.cat)}</span>
        <span style="font-weight:700;">\${d.avg.toFixed(1)}</span>
      </div>\`).join('');
  }

  function renderCarrerasTabla(carreras, filters) {
    const tbody = $('tbody-carreras-cualitativo');
    if (!tbody) return;

    let displayCarreras = carreras;
    if (filters.carrera) {
      displayCarreras = carreras.filter(c => c.id === filters.carrera);
    }

    let html = '';
    displayCarreras.forEach(c => {
      const tot = (c.promotores || 0) + (c.pasivos || 0) + (c.detractores || 0);
      const pProm = tot > 0 ? ((c.promotores || 0)/tot)*100 : 0;
      const pPas = tot > 0 ? ((c.pasivos || 0)/tot)*100 : 0;
      const pDet = tot > 0 ? ((c.detractores || 0)/tot)*100 : 0;

      html += \`
        <tr>
          <td style="font-weight:600;">\${escapeHTML(c.id)}</td>
          <td class="text-center">\${formatInt(c.encuestados || 0)}</td>
          <td>
            <div class="csat-bar-row">
              \${pProm > 0 ? \`<div class="csat-segment" style="width:\${pProm}%; background:\${COLORS.prom};"><span class="csat-label">\${pProm.toFixed(1)}%</span></div>\` : ''}
              \${pPas > 0 ? \`<div class="csat-segment" style="width:\${pPas}%; background:\${COLORS.pas};"><span class="csat-label">\${pPas.toFixed(1)}%</span></div>\` : ''}
              \${pDet > 0 ? \`<div class="csat-segment" style="width:\${pDet}%; background:\${COLORS.det};"><span class="csat-label">\${pDet.toFixed(1)}%</span></div>\` : ''}
            </div>
          </td>
        </tr>
      \`;
    });
    tbody.innerHTML = html;
  }

  function renderIdeasDetalle(frags) {
    const tbody = $('tbody-ideas-detalle');
    if (!tbody) return;

    let html = '';
    const displayFrags = frags.slice(0, 50);

    displayFrags.forEach(f => {
      const senColor = f.sen === 'pos' ? COLORS.pos : f.sen === 'neg' ? COLORS.neg : COLORS.neu;
      const segColor = f.seg === 'Promotor' ? COLORS.prom : f.seg === 'Detractor' ? COLORS.det : COLORS.pas;
      
      html += \`
        <tr>
          <td>\${escapeHTML(f.car || '')}</td>
          <td class="text-center">\${escapeHTML(f.cic || '')}</td>
          <td class="text-center"><span style="color:\${segColor}; font-weight:600;">\${escapeHTML(f.seg || '')}</span></td>
          <td class="text-center"><span style="color:\${senColor}; font-weight:600;">\${f.sen === 'pos' ? 'Positivo' : f.sen === 'neg' ? 'Negativo' : 'Neutro'}</span></td>
          <td><span style="font-size:11px; background:var(--gray-200); padding:2px 6px; border-radius:4px; color:var(--gray-700);">\${escapeHTML(f.cat || '')}</span></td>
          <td style="font-size:13px;">\${escapeHTML(f.txt || '')}</td>
        </tr>
      \`;
    });
    
    if (frags.length > 50) {
      html += \`<tr><td colspan="6" class="text-center" style="color:var(--gray-500); padding:10px;">Mostrando las primeras 50 de \${frags.length} ideas. Utilice los filtros para ver más resultados.</td></tr>\`;
    } else if (frags.length === 0) {
      html += \`<tr><td colspan="6" class="text-center" style="color:var(--gray-500); padding:10px;">No se encontraron ideas con estos filtros.</td></tr>\`;
    }

    tbody.innerHTML = html;
  }

  // Auto-init on load
  document.addEventListener('DOMContentLoaded', loadData);

  return {
    init: loadData,
    renderAll
  };
})();
