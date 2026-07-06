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

  const sumKeys = _dh.sumKeys;
  const dimensionAplica = (rows, dim) => rows.some((r) => r.dimension === dim && sumKeys(r, SAT_KEYS) > 0);
  const $ = _dh.$;

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

    svg.setAttribute('viewBox', '-80 0 760 500');

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
      if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0, categoria: r.categoria, totSat: 0, muySat: 0, sat: 0, insat: 0, totInsat: 0 };
      const d = dims[r.dimension];
      d.total += sumKeys(r, SAT_KEYS);
      d.top3 += sumKeys(r, SAT_TOP3_KEYS);
      d.totSat += (r['Totalmente satisfecho'] || 0);
      d.muySat += (r['Muy satisfecho'] || 0);
      d.sat += (r['Satisfecho'] || 0);
      d.insat += (r['Insatisfecho'] || 0);
      d.totInsat += (r['Totalmente insatisfecho'] || 0);
    });

    const allDims = Object.entries(dims)
      .filter(([, v]) => v.total > 0)
      .map(([dim, v]) => {
        const top2box = ((v.totSat + v.muySat) / v.total) * 100;
        const ponderado = ((5 * v.totSat + 4 * v.muySat + 3 * v.sat + 2 * v.insat + 1 * v.totInsat) / v.total) / 5 * 100;
        return { dim, pct: (v.top3 / v.total) * 100, categoria: v.categoria, top2box, ponderado, counts: { 'Totalmente satisfecho': v.totSat, 'Muy satisfecho': v.muySat, 'Satisfecho': v.sat, 'Insatisfecho': v.insat, 'Totalmente insatisfecho': v.totInsat }, total: v.total };
      })
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
    const R_label = maxR + 26;
    const n = allDims.length;
    const parts = [];

    // Círculos concéntricos de escala (25%, 50%, 75%, 100%)
    [0.25, 0.5, 0.75, 1].forEach((f) =>
      parts.push(`<circle cx="${cx}" cy="${cy}" r="${maxR * f}" fill="none" stroke="#E5E7EB" stroke-width="1"/>`),
    );

    // 1. Calcular posiciones iniciales y dibujar ejes radiales
    const labels = allDims.map((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x2 = cx + maxR * Math.cos(angle);
      const y2 = cy + maxR * Math.sin(angle);
      parts.push(`<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="#E5E7EB" stroke-width="1"/>`);

      const lx = cx + R_label * Math.cos(angle);
      const ly = cy + R_label * Math.sin(angle);

      // Determinar alineación de texto base según posición horizontal
      const cosA = Math.cos(angle);
      let anchor = 'middle';
      if (cosA > 0.0001) {
        anchor = 'start';
      } else if (cosA < -0.0001) {
        anchor = 'end';
      }

      return {
        dim: d.dim,
        pct: d.pct,
        top2box: d.top2box,
        ponderado: d.ponderado,
        angle: angle,
        x: lx,
        y: ly,
        rawY: ly,
        anchor: anchor,
        cosA: cosA
      };
    });

    // 2. Separar por lados (derecho e izquierdo) para resolver colisiones verticales
    // Las etiquetas en los ejes polares exactos se incluyen en ambos grupos para empujar a sus vecinos simétricamente.
    const rightLabels = labels.filter(l => l.cosA >= -0.001);
    const leftLabels = labels.filter(l => l.cosA <= 0.001);

    const minY = 20;
    const maxY = 480;
    const gap = 15; // separación vertical mínima de 15px entre textos

    const adjustSpacing = (list) => {
      const len = list.length;
      if (len <= 1) return;

      // Ordenar por coordenada Y inicial (de arriba a abajo)
      list.sort((a, b) => a.rawY - b.rawY);

      // Paso 1: Empujar hacia abajo
      list[0].y = Math.max(list[0].y, minY);
      for (let i = 1; i < len; i++) {
        if (list[i].y < list[i - 1].y + gap) {
          list[i].y = list[i - 1].y + gap;
        }
      }

      // Paso 2: Empujar hacia arriba si sobrepasa el límite inferior
      if (list[len - 1].y > maxY) {
        list[len - 1].y = maxY;
        for (let i = len - 2; i >= 0; i--) {
          if (list[i].y > list[i + 1].y - gap) {
            list[i].y = list[i + 1].y - gap;
          }
        }
      }
    };

    adjustSpacing(rightLabels);
    adjustSpacing(leftLabels);

    // 3. Proyección circular de etiquetas laterales y renderizado de textos SVG
    labels.forEach((l) => {
      // Para etiquetas laterales, recalculamos X para adaptarla a la curva del radar
      if (l.anchor !== 'middle') {
        const dy = Math.min(Math.abs(l.y - cy), R_label - 1);
        const signX = Math.cos(l.angle) >= 0 ? 1 : -1;
        l.x = cx + signX * Math.sqrt(R_label * R_label - dy * dy);
      }

      // Línea conectora desde la etiqueta hasta su punto de datos
      const rEnd = (l.pct / 100) * maxR;
      const pxEnd = cx + rEnd * Math.cos(l.angle);
      const pyEnd = cy + rEnd * Math.sin(l.angle);
      parts.push(`<line x1="${l.x}" y1="${l.y}" x2="${pxEnd}" y2="${pyEnd}" stroke="#9CA3AF" stroke-width="1" style="cursor:pointer;"
                  data-dim="${_fmt.formatDimensionNameForAttr(l.dim)}"
                  data-pct="${_fmt.formatDecimal(l.pct, 2)}"
                  data-t2b="${_fmt.formatDecimal(l.top2box, 2)}"
                  data-pond="${_fmt.formatDecimal(l.ponderado, 2)}"/>`);

      parts.push(`<text x="${l.x}" y="${l.y}" font-size="10" font-weight="500" fill="#6B7280" style="cursor:pointer;"
                  text-anchor="${l.anchor}" dominant-baseline="middle"
                  data-dim="${_fmt.formatDimensionNameForAttr(l.dim)}"
                  data-pct="${_fmt.formatDecimal(l.pct, 2)}"
                  data-t2b="${_fmt.formatDecimal(l.top2box, 2)}"
                  data-pond="${_fmt.formatDecimal(l.ponderado, 2)}">${_fmt.formatDimensionNameSVG(l.dim, RADAR_LABEL_MAXLEN)}</text>`);
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

      parts.push(`<circle cx="${ox}" cy="${oy}" r="4" fill="${color}" style="cursor:pointer;opacity:0"
                  data-dim="${_fmt.formatDimensionNameForAttr(d.dim)}"
                  data-pct="${_fmt.formatDecimal(d.pct, 2)}"
                  data-t2b="${_fmt.formatDecimal(d.top2box, 2)}"
                  data-pond="${_fmt.formatDecimal(d.ponderado, 2)}">
                  <animate attributeName="cx" from="${ox}" to="${px}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="cy" from="${oy}" to="${py}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
                </circle>`);
    });

    svg.innerHTML = parts.join('');

    // Bind tooltip events to radar labels via addEventListener (CSP-friendly)
    const _ttp = window.SurveyTooltip;
    if (_ttp) {
      svg.querySelectorAll('text[data-dim], circle[data-dim], line[data-dim]').forEach((el) => {
        const dim = el.getAttribute('data-dim');
        const pct = el.getAttribute('data-pct');
        const t2b = el.getAttribute('data-t2b');
        const pond = el.getAttribute('data-pond');
        el.addEventListener('mousemove', (e) => {
          // Build tooltip: table (Escala + Respuestas) + horizontal bar chart (T3B, T2B, Ponderado)
          const d = allDims.find(x => _fmt.formatDimensionNameForAttr(x.dim) === dim);
          let html = '<div style="display:flex;gap:16px;white-space:nowrap;">';

          // ——— Left column: Escala de Satisfacción + Respuestas ———
          html += '<table style="border-collapse:collapse;font-size:11px;">';
          html += '<tr><th style="text-align:left;padding:2px 6px;border-bottom:1px solid #ccc;">Escala de Satisfacción</th>' +
                  '<th style="text-align:center;padding:2px 6px;border-bottom:1px solid #ccc;">Respuestas</th></tr>';
          if (d) {
            const satKeys = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho', 'Insatisfecho', 'Totalmente insatisfecho'];
            satKeys.forEach((key) => {
              const val = d.counts[key] || 0;
              if (val === 0) return;
              html += `<tr><td style="padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${key}</td>` +
                      `<td style="text-align:center;padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${_fmt.formatInteger(val)}</td></tr>`;
            });
          }
          html += '</table>';

          // ——— Right column: horizontal bars estilo Top3 cards (monocromo tooltip) ———
          html += '<div style="display:flex;flex-direction:column;justify-content:center;gap:6px;min-width:150px;padding-left:8px;border-left:1px solid rgba(255,255,255,0.2);">';
          const barItems = [
            { label: 'T3B', value: pct },
            { label: 'T2B', value: t2b },
            { label: 'Pond.', value: pond }
          ];
          barItems.forEach((item) => {
            const cssVal = String(item.value).replace(',', '.');
            const p = parseFloat(cssVal);
            const outside = p < 12;
            html += '<div style="display:flex;align-items:center;gap:8px;">';
            html += `<span style="color:#fff;font-size:10px;font-weight:600;width:34px;text-align:right;flex-shrink:0;">${item.label}</span>`;
            html += '<div style="flex:1;height:18px;background:rgba(255,255,255,0.12);border-radius:4px;overflow:visible;position:relative;">';
            html += `<div style="height:100%;width:${cssVal}%;background:#fff;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:4px;transition:width 0.3s;min-width:0;">`;
            if (!outside) {
              html += `<span style="color:#111827;font-size:9px;font-weight:700;line-height:1;">${item.value}%</span>`;
            }
            html += '</div>';
            if (outside) {
              html += `<span style="position:absolute;left:100%;top:50%;transform:translateY(-50%);margin-left:4px;color:#fff;font-size:9px;font-weight:700;white-space:nowrap;">${item.value}%</span>`;
            }
            html += '</div>';
            html += '</div>';
          });
          html += '</div>'; // close right column
          html += '</div>'; // close flex container
          _ttp.show(e, html, true);
        });
        el.addEventListener('mouseleave', () => _ttp.hide());
      });
    }

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
