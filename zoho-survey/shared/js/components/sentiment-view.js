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
  function createLegendItem(colorVar, label, pct, valLower) {
    const span = document.createElement('span');
    span.style.cssText = `color:${colorVar}; display:inline-flex; align-items:center; gap:4px; cursor:pointer;`;

    const dot = document.createElement('span');
    dot.style.cssText = `display:inline-block; width:8px; height:8px; background:${colorVar}; border-radius:50%;`;

    span.appendChild(dot);
    span.appendChild(document.createTextNode(`${label}: ${pct}%`));

    span.addEventListener('click', () => {
      const select = $('explorador-sentimiento');
      if (select) {
        select.value = valLower;
        applyExploradorFilters();
        const explSec = $('tabla-explorador-comentarios');
        if (explSec) explSec.scrollIntoView({ behavior: 'smooth' });
      }
    });

    return span;
  }

  // Draw the SVG Doughnut Chart
  function drawSVGDoughnut(pos, neu, neg) {
    const svg = $('svg-sentimiento');
    if (!svg) return;
    svg.innerHTML = '';

    const total = pos + neu + neg;
    const centerVal = $('doughnut-center-val');
    if (centerVal) centerVal.textContent = _fmt.formatInteger(total);

    const legend = $('sentimiento-legend');
    if (total === 0) {
      if (legend) legend.innerHTML = '';
      return;
    }

    const data = [
      { label: 'Positivo', value: pos, color: 'var(--success-text)' },
      { label: 'Neutro', value: neu, color: 'var(--ulima-orange)' },
      { label: 'Negativo', value: neg, color: 'var(--ulima-red)' }
    ];

    const r = 35;
    const circumference = 2 * Math.PI * r; // ~219.911
    let accumulatedPct = 0;

    data.forEach(item => {
      if (item.value === 0) return;

      const pctVal = item.value / total;
      const dashArray = `${pctVal * circumference} ${circumference}`;
      const dashOffset = -accumulatedPct * circumference;

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', '50');
      circle.setAttribute('cy', '50');
      circle.setAttribute('r', r.toString());
      circle.setAttribute('class', 'doughnut-segment');
      circle.style.stroke = item.color;
      circle.style.strokeDasharray = dashArray;
      circle.style.strokeDashoffset = dashOffset.toString();

      // Tooltip events
      circle.addEventListener('mouseenter', (e) => {
        const pctLabel = Math.round(pctVal * 100);
        _ttp.show(e, `<strong>${item.label}</strong>: ${item.value} (${pctLabel}%)`);
      });
      circle.addEventListener('mousemove', (e) => {
        _ttp.move(e);
      });
      circle.addEventListener('mouseleave', () => {
        _ttp.hide();
      });

      // Quick filter on click
      circle.style.cursor = 'pointer';
      circle.addEventListener('click', () => {
        const select = $('explorador-sentimiento');
        if (select) {
          select.value = item.label.toLowerCase();
          applyExploradorFilters();
          const explSec = $('tabla-explorador-comentarios');
          if (explSec) explSec.scrollIntoView({ behavior: 'smooth' });
        }
      });

      svg.appendChild(circle);
      accumulatedPct += pctVal;
    });

    // Draw legends
    if (legend) {
      legend.innerHTML = '';
      const pPct = Math.round((pos / total) * 100);
      const nPct = Math.round((neu / total) * 100);
      const negPct = Math.round((neg / total) * 100);
      
      legend.appendChild(createLegendItem('var(--success-text)', 'Positivo', pPct, 'positivo'));
      legend.appendChild(createLegendItem('var(--ulima-orange)', 'Neutro', nPct, 'neutro'));
      legend.appendChild(createLegendItem('var(--ulima-red)', 'Negativo', negPct, 'negativo'));
    }
  }

  // Draw category horizontal bars
  function renderCategoryBars(comments) {
    const container = $('categorias-barras-container');
    if (!container) return;

    container.innerHTML = '';
    
    const categoryCounts = {};
    const categoryIntensity = {};
    const categoryIntensityCount = {};

    comments.forEach(c => {
      if (!c.es_valido) return;
      const cat = c.categoria_padre || 'Otros';
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
      categoryIntensity[cat] = (categoryIntensity[cat] || 0) + c.intensidad;
      categoryIntensityCount[cat] = (categoryIntensityCount[cat] || 0) + 1;
    });

    const sortedCats = Object.keys(categoryCounts).sort((a, b) => categoryCounts[b] - categoryCounts[a]);

    if (sortedCats.length === 0) {
      container.innerHTML = '<p style="color:var(--gray-500);font-size:12px;text-align:center;padding:20px 0;">No hay menciones registradas.</p>';
      return;
    }

    const maxCount = categoryCounts[sortedCats[0]];

    sortedCats.forEach(cat => {
      const count = categoryCounts[cat];
      const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
      const avgInt = categoryIntensityCount[cat] > 0 ? (categoryIntensity[cat] / categoryIntensityCount[cat]) : 0;

      let barColor = 'var(--gray-500)';
      if (cat === 'Académico') barColor = 'var(--blue)';
      else if (cat === 'Infraestructura') barColor = 'var(--green)';
      else if (cat === 'Administrativo y Bienestar') barColor = 'var(--amber)';
      else if (cat === 'Valoración General') barColor = 'var(--success-text)';

      const row = document.createElement('div');
      row.className = 'category-row';
      row.innerHTML = `
        <div class="category-header">
          <span>${_san.escapeHTML(cat)}</span>
          <span>${count} mención${count !== 1 ? 'es' : ''} <span class="category-intensity" style="margin-left:8px;">⚡ Intensidad: ${Math.round(avgInt * 100)}%</span></span>
        </div>
        <div class="category-bar-wrapper">
          <div class="category-bar-fill" style="width: ${pct}%; background-color: ${barColor};"></div>
        </div>
      `;
      container.appendChild(row);
    });
  }

  // Draw Insights Cards (with phrases representativas)
  function renderInsightsCards(sentimentCache) {
    const container = $('insights-container');
    if (!container || !sentimentCache) return;

    const filtroTipo = $('filter-sentimiento')?.value || 'todos';
    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCar = $('filter-carrera-sent')?.value || '';
    const filtroCiclo = _dh.getSelectedValues($('filter-ciclo-sent')) || '';

    let topicos = sentimentCache.topicos || [];

    if (filtroTipo !== 'todos') {
      topicos = topicos.filter((t) => t.tipo === filtroTipo);
    }

    if (filtroCar) {
      topicos = topicos
        .map((t) => {
          const count = t.por_carrera[filtroCar] || 0;
          return { ...t, _filteredCount: count };
        })
        .filter((t) => t._filteredCount > 0);
    } else if (filtroFac) {
      topicos = topicos
        .map((t) => {
          let count;
          if (esEstudiosGen(filtroFac)) {
            const cycles = filtroCiclo
              ? Array.isArray(filtroCiclo)
                ? filtroCiclo
                : [filtroCiclo]
              : CICLOS_ESTUDIOS_GENERALES;
            count = cycles.reduce((sum, cycle) => sum + (t.por_ciclo[cycle] || 0), 0);
          } else {
            count = t.por_facultad[filtroFac] || 0;
          }
          return { ...t, _filteredCount: count };
        })
        .filter((t) => t._filteredCount > 0);
    } else if (filtroCiclo) {
      const selectedCycles = Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo];
      topicos = topicos
        .map((t) => {
          const count = selectedCycles.reduce((sum, cycle) => sum + (t.por_ciclo[cycle] || 0), 0);
          return { ...t, _filteredCount: count };
        })
        .filter((t) => t._filteredCount > 0);
    }

    if (!topicos.length) {
      container.innerHTML = `<p style="color:var(--gray-500);font-size:13px;padding:16px 0;">
        No hay insights para los filtros seleccionados.</p>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    topicos.forEach((t) => {
      const colores = colorPorTipo(t.tipo);
      const displayCount = t._filteredCount !== undefined ? t._filteredCount : t.total_comentarios;
      const frases = (t.frases_representativas || []).slice(0, 3);
      const card = document.createElement('div');
      card.style.cssText = `
        background:${colores.bg};border-left:4px solid ${colores.border};
        border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:12px;
      `;
      const frasesHTML = frases.length
        ? `<ul style="margin:8px 0 0 0;padding-left:16px;list-style:disc;">
            ${frases.map((f) => `<li style="font-size:12px;color:var(--gray-700);margin-bottom:4px;line-height:1.5;">"${_san.escapeHTML(f)}"</li>`).join('')}
           </ul>`
        : '';
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
          <div>
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;
              letter-spacing:0.5px;color:${colores.border};">${colores.label}</span>
            <h4 style="font-size:14px;font-weight:700;color:var(--gray-900);margin:4px 0;">${_san.escapeHTML(t.icono)} ${_san.escapeHTML(t.topico)}</h4>
          </div>
          <span style="background:${colores.border};color:white;border-radius:12px;
            padding:3px 10px;font-size:11px;font-weight:700;white-space:nowrap;">
            ${_fmt.formatInteger(displayCount)} comentario${displayCount !== 1 ? 's' : ''}
          </span>
        </div>
        ${frasesHTML}
      `;
      fragment.appendChild(card);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  // Draw narrative block
  function renderNarrativeIA(sentimentCache, comments) {
    const iaGlobal = $('insight-ia-global');
    const iaCategorias = $('insight-ia-categorias');
    if (!iaGlobal || !iaCategorias || !sentimentCache.insights_ia) return;

    const ia = sentimentCache.insights_ia;
    
    // Calculate filtered totals
    const total = comments.length;
    const pos = comments.filter(c => c.es_valido && c.sentimiento === 'positivo').length;
    const neg = comments.filter(c => c.es_valido && c.sentimiento === 'negativo').length;
    
    const filtroFac = $('filter-facultad-sent')?.value || '';
    if (filtroFac) {
      iaGlobal.innerHTML = `Para la facultad/programa seleccionada se analizaron <strong>${_fmt.formatInteger(total)}</strong> comentarios válidos, de los cuales <strong>${_fmt.formatInteger(pos)}</strong> presentan un sentimiento positivo y <strong>${_fmt.formatInteger(neg)}</strong> expresan insatisfacción o sugerencias de mejora.`;
    } else {
      iaGlobal.textContent = ia.global || 'No hay resumen global disponible.';
    }

    iaCategorias.innerHTML = '';
    if (ia.por_categoria_padre) {
      Object.entries(ia.por_categoria_padre).forEach(([catName, text]) => {
        const catCommentsCount = comments.filter(c => c.es_valido && c.categoria_padre === catName).length;
        if (filtroFac && catCommentsCount === 0) return;
        const li = document.createElement('li');
        li.innerHTML = `<strong>${_san.escapeHTML(catName)}</strong> (${catCommentsCount} menciones): ${_san.escapeHTML(text)}`;
        iaCategorias.appendChild(li);
      });
    }
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
    renderExploradorTable();
    updateExploradorPagination();
  }

  // Render rows in the comments table
  function renderExploradorTable() {
    const tbody = $('tbody-explorador-comentarios');
    if (!tbody) return;

    tbody.innerHTML = '';
    const start = state.currentPage * state.pageSize;
    const end = Math.min(start + state.pageSize, state.filteredComments.length);
    const pageComments = state.filteredComments.slice(start, end);

    if (pageComments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color:var(--gray-500); padding: 24px;">No se encontraron comentarios con los filtros actuales.</td></tr>';
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

      tr.innerHTML = `
        <td style="font-size:12px; font-weight:600; color:var(--dark);">${_san.escapeHTML(c.carrera)}</td>
        <td class="text-center" style="font-size:12px; color:var(--text2);">${_san.escapeHTML(c.ciclo || '-')}</td>
        <td class="text-center">${sentBadge}</td>
        <td class="text-center">${npsBadge}</td>
        <td style="font-size:12px; font-weight:600; color:var(--text2);">${_san.escapeHTML(c.categoria)}</td>
        <td style="font-size:12px; line-height:1.5; color:var(--text); text-align:left;">${displayComment}</td>
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
      c.categoria,
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
        renderExploradorTable();
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
          renderExploradorTable();
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
          renderExploradorTable();
          updateExploradorPagination();
        }
      });
      nextBtn.dataset.listener = 'true';
    }
  }

  // Legacy fallback table renderer
  function renderTablaSentimientoCarrera(sentimentCache) {
    const tbody = $('tbody-sentimiento-carrera');
    if (!tbody || !sentimentCache) return;

    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCar = $('filter-carrera-sent')?.value || '';

    let data = sentimentCache.por_carrera || [];

    if (filtroFac) data = data.filter((r) => r.facultad === filtroFac);
    if (filtroCar) data = data.filter((r) => r.carrera === filtroCar);

    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${_san.escapeHTML(item.carrera)}</td>
        <td class="text-center">${_fmt.formatInteger(item.total)}</td>
        <td class="text-center" style="color:var(--ulima-orange);font-weight:600;">${_fmt.formatInteger(item.pasivos)}</td>
        <td class="text-center" style="color:var(--ulima-red);font-weight:600;">${_fmt.formatInteger(item.detractores)}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    const insightEl = $('insight-cualitativo');
    if (!insightEl || !data.length) return;
    const topCarrera = [...data].sort((a, b) => b.total - a.total)[0];
    const totalGlobal = data.reduce((s, r) => s + r.total, 0);
    const topicosCount = (sentimentCache.topicos || []).length;
    insightEl.innerHTML = _san.sanitizeHTML(`
      Se identificaron <strong>${_fmt.formatInteger(topicosCount)} temas</strong> en los comentarios de Pasivos y Detractores.
      ${
        topCarrera
          ? `La carrera con más comentarios es <strong>${_san.escapeHTML(topCarrera.carrera)}</strong>
           (${_fmt.formatInteger(topCarrera.total)} de ${_fmt.formatInteger(totalGlobal)} total),
           con <strong>${_fmt.formatInteger(topCarrera.detractores)}</strong> de Detractores y
           <strong>${_fmt.formatInteger(topCarrera.pasivos)}</strong> de Pasivos.`
          : ''
      }
      Las frases representativas muestran el contexto real de cada preocupación estudiantil.
    `);
  }

  // Main render function
  function render(sentimentCache) {
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;

    if (!sentimentCache || !sentimentCache.topicos || !sentimentCache.topicos.length) {
      kpiGrid.innerHTML = `<p style="color:var(--gray-500);font-size:13px;padding:20px 0;">
        No hay datos de análisis semántico disponibles para este período.</p>`;
      return;
    }

    const r = sentimentCache.resumen;
    const isV3 = sentimentCache.version === '3.0' && sentimentCache.comentarios;

    if (isV3) {
      const invalidCount = r.comentarios_invalidos || 0;
      kpiGrid.innerHTML = `
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;">${_fmt.formatInteger(r.total_respuestas)}</div>
          <div class="kpi-label">Respuestas totales</div>
          <div class="kpi-meta">Muestra cualitativa</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;color:var(--success-text);">${_fmt.formatInteger(r.total_analizados)}</div>
          <div class="kpi-label" style="color:var(--success-text);">Comentarios válidos</div>
          <div class="kpi-meta">Clasificados por la IA</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;color:var(--gray-500);">${_fmt.formatInteger(invalidCount)}</div>
          <div class="kpi-label" style="color:var(--gray-600);">Mensajes sin opinión</div>
          <div class="kpi-meta">Ruido o saludo cordial</div>
        </div>
      `;

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
      
      // Update visual doughnut, bars, IA narrative
      drawSVGDoughnut(posCount, neuCount, negCount);
      renderCategoryBars(businessFilteredComments);
      renderNarrativeIA(sentimentCache, businessFilteredComments);

      // Render chips of topics
      const temasContainer = $('temas-container');
      if (temasContainer) {
        const topicsCounts = {};
        validFilteredComments.forEach(c => {
          topicsCounts[c.categoria] = (topicsCounts[c.categoria] || 0) + 1;
        });

        const chipsHTML = sentimentCache.topicos
          .map((t) => {
            const currentCount = topicsCounts[t.topico] || 0;
            if (currentCount === 0) return '';
            
            const colorMap = {
              negativo: 'var(--ulima-red)',
              mejora: 'var(--ulima-orange)',
              positivo: 'var(--success-text)',
            };
            const color = colorMap[t.tipo] || 'var(--gray-600)';
            return `<span class="tema-chip" data-topico="${_san.escapeHTML(t.topico)}" style="
            display:inline-flex;align-items:center;gap:6px;padding:6px 12px;
            border-radius:20px;border:1px solid ${color};color:${color};
            font-size:11px;font-weight:600;cursor:pointer;background:var(--white);
            transition:background 0.2s;">
            ${_san.escapeHTML(t.icono)} ${_san.escapeHTML(t.topico)} <span style="background:${color};color:white;border-radius:10px;padding:1px 6px;font-size:10px;">${currentCount}</span>
          </span>`;
          })
          .filter(Boolean)
          .join('');

        temasContainer.innerHTML = chipsHTML || '<p style="color:var(--gray-500);font-size:12px;padding:8px 0;">No hay temas mencionados para la selección.</p>';

        temasContainer.querySelectorAll('.tema-chip').forEach(chip => {
          chip.addEventListener('click', () => {
            const topicName = chip.dataset.topico;
            const select = $('explorador-categoria');
            if (select) {
              select.value = topicName;
              applyExploradorFilters();
              const explTable = $('tabla-explorador-comentarios');
              if (explTable) explTable.scrollIntoView({ behavior: 'smooth' });
            }
          });
        });
      }

      // Render insights cards
      renderInsightsCards(sentimentCache);

      // Populate category filter and activate explorador
      populateExploradorTopicsDropdown(businessFilteredComments);
      setupExploradorListeners();
      applyExploradorFilters();

    } else {
      // Fallback rendering
      kpiGrid.innerHTML = `
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;">${_fmt.formatInteger(r.total_analizados)}</div>
          <div class="kpi-label">Comentarios analizados</div>
          <div class="kpi-meta">Pasivos + Detractores</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;color:var(--ulima-orange);">${_fmt.formatInteger(r.pasivos)}</div>
          <div class="kpi-label" style="color:var(--ulima-orange);">Pasivos con comentario</div>
          <div class="kpi-meta">NPS 7–8</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value" style="font-size:28px;color:var(--ulima-red);">${_fmt.formatInteger(r.detractores)}</div>
          <div class="kpi-label" style="color:var(--ulima-red);">Detractores con comentario</div>
          <div class="kpi-meta">NPS 0–6</div>
        </div>
      `;

      const temasContainer = $('temas-container');
      if (temasContainer) {
        const chips = sentimentCache.topicos
          .map((t) => {
            const colorMap = {
              negativo: 'var(--ulima-red)',
              mejora: 'var(--ulima-orange)',
              positivo: 'var(--success-text)',
            };
            const color = colorMap[t.tipo] || 'var(--gray-600)';
            return `<span class="tema-chip" data-topico="${_san.escapeHTML(t.topico)}" style="
            display:inline-flex;align-items:center;gap:6px;padding:6px 12px;
            border-radius:20px;border:1px solid ${color};color:${color};
            font-size:11px;font-weight:600;cursor:pointer;background:var(--white);
            transition:background 0.2s;">
            ${_san.escapeHTML(t.icono)} ${_san.escapeHTML(t.topico)} <span style="background:${color};color:white;border-radius:10px;padding:1px 6px;font-size:10px;">${_fmt.formatInteger(t.total_comentarios)}</span>
          </span>`;
          })
          .join('');
        temasContainer.innerHTML = chips;
      }

      renderInsightsCards(sentimentCache);
      renderTablaSentimientoCarrera(sentimentCache);
    }
  }

  return {
    render,
    renderInsightsCards,
    renderTablaSentimientoCarrera,
    applyExploradorFilters
  };
})();
