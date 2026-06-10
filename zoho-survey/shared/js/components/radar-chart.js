/**
 * SURVEY RADAR CHART — Generador y renderizador del gráfico radar SVG.
 *
 * Dibuja círculos concéntricos, ejes de dimensiones, polígonos rellenos,
 * marcadores de satisfacción y maneja tooltips interactivos.
 * Genera de forma dinámica la recomendación de fortalezas/atenciones.
 *
 * Dependencias: SurveyFormatters, SurveySanitizer, SurveyTooltip (globales)
 *
 * @module components/radar-chart
 * @version 1.0.0
 */
window.SurveyRadarChart = (() => {
  'use strict';

  const _fmt = window.SurveyFormatters;
  const _san = window.SurveySanitizer;
  const _ms = window.SurveyMultiselect;
  const _dh = window.SurveyDOMHelpers;

  const C = window.SURVEY_CONFIG || {};
  const META_CSAT = C.META_CSAT ?? 93;
  const RADAR_LABEL_MAXLEN = C.RADAR_LABEL_MAXLEN ?? 26;
  const ANIMATION_FALLBACK_MS = C.ANIMATION_FALLBACK_MS ?? 1200;
  const SAT_KEYS = C.SAT_KEYS ?? [
    'Totalmente satisfecho',
    'Muy satisfecho',
    'Satisfecho',
    'Insatisfecho',
    'Totalmente insatisfecho',
  ];
  const SAT_TOP3_KEYS = SAT_KEYS.slice(0, 3);

  const sumKeys = (row, keys) => keys.reduce((acc, k) => acc + (row[k] || 0), 0);
  const dimensionAplica = (rows, dim) => rows.some((r) => r.dimension === dim && sumKeys(r, SAT_KEYS) > 0);
  const $ = (id) => document.getElementById(id);

  /**
   * Actualiza el cuadro de texto de insights del gráfico radar.
   */
  function updateInsightFortaleza(allDims, fac, car, cic) {
    const insightEl = $('insight-fortaleza');
    if (!insightEl) return;

    if (!allDims.length) {
      insightEl.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }

    const fortalezas = allDims.filter((d) => d.pct >= META_CSAT).sort((a, b) => b.pct - a.pct);
    const adecuados = allDims.filter((d) => d.pct >= 80 && d.pct < META_CSAT).sort((a, b) => b.pct - a.pct);
    const atencion = allDims.filter((d) => d.pct < 80).sort((a, b) => a.pct - b.pct);

    const hayFiltro = fac || car || (Array.isArray(cic) ? cic.length > 0 : cic);
    const contexto = hayFiltro ? [fac, car, Array.isArray(cic) ? cic.join(', ') : cic].filter(Boolean).join(' · ') : '';
    const cleanContexto = _san.escapeHTML(contexto);
    const fmtP = (v) => _fmt.formatPercent(v, 2);
    const fmtD = (d) => _san.escapeHTML(_fmt.formatDimensionName(d));
    let txt = '';

    if (hayFiltro) {
      txt += `<strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">${cleanContexto}</strong><br>`;
      if (fortalezas.length) {
        txt += `${fortalezas.length === 1 ? 'La dimensión mejor evaluada es' : 'Las dimensiones mejor evaluadas son'} `;
        txt += fortalezas
          .slice(0, 3)
          .map((d) => `<strong>${fmtD(d.dim)}</strong> (${fmtP(d.pct)})`)
          .join(', ');
        txt += `. En total, <strong>${fortalezas.length}</strong> de ${allDims.length} dimensiones superan el ${META_CSAT} %.`;
      } else {
        txt += `Ninguna dimensión alcanza el umbral de <strong>${META_CSAT} %</strong> (Fortaleza). `;
        if (adecuados.length) {
          txt += `Las más cercanas son ${adecuados
            .slice(0, 2)
            .map((d) => `<strong>${fmtD(d.dim)}</strong> (${fmtP(d.pct)})`)
            .join(' y ')}.`;
        }
      }
      if (atencion.length) {
        txt += ` ${atencion.length === 1 ? 'Requiere' : 'Requieren'} atención: `;
        txt += atencion
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dim)}</strong> (${fmtP(d.pct)})`)
          .join(' y ');
        txt += ` por estar debajo del 80 %.`;
      }
    } else {
      if (fortalezas.length) {
        txt += `La satisfacción en ${fortalezas
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dim)}</strong> (${fmtP(d.pct)})`)
          .join(' y ')} son las mejor evaluadas. `;
        txt += `En total, <strong>${fortalezas.length}</strong> de ${allDims.length} dimensiones se encuentran en rango de Fortaleza (≥${META_CSAT} %).`;
      } else {
        txt += `Actualmente ninguna dimensión alcanza el umbral de <strong>${META_CSAT} %</strong> (Fortaleza).`;
      }
      if (atencion.length) {
        txt += ` ${atencion.length === 1 ? 'La dimensión' : 'Las dimensiones'} `;
        txt += atencion
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dim)}</strong> (${fmtP(d.pct)})`)
          .join(' y ');
        txt += ` ${atencion.length === 1 ? 'requiere' : 'requieren'} atención prioritaria.`;
      }
    }
    insightEl.innerHTML = txt;
  }

  /**
   * Renderiza el Radar Chart en el SVG.
   *
   * @param {Object} options
   * @param {string} options.svgId - ID del contenedor SVG ('radar-chart')
   * @param {Array} options.filteredDimensions - Dimensiones ya filtradas por facultad/carrera/ciclo
   * @param {Array} options.rawDimensions - Lista original de dimensiones para inicializar filtros de categorías
   * @param {string} options.fac - Facultad seleccionada
   * @param {string} options.car - Carrera seleccionada
   * @param {string|Array} options.cic - Ciclo(s) seleccionado(s)
   */
  function render(options = {}) {
    const { svgId = 'radar-chart', filteredDimensions = [], rawDimensions = [], fac = '', car = '', cic = '' } = options;
    const svg = $(svgId);
    if (!svg) return;

    // Inicializar filtro de categorías en el radar (si existe el select)
    const selCat = $('filter-categoria-radar');
    if (selCat && selCat.options.length <= 1 && rawDimensions.length > 0) {
      const cats = [...new Set(rawDimensions.map((r) => r.categoria))].sort();
      const catDisplay = { 'Administrativo y Bienestar': 'Servicios al estudiante' };
      cats.forEach((c) => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = catDisplay[c] || c;
        selCat.appendChild(opt);
      });
      if (!selCat.__multiselect && _ms) {
        selCat.__multiselect = _ms.create(selCat, () => render(options), 'Todas las categorías', 'categorías');
        selCat.__multiselect.update();
      }

      // Enlazar al botón de reset para limpiar categorías
      const resetBtn = $('reset-radar');
      if (resetBtn && !resetBtn.dataset._catHooked) {
        resetBtn.dataset._catHooked = '1';
        resetBtn.addEventListener('click', () => {
          if (selCat.__multiselect) {
            Array.from(selCat.options).forEach((o) => {
              if (o.value) o.selected = false;
            });
            selCat.__multiselect.update();
            render(options);
          }
        });
      }
    }

    const selectedCats = selCat ? _dh.getSelectedValues(selCat) : null;

    // Agrupar satisfacción por dimensión
    const dims = {};
    filteredDimensions.forEach((r) => {
      if (!dimensionAplica(filteredDimensions, r.dimension)) return;
      if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0, categoria: r.categoria };
      dims[r.dimension].total += sumKeys(r, SAT_KEYS);
      dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
    });

    const allDims = Object.entries(dims)
      .filter(([, v]) => v.total > 0)
      .map(([dim, v]) => ({ dim, pct: (v.top3 / v.total) * 100, categoria: v.categoria }))
      .filter((d) => !selectedCats || selectedCats.length === 0 || selectedCats.includes(d.categoria));

    if (!allDims.length) {
      svg.innerHTML = '<text x="300" y="250" text-anchor="middle" font-size="14" fill="#9CA3AF">Sin datos</text>';
      updateInsightFortaleza([], fac, car, cic);
      return;
    }
    allDims.sort((a, b) => b.pct - a.pct);

    const cx = 300;
    const cy = 250;
    const maxR = 200;
    const n = allDims.length;
    const parts = [];

    // Círculos concéntricos de escala (25%, 50%, 75%, 100%)
    [0.25, 0.5, 0.75, 1].forEach((f) =>
      parts.push(`<circle cx="${cx}" cy="${cy}" r="${maxR * f}" fill="none" stroke="#E5E7EB" stroke-width="1"/>`),
    );

    // Ejes radiales y etiquetas de dimensiones
    allDims.forEach((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x2 = cx + maxR * Math.cos(angle);
      const y2 = cy + maxR * Math.sin(angle);
      parts.push(`<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="#E5E7EB" stroke-width="1"/>`);

      const lx = cx + (maxR + 26) * Math.cos(angle);
      const ly = cy + (maxR + 26) * Math.sin(angle);
      const anchor = angle > Math.PI / 2 || angle < -Math.PI / 2 ? 'end' : 'start';

      parts.push(`<text x="${lx}" y="${ly}" font-size="10" font-weight="500" fill="#6B7280" style="cursor:pointer;"
                  text-anchor="${anchor}" dominant-baseline="middle"
                  onmousemove="window.SurveyTooltip.show(event,'${_fmt.formatDimensionNameForAttr(d.dim)}: ${_fmt.formatPercent(d.pct, 2)}')"
                  onmouseleave="window.SurveyTooltip.hide()">${_fmt.formatDimensionNameSVG(d.dim, RADAR_LABEL_MAXLEN)}</text>`);
    });

    // Puntos del polígono de datos
    const outer = allDims
      .map((d, i) => {
        const a = (Math.PI * 2 * i) / n - Math.PI / 2;
        return `${cx + maxR * Math.cos(a)},${cy + maxR * Math.sin(a)}`;
      })
      .join(' ');

    const data = allDims
      .map((d, i) => {
        const a = (Math.PI * 2 * i) / n - Math.PI / 2;
        const r = (d.pct / 100) * maxR;
        return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
      })
      .join(' ');

    // Agregar polígono con animación SVG SMIL
    parts.push(`<polygon points="${outer}" fill="rgba(55,65,81,0.18)" stroke="#374151" stroke-width="2">
      <animate attributeName="points" from="${outer}" to="${data}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
    </polygon>`);

    // Círculos marcadores en las puntas con animación
    allDims.forEach((d, i) => {
      const a = (Math.PI * 2 * i) / n - Math.PI / 2;
      const rFinal = (d.pct / 100) * maxR;
      const ox = cx + maxR * Math.cos(a);
      const oy = cy + maxR * Math.sin(a);
      const px = cx + rFinal * Math.cos(a);
      const py = cy + rFinal * Math.sin(a);
      const color = d.pct >= META_CSAT ? 'var(--satisfaction-high,#374151)' : d.pct >= 80 ? 'var(--satisfaction-medium,#9CA3AF)' : 'var(--satisfaction-low,#FF0000)';

      parts.push(`<circle cx="${ox}" cy="${oy}" r="4" fill="${color}" style="cursor:pointer;opacity:0">
                  <animate attributeName="cx" from="${ox}" to="${px}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="cy" from="${oy}" to="${py}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
                </circle>`);
    });

    svg.innerHTML = parts.join('');

    // Disparar las animaciones inmediatamente
    setTimeout(() => {
      svg.querySelectorAll('animate').forEach((anim) => {
        try {
          anim.beginElement();
        } catch (e) {}
      });
    }, 10);

    updateInsightFortaleza(allDims, fac, car, cic);
  }

  return { render, dimensionAplica };
})();
