/**
 * SURVEY SENTIMENT VIEW — Renderizador del análisis cualitativo y semántico.
 *
 * Muestra KPIs de comentarios, chips de temas semánticos principales,
 * tarjetas de insights cualitativos (insatisfacción/mejora/fortalezas) con frases reales,
 * y la tabla detallada de comentarios agrupados por carrera.
 *
 * Dependencias: SurveyFormatters, SurveyDOMHelpers, SurveySanitizer (globales)
 *
 * @module components/sentiment-view
 * @version 3.0.0
 */
window.SurveySentimentView = (() => {
  'use strict';

  const _fmt = window.SurveyFormatters;
  const _dh = window.SurveyDOMHelpers;
  const _san = window.SurveySanitizer;
  const _ttp = window.SurveyTooltip;

  const C = window.SURVEY_CONFIG || {};
  const PROGRAMA_ESTUDIOS_GENERALES = C.PROGRAMA_ESTUDIOS_GENERALES ?? 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = C.CICLOS_ESTUDIOS_GENERALES ?? ['1° Ciclo', '2° Ciclo'];

  const esEstudiosGen = (f) => f === PROGRAMA_ESTUDIOS_GENERALES;
  const $ = (id) => document.getElementById(id);

  // State for the Paginated Comment Explorador
  const state = {
    originalComments: [],
    filteredComments: [],
    currentPage: 0,
    pageSize: 10,
    showCorregido: true,
    sentimentCache: null
  };

  function colorPorTipo(tipo) {
    if (tipo === 'negativo') {
      return { border: 'var(--ulima-red)', bg: 'var(--sentiment-neg-bg, var(--danger-pastel))', label: 'Insatisfacción' };
    }
    if (tipo === 'positivo') {
      return { border: 'var(--success-text)', bg: 'var(--sentiment-pos-bg, var(--success-pastel))', label: 'Fortaleza reconocida' };
    }
    return { border: 'var(--ulima-orange)', bg: 'var(--sentiment-neu-bg, var(--warning-pastel))', label: 'Oportunidad de mejora' };
  }

  // Helper to create legend items with CSP-friendly event listeners
  function createLegendItem(colorVar, label, value, valLower) {
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.style.cursor = 'pointer';

    const dot = document.createElement('div');
    dot.className = 'legend-dot';
    dot.style.background = colorVar;

    div.appendChild(dot);
    const formattedValue = window.SurveyFormatters ? window.SurveyFormatters.formatInteger(value) : value.toLocaleString('en-US');
    div.appendChild(document.createTextNode(`${label}: ${formattedValue}`));

    div.addEventListener('click', () => {
      const select = $('explorador-sentimiento');
      if (select) {
        select.value = valLower;
        applyExploradorFilters();
        const explSec = $('tabla-explorador-comentarios');
        if (explSec) explSec.scrollIntoView({ behavior: 'smooth' });
      }
    });

    return div;
  }

  function drawSentimentBars(stats) {
    const container = $('sentimiento-bar-chart');
    if (!container) return;
    container.innerHTML = '';
    // Set fixed height to match Ideas por segmento NPS
    container.style.cssText = 'height: 180px; display: flex; flex-direction: column; justify-content: center;';

    const pos = stats.pos.total;
    const neu = stats.neu.total;
    const neg = stats.neg.total;
    const total = pos + neu + neg;
    if (total === 0) return;

    const data = [
      { label: 'Positivo', value: pos, color: 'var(--success-text)', breakdown: stats.pos },
      { label: 'Neutro', value: neu, color: 'var(--gray-400)', breakdown: stats.neu },
      { label: 'Negativo', value: neg, color: 'var(--ulima-red)', breakdown: stats.neg }
    ];

    const fragment = document.createDocumentFragment();
    data.forEach((item, index) => {
      if (item.value === 0) return;
      
      const pct = Math.round((item.value / total) * 100);
      const barValueOutside = pct < 12;

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label" style="width: 80px;">${item.label}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="width:${pct}%; background-color:${item.color}; animation-delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}" style="${barValueOutside ? 'color: var(--dark);' : 'color: white;'}">${_fmt.formatInteger(item.value)}</span>
          </div>
        </div>
      `;

      // Tooltip events
      barItem.addEventListener('mouseenter', (e) => {
        const b = item.breakdown;
        let html = `<strong>${item.label}</strong>: ${_fmt.formatInteger(item.value)} ideas (${pct}%)<br>`;
        html += `Promotores: ${_fmt.formatInteger(b.prom)}<br>`;
        html += `Pasivos: ${_fmt.formatInteger(b.pas)}<br>`;
        html += `Detractores: ${_fmt.formatInteger(b.det)}`;
        _ttp.show(e, html);
      });
      barItem.addEventListener('mousemove', (e) => {
        _ttp.move(e);
      });
      barItem.addEventListener('mouseleave', () => {
        _ttp.hide();
      });

      fragment.appendChild(barItem);
    });

    container.appendChild(fragment);
  }

  function renderMetricCards(comments, cache, totalRespuestasGlobal) {
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;
    
    // Sincronización global desde dashboard_data.json (para que cuadre matemáticamente con 4024)
    const totalGlobal = window.cache?.dashboard?.resumen?.encuestas || totalRespuestasGlobal || comments.length;
    const totalRespuestas = totalGlobal;
    
    let textAbierto = 0, ideas = 0, neg = 0, pos = 0, neu = 0, sumInt = 0;
    
    comments.forEach(c => {
      if (c.es_valido) {
        ideas++;
        if (c.sentimiento === 'positivo') pos++;
        else if (c.sentimiento === 'negativo') neg++;
        else neu++;
        sumInt += (c.intensidad || 0);
      }
    });

    const uniqueIds = new Set(comments.map(c => c.id_encuesta || c.comentario_id_original));
    textAbierto = uniqueIds.size;

    // Sincronización directa con el DOM del visual "Composición del Índice de Promotores Netos" (Ejecutivo)
    // Ya que window.cache es privado en dashboard.js, extraemos el valor exacto renderizado en la leyenda.
    let promotores = 0, pasivos = 0, detractores = 0;
    const npsLegend = document.getElementById('nps-legend');
    if (npsLegend) {
      const text = npsLegend.textContent || '';
      const matchProm = text.match(/Promotores:\s*([\d,]+)/);
      const matchPas = text.match(/Pasivos:\s*([\d,]+)/);
      const matchDet = text.match(/Detractores:\s*([\d,]+)/);
      if (matchProm) promotores = parseInt(matchProm[1].replace(/,/g, ''), 10);
      if (matchPas) pasivos = parseInt(matchPas[1].replace(/,/g, ''), 10);
      if (matchDet) detractores = parseInt(matchDet[1].replace(/,/g, ''), 10);
    }

    const intensidadProm = ideas > 0 ? (sumInt / ideas) : 0; 

    const pctPos = ideas > 0 ? Math.round((pos/ideas)*100) : 0;
    const pctNeu = ideas > 0 ? Math.round((neu/ideas)*100) : 0;
    const pctNeg = ideas > 0 ? Math.round((neg/ideas)*100) : 0;

    const createKpiCard = (label, value, colorClass, idStr = '') => `
      <div class="kpi-card" style="flex: 1 1 18%; min-width: 150px; margin: 0;">
        <div class="kpi-value ${colorClass}" ${idStr ? `id="${idStr}"` : ''}>${value}</div>
        <div class="kpi-label ${colorClass}">${label}</div>
      </div>
    `;

    // Row 1: Total encuestados, Promotores, Pasivos, Detractores, Con texto abierto
    // Row 2: Intensidad prom., Positivas, Neutras, Negativas, Ideas analizadas
    kpiGrid.style.display = 'block';
    kpiGrid.innerHTML = `
      <div style="display: flex; flex-wrap: wrap; gap: 16px; width: 100%; margin-bottom: 16px;">
        ${createKpiCard('Total encuestados', totalRespuestas, 'color-emplea')}
        ${createKpiCard('Promotores', promotores, 'color-csat')}
        ${createKpiCard('Pasivos', pasivos, 'color-emplea')}
        ${createKpiCard('Detractores', detractores, 'color-negative')}
        ${createKpiCard('Con texto abierto', textAbierto, 'color-emplea')}
      </div>
      <div style="display: flex; flex-wrap: wrap; gap: 16px; width: 100%;">
        ${createKpiCard('Intensidad prom.', intensidadProm.toFixed(2), 'color-emplea')}
        ${createKpiCard('Positivas', pos, 'color-csat')}
        ${createKpiCard('Neutras', neu, 'color-emplea')}
        ${createKpiCard('Negativas', neg, 'color-negative')}
        ${createKpiCard('Ideas analizadas', ideas, 'color-emplea')}
      </div>
    `;
  }

  function renderSentimentDistribution(comments) {
    const stats = {
      pos: { total: 0, prom: 0, pas: 0, det: 0 },
      neu: { total: 0, prom: 0, pas: 0, det: 0 },
      neg: { total: 0, prom: 0, pas: 0, det: 0 }
    };
    
    comments.forEach(c => {
      if (!c.es_valido) return;
      
      const nps = Number(c.nps_score);
      let npsKey = 'det';
      if (nps >= 9) npsKey = 'prom';
      else if (nps >= 7) npsKey = 'pas';

      let sentKey = 'neu';
      if (c.sentimiento === 'positivo') sentKey = 'pos';
      else if (c.sentimiento === 'negativo') sentKey = 'neg';
      
      stats[sentKey].total++;
      stats[sentKey][npsKey]++;
    });

    drawSentimentBars(stats);
  }

  // Draw Top categorías — menciones totales (Vertical Bars)
  function renderTopCategoriesBars(comments) {
    const container = $('categorias-barras-container');
    if (!container) return;

    container.innerHTML = '';
    // Horizontal flex row with bottom alignment for the columns
    container.style.cssText = 'display: flex; align-items: flex-end; justify-content: space-around; height: 180px; padding-top: 10px; padding-bottom: 10px; gap: 4px;';
    
    const stats = {};

    comments.forEach(c => {
      if (!c.es_valido) return;
      const cat = c.categoria_padre || c.categoria || 'Otros';
      if (!stats[cat]) stats[cat] = { pos: 0, neu: 0, neg: 0, total: 0 };
      stats[cat][c.sentimiento] = (stats[cat][c.sentimiento] || 0) + 1;
      stats[cat].total++;
    });

    const sortedCats = Object.keys(stats).sort((a, b) => stats[b].total - stats[a].total).slice(0, 8); // Top 8

    if (sortedCats.length === 0) {
      container.style.cssText = '';
      container.innerHTML = '<p style="color:var(--gray-500);font-size:12px;text-align:center;padding:20px 0;">No hay menciones registradas.</p>';
      return;
    }

    const maxTotal = stats[sortedCats[0]].total;

    sortedCats.forEach(cat => {
      const s = stats[cat];
      const heightPct = Math.max(10, (s.total / maxTotal) * 100);
      
      const pPct = (s.pos / s.total) * 100;
      const nPct = (s.neu / s.total) * 100;
      const negPct = (s.neg / s.total) * 100;

      const col = document.createElement('div');
      col.style.cssText = 'display:flex; flex-direction:column; align-items:center; flex:1; height:100%; justify-content:flex-end; gap:6px;';
      col.innerHTML = `
        <div style="font-size:11px; font-weight:600; color:var(--text2);">${s.total}</div>
        <div style="width:36px; height:${heightPct}%; background:var(--gray-200); border-radius:4px 4px 0 0; overflow:hidden; display:flex; flex-direction:column; justify-content:flex-end;">
          <div style="width:100%; height:${nPct}%; background:var(--gray-400);" title="Neutro: ${s.neu}"></div>
          <div style="width:100%; height:${pPct}%; background:var(--success-text);" title="Positivo: ${s.pos}"></div>
          <div style="width:100%; height:${negPct}%; background:var(--ulima-red);" title="Negativo: ${s.neg}"></div>
        </div>
        <div style="font-size:10px; font-weight:600; color:var(--dark); text-align:center; white-space:normal; line-height:1.1; max-width:64px; height:24px; overflow:hidden;">${_san.escapeHTML(cat)}</div>
      `;
      container.appendChild(col);
    });
  }

  function renderNPSSegmentBars(comments) {
    const container = $('seg-nps-container');
    if (!container) return;
    container.innerHTML = '';
    container.style.cssText = 'height: 180px; display: flex; flex-direction: column; justify-content: center;';

    const stats = {
      'Promotor': { total: 0, pos: 0, neu: 0, neg: 0 },
      'Pasivo': { total: 0, pos: 0, neu: 0, neg: 0 },
      'Detractor': { total: 0, pos: 0, neu: 0, neg: 0 }
    };

    let totalIdeas = 0;
    comments.forEach(c => {
      if (!c.es_valido) return;
      const nps = Number(c.nps_score);
      let seg = '';
      if (nps >= 9) seg = 'Promotor';
      else if (nps >= 7) seg = 'Pasivo';
      else seg = 'Detractor';
      c.segmento_nps = seg;
      
      stats[seg].total++;
      if (c.sentimiento === 'positivo') stats[seg].pos++;
      else if (c.sentimiento === 'negativo') stats[seg].neg++;
      else stats[seg].neu++;
      
      totalIdeas++;
    });

    if (totalIdeas === 0) return;

    const data = [
      { label: 'Promotores', value: stats['Promotor'].total, color: 'var(--success-text)', breakdown: stats['Promotor'] },
      { label: 'Pasivos', value: stats['Pasivo'].total, color: 'var(--gray-400)', breakdown: stats['Pasivo'] },
      { label: 'Detractores', value: stats['Detractor'].total, color: 'var(--ulima-red)', breakdown: stats['Detractor'] }
    ];

    const fragment = document.createDocumentFragment();
    data.forEach((item, index) => {
      if (item.value === 0) return;
      
      const pct = Math.round((item.value / totalIdeas) * 100);
      const barValueOutside = pct < 12;

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label" style="width: 80px;">${item.label}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="width:${pct}%; background-color:${item.color}; animation-delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}" style="${barValueOutside ? 'color: var(--dark);' : 'color: white;'}">${_fmt.formatInteger(item.value)}</span>
          </div>
        </div>
      `;

      // Tooltip events
      barItem.addEventListener('mouseenter', (e) => {
        const b = item.breakdown;
        let html = `<strong>${item.label}</strong>: ${_fmt.formatInteger(item.value)} ideas (${pct}%)<br>`;
        html += `Positivos: ${_fmt.formatInteger(b.pos)}<br>`;
        html += `Neutros: ${_fmt.formatInteger(b.neu)}<br>`;
        html += `Negativos: ${_fmt.formatInteger(b.neg)}`;
        _ttp.show(e, html);
      });
      barItem.addEventListener('mousemove', (e) => {
        _ttp.move(e);
      });
      barItem.addEventListener('mouseleave', () => {
        _ttp.hide();
      });

      fragment.appendChild(barItem);
    });

    container.appendChild(fragment);
  }

  // Generic Aspects & Intensity lists rendering
  function _renderList(containerId, data, isIntensity, isPos) {
    const container = $(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (data.length === 0) {
      container.innerHTML = '<span style="font-size:12px; color:var(--gray-500);">Data insuficiente</span>';
      return;
    }
    const maxVal = Math.max(...data.map(d => d.val));
    const fragment = document.createDocumentFragment();

    data.forEach((item, index) => {
      let pct = 0;
      let displayVal = '';
      if (isIntensity) {
        pct = item.val * 100;
        displayVal = Math.round(pct) + '%';
      } else {
        pct = maxVal > 0 ? (item.val / maxVal) * 100 : 0;
        displayVal = _fmt.formatInteger(item.val);
      }
      pct = Math.round(pct);
      const barValueOutside = pct < 12;
      const color = isPos ? 'var(--success-text)' : 'var(--ulima-red)';

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label">${_san.escapeHTML(item.name)}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="width:${pct}%; background-color:${color}; animation-delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}" style="${barValueOutside ? 'color: var(--dark);' : 'color: white;'}">${displayVal}</span>
          </div>
        </div>
      `;

      const tooltipText = isIntensity ? 
        `<strong>${_san.escapeHTML(item.name)}</strong>: Intensidad promedio ${displayVal}` : 
        `<strong>${_san.escapeHTML(item.name)}</strong>: ${_fmt.formatInteger(item.val)} menciones`;
        
      barItem.addEventListener('mouseenter', (e) => {
        _ttp.show(e, tooltipText);
      });
      barItem.addEventListener('mousemove', (e) => _ttp.move(e));
      barItem.addEventListener('mouseleave', () => _ttp.hide());

      fragment.appendChild(barItem);
    });
    container.appendChild(fragment);
  }

  function getAspectData(comments, filterSentimiento, isIntensity) {
    const aspStats = {};
    comments.forEach(c => {
      if (!c.es_valido) return;
      if (c.sentimiento !== filterSentimiento) return;
      const aspect = c.aspecto_normalizado || c.categoria || 'Otros';
      if (!aspStats[aspect]) aspStats[aspect] = { count: 0, intSum: 0 };
      aspStats[aspect].count++;
      aspStats[aspect].intSum += (c.intensidad || 0);
    });
    
    const aspects = Object.keys(aspStats);
    if (isIntensity) {
      return aspects.map(a => ({ name: a, val: aspStats[a].count > 0 ? (aspStats[a].intSum / aspStats[a].count) : 0, count: aspStats[a].count }))
        .filter(a => a.count > 0)
        .sort((a, b) => b.val - a.val).slice(0, 5);
    } else {
      return aspects.map(a => ({ name: a, val: aspStats[a].count }))
        .filter(a => a.val > 0)
        .sort((a, b) => b.val - a.val).slice(0, 5);
    }
  }

  function renderPositiveAspects(comments) {
    _renderList('aspectos-positivos-container', getAspectData(comments, 'positivo', false), false, true);
  }

  function renderNegativeAspects(comments) {
    _renderList('aspectos-negativos-container', getAspectData(comments, 'negativo', false), false, false);
  }

  function renderPositiveIntensity(comments) {
    _renderList('intensidad-positivos-container', getAspectData(comments, 'positivo', true), true, true);
  }

  function renderNegativeIntensity(comments) {
    _renderList('intensidad-negativos-container', getAspectData(comments, 'negativo', true), true, false);
  }

  function renderCareerNPSTable(comments) {
    const tbody = $('tbody-nps-carrera');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const carStats = {};
    comments.forEach(c => {
      const car = c.carrera || 'No Definida';
      if (!carStats[car]) carStats[car] = { total: 0, prom: 0, pas: 0, det: 0 };
      carStats[car].total++;
      if (c.nps_score >= 9) carStats[car].prom++;
      else if (c.nps_score >= 7) carStats[car].pas++;
      else carStats[car].det++;
    });

    const sortedCars = Object.keys(carStats).sort((a, b) => carStats[b].total - carStats[a].total);
    
    sortedCars.forEach(car => {
      const s = carStats[car];
      const pctNps = s.total > 0 ? Math.round(((s.prom - s.det) / s.total) * 100) : 0;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-size:12px; font-weight:600; color:var(--dark);">${_san.escapeHTML(car)}</td>
        <td class="text-center" style="font-size:12px;">${s.total}</td>
        <td class="text-center" style="font-size:12px; color:var(--success-text);">${s.prom}</td>
        <td class="text-center" style="font-size:12px; color:var(--ulima-orange);">${s.pas}</td>
        <td class="text-center" style="font-size:12px; color:var(--ulima-red);">${s.det}</td>
        <td class="text-center" style="font-size:12px; font-weight:600;">${pctNps}%</td>
      `;
      tbody.appendChild(tr);
    });
  }


  // Populate dynamic category selector
  function populateExploradorTopicsDropdown(comentarios) {
    const select = $('explorador-categoria');
    if (!select) return;

    const currentVal = select.value;
    const categories = [...new Set(comentarios.filter(c => c.es_valido).map(c => c.categoria))].sort();

    select.innerHTML = '<option value="">Todos los temas</option>';
    categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      select.appendChild(opt);
    });

    if (categories.includes(currentVal)) {
      select.value = currentVal;
    }
  }

  // Filter comments for the paginated list
  function applyExploradorFilters() {
    const searchVal = $('explorador-search')?.value.toLowerCase() || '';
    const catVal = $('explorador-categoria')?.value || '';
    const sentVal = $('explorador-sentimiento')?.value || '';

    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCar = $('filter-carrera-sent')?.value || '';
    const filtroCiclo = _dh.getSelectedValues($('filter-ciclo-sent')) || '';

    state.filteredComments = state.originalComments.filter(c => {
      if (filtroCar && c.carrera !== filtroCar) return false;
      if (filtroFac) {
        if (esEstudiosGen(filtroFac)) {
          const cycles = filtroCiclo ? (Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo]) : CICLOS_ESTUDIOS_GENERALES;
          if (!cycles.includes(c.ciclo)) return false;
        } else if (c.facultad !== filtroFac) {
          return false;
        }
      } else if (filtroCiclo) {
        const selectedCycles = Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo];
        if (selectedCycles.length > 0 && !selectedCycles.includes(c.ciclo)) return false;
      }

      if (catVal && c.categoria !== catVal) return false;
      if (sentVal && c.sentimiento !== sentVal) return false;

      if (searchVal) {
        const inOrig = c.fragmento_original?.toLowerCase().includes(searchVal);
        const inCorregido = c.fragmento_mostrar?.toLowerCase().includes(searchVal);
        const inCarrera = c.carrera?.toLowerCase().includes(searchVal);
        const inCat = c.categoria?.toLowerCase().includes(searchVal);
        if (!inOrig && !inCorregido && !inCarrera && !inCat) return false;
      }

      return true;
    });

    state.currentPage = 0;
    renderExplorerTable();
    updateExploradorPagination();
  }

  // Render rows in the comments table
  function renderExplorerTable() {
    const tbody = $('tbody-explorador-comentarios');
    if (!tbody) return;

    tbody.innerHTML = '';
    const start = state.currentPage * state.pageSize;
    const end = Math.min(start + state.pageSize, state.filteredComments.length);
    const pageComments = state.filteredComments.slice(start, end);

    if (pageComments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center" style="color:var(--gray-500); padding: 24px;">No se encontraron comentarios con los filtros actuales.</td></tr>';
      return;
    }

    const fragment = document.createDocumentFragment();
    pageComments.forEach(c => {
      const tr = document.createElement('tr');

      let sentBadge = '';
      if (!c.es_valido) {
        const motivoLabel = c.motivo_invalidez === 'spam_o_ruido' ? 'Ruido' : 'Sin opinión';
        sentBadge = `<span style="background:var(--gray-200); color:var(--gray-600); border-radius:12px; padding:3px 8px; font-size:11px; font-weight:700;">${motivoLabel}</span>`;
      } else {
        let bg = 'var(--gray-200)', fg = 'var(--gray-700)', label = 'Neutro';
        if (c.sentimiento === 'positivo') {
          bg = 'var(--success-pastel)';
          fg = 'var(--success-text)';
          label = 'Positivo';
        } else if (c.sentimiento === 'negativo') {
          bg = 'var(--danger-pastel)';
          fg = 'var(--ulima-red)';
          label = 'Negativo';
        }
        sentBadge = `<span style="background:${bg}; color:${fg}; border-radius:12px; padding:3px 8px; font-size:11px; font-weight:700;">${label}</span>`;
      }

      let npsBg = 'var(--gray-200)', npsFg = 'var(--gray-700)';
      if (c.nps_score >= 9) {
        npsBg = 'var(--success-pastel)';
        npsFg = 'var(--success-text)';
      } else if (c.nps_score >= 7) {
        npsBg = 'var(--warning-pastel)';
        npsFg = 'var(--warning-text)';
      } else {
        npsBg = 'var(--danger-pastel)';
        npsFg = 'var(--ulima-red)';
      }
      const npsBadge = `<span style="background:${npsBg}; color:${npsFg}; border-radius:50%; width:24px; height:24px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:700;">${c.nps_score}</span>`;

      const commentText = state.showCorregido ? (c.fragmento_mostrar || c.fragmento_original) : c.fragmento_original;
      const displayComment = c.es_valido 
        ? _san.escapeHTML(commentText) 
        : `<span style="color:var(--gray-400); font-style:italic;">[Invalidado: ${c.motivo_invalidez}]</span> "${_san.escapeHTML(commentText)}"`;

      const cId = c.id_fragmento || c.id || c.comentario_id_original || '-';

      let computedSeg = c.segmento_nps;
      if (!computedSeg) {
        if (c.nps_score >= 9) computedSeg = 'Promotor';
        else if (c.nps_score >= 7) computedSeg = 'Pasivo';
        else computedSeg = 'Detractor';
      }

      tr.innerHTML = `
        <td style="font-size:11px; color:var(--text2);">${_san.escapeHTML(cId)}</td>
        <td style="font-size:11px; font-weight:600; color:var(--dark);">${_san.escapeHTML(c.carrera)}</td>
        <td class="text-center" style="font-size:11px; color:var(--text2);">${_san.escapeHTML(c.ciclo || '-')}</td>
        <td class="text-center" style="font-size:11px; font-weight:600;">${_san.escapeHTML(computedSeg)}</td>
        <td class="text-center">${npsBadge}</td>
        <td style="font-size:11px; line-height:1.4; color:var(--text); text-align:left;">${displayComment}</td>
        <td style="font-size:11px; color:var(--text2);">${_san.escapeHTML(c.categoria_padre || c.categoria || '-')}</td>
        <td class="text-center">${sentBadge}</td>
        <td class="text-center" style="font-size:11px; font-weight:600; color:var(--dark);">${c.intensidad ? Math.round(c.intensidad * 100) + '%' : '-'}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.appendChild(fragment);
  }

  function updateExploradorPagination() {
    const total = state.filteredComments.length;
    const prevBtn = $('explorador-btn-prev');
    const nextBtn = $('explorador-btn-next');
    const info = $('explorador-pagination-info');

    if (!prevBtn || !nextBtn || !info) return;

    const start = state.currentPage * state.pageSize;
    const end = Math.min(start + state.pageSize, total);

    prevBtn.disabled = state.currentPage === 0;
    nextBtn.disabled = end >= total;

    if (total === 0) {
      info.textContent = 'Mostrando 0-0 de 0 comentarios';
    } else {
      info.textContent = `Mostrando ${start + 1}-${end} de ${total} comentarios`;
    }
  }

  // Export filtered comments as CSV
  function exportCSV() {
    const comments = state.filteredComments;
    if (comments.length === 0) {
      alert('No hay comentarios para exportar.');
      return;
    }

    const headers = ['ID', 'Carrera', 'Facultad', 'Ciclo', 'NPS Score', 'Sentimiento', 'Intensidad', 'Tema', 'Tema Padre', 'Comentario Original', 'Comentario Corregido', 'Valido', 'Motivo Invalidez'];
    
    const rows = comments.map(c => [
      c.id,
      c.carrera,
      c.facultad,
      c.ciclo || '',
      c.nps_score,
      c.sentimiento,
      c.intensidad,
      c.aspecto_normalizado || '',
      c.categoria_padre,
      c.fragmento_original,
      c.fragmento_mostrar || '',
      c.es_valido ? 'SI' : 'NO',
      c.motivo_invalidez || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(val => {
        const strVal = String(val === null || val === undefined ? '' : val);
        if (strVal.includes(',') || strVal.includes('"') || strVal.includes('\n') || strVal.includes('\r')) {
          return `"${strVal.replace(/"/g, '""')}"`;
        }
        return strVal;
      }).join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `comentarios_cualitativos_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Set up event listeners
  function setupExploradorListeners() {
    const searchInput = $('explorador-search');
    if (searchInput && !searchInput.dataset.listener) {
      searchInput.addEventListener('input', () => {
        applyExploradorFilters();
      });
      searchInput.dataset.listener = 'true';
    }

    const catSelect = $('explorador-categoria');
    if (catSelect && !catSelect.dataset.listener) {
      catSelect.addEventListener('change', () => {
        applyExploradorFilters();
      });
      catSelect.dataset.listener = 'true';
    }

    const sentSelect = $('explorador-sentimiento');
    if (sentSelect && !sentSelect.dataset.listener) {
      sentSelect.addEventListener('change', () => {
        applyExploradorFilters();
      });
      sentSelect.dataset.listener = 'true';
    }

    const toggleText = $('explorador-toggle-texto');
    if (toggleText && !toggleText.dataset.listener) {
      toggleText.addEventListener('change', (e) => {
        state.showCorregido = e.target.checked;
        renderExplorerTable();
      });
      toggleText.dataset.listener = 'true';
    }

    const exportBtn = $('explorador-export-csv');
    if (exportBtn && !exportBtn.dataset.listener) {
      exportBtn.addEventListener('click', () => {
        exportCSV();
      });
      exportBtn.dataset.listener = 'true';
    }

    const prevBtn = $('explorador-btn-prev');
    if (prevBtn && !prevBtn.dataset.listener) {
      prevBtn.addEventListener('click', () => {
        if (state.currentPage > 0) {
          state.currentPage--;
          renderExplorerTable();
          updateExploradorPagination();
        }
      });
      prevBtn.dataset.listener = 'true';
    }

    const nextBtn = $('explorador-btn-next');
    if (nextBtn && !nextBtn.dataset.listener) {
      nextBtn.addEventListener('click', () => {
        const total = state.filteredComments.length;
        if ((state.currentPage + 1) * state.pageSize < total) {
          state.currentPage++;
          renderExplorerTable();
          updateExploradorPagination();
        }
      });
      nextBtn.dataset.listener = 'true';
    }
  }

  // Main render function
  function render(sentimentCache, totalRespuestasGlobal) {
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;

    if (!sentimentCache || !sentimentCache.topicos || !sentimentCache.topicos.length) {
      kpiGrid.innerHTML = `<p style="color:var(--gray-500);font-size:13px;padding:20px 0;">
        No hay datos de análisis semántico disponibles para este período.</p>`;
      return;
    }

    renderMetricCards(sentimentCache.comentarios || [], sentimentCache, totalRespuestasGlobal);

    state.originalComments = sentimentCache.comentarios || [];
    state.sentimentCache = sentimentCache;

    // Filter based on active selectors
    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCar = $('filter-carrera-sent')?.value || '';
    const filtroCiclo = _dh.getSelectedValues($('filter-ciclo-sent')) || '';

    const businessFilteredComments = state.originalComments.filter(c => {
      if (filtroCar && c.carrera !== filtroCar) return false;
      if (filtroFac) {
        if (esEstudiosGen(filtroFac)) {
          const cycles = filtroCiclo ? (Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo]) : CICLOS_ESTUDIOS_GENERALES;
          if (!cycles.includes(c.ciclo)) return false;
        } else if (c.facultad !== filtroFac) {
          return false;
        }
      } else if (filtroCiclo) {
        const selectedCycles = Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo];
        if (selectedCycles.length > 0 && !selectedCycles.includes(c.ciclo)) return false;
      }
      return true;
    });

    const validFilteredComments = businessFilteredComments.filter(c => c.es_valido);
    const posCount = validFilteredComments.filter(c => c.sentimiento === 'positivo').length;
    const neuCount = validFilteredComments.filter(c => c.sentimiento === 'neutro').length;
    const negCount = validFilteredComments.filter(c => c.sentimiento === 'negativo').length;
    
    renderSentimentDistribution(businessFilteredComments);
    renderNPSSegmentBars(businessFilteredComments);
    renderTopCategoriesBars(businessFilteredComments);
    renderPositiveAspects(businessFilteredComments);
    renderNegativeAspects(businessFilteredComments);
    renderPositiveIntensity(businessFilteredComments);
    renderNegativeIntensity(businessFilteredComments);
    renderCareerNPSTable(businessFilteredComments);

    // Populate category filter and activate explorador
    populateExploradorTopicsDropdown(businessFilteredComments);
    setupExploradorListeners();
    applyExploradorFilters();
  }

  return {
    render,
    applyExploradorFilters
  };
})();
