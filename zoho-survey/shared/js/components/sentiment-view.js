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
 * @version 1.0.0
 */
window.SurveySentimentView = (() => {
  'use strict';

  const _fmt = window.SurveyFormatters;
  const _dh = window.SurveyDOMHelpers;
  const _san = window.SurveySanitizer;

  const C = window.SURVEY_CONFIG || {};
  const PROGRAMA_ESTUDIOS_GENERALES = C.PROGRAMA_ESTUDIOS_GENERALES ?? 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = C.CICLOS_ESTUDIOS_GENERALES ?? ['1° Ciclo', '2° Ciclo'];

  const esEstudiosGen = (f) => f === PROGRAMA_ESTUDIOS_GENERALES;
  const $ = (id) => document.getElementById(id);

  function colorPorTipo(tipo) {
    if (tipo === 'negativo') {
      return { border: 'var(--ulima-red)', bg: 'var(--sentiment-neg-bg, var(--danger-pastel))', label: 'Insatisfacción' };
    }
    if (tipo === 'positivo') {
      return { border: 'var(--success-text)', bg: 'var(--sentiment-pos-bg, var(--success-pastel))', label: 'Fortaleza reconocida' };
    }
    return { border: 'var(--ulima-orange)', bg: 'var(--sentiment-neu-bg, var(--warning-pastel))', label: 'Oportunidad de mejora' };
  }

  /**
   * Renderiza las tarjetas de insights cualitativos según los filtros aplicados.
   */
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

  /**
   * Renderiza la tabla de distribución de comentarios por carrera.
   */
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

  /**
   * Inicializa y renderiza la vista completa de sentimiento.
   *
   * @param {Object} sentimentCache - Objeto de datos de sentimientos cargado
   */
  function render(sentimentCache) {
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;

    if (!sentimentCache || !sentimentCache.topicos || !sentimentCache.topicos.length) {
      kpiGrid.innerHTML = `<p style="color:var(--gray-500);font-size:13px;">
        No hay datos de análisis semántico disponibles para este período.</p>`;
      return;
    }

    const r = sentimentCache.resumen;
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

  return {
    render,
    renderInsightsCards,
    renderTablaSentimientoCarrera,
  };
})();
