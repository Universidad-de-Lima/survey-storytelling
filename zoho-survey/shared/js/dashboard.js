(() => {
  'use strict';

  // ── Constantes y Configuración de Negocio ──
  const config = window.SURVEY_CONFIG || {};
  const BASE_URL = './json';
  const META_NPS = config.META_NPS ?? 50;
  const META_CSAT = config.META_CSAT ?? 93;
  const META_EMPLEABILIDAD = config.META_EMPLEABILIDAD ?? 85;
  const CARRERAS_12_CICLOS = config.CARRERAS_12_CICLOS ?? ['Derecho', 'Psicología'];
  const FACULTADES_12_CICLOS = config.FACULTADES_12_CICLOS ?? ['Facultad de Derecho', 'Facultad de Psicología'];
  const PROGRAMA_ESTUDIOS_GENERALES = config.PROGRAMA_ESTUDIOS_GENERALES ?? 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = config.CICLOS_ESTUDIOS_GENERALES ?? ['1° Ciclo', '2° Ciclo'];
  const FACULTAD_PLACEHOLDER = config.FACULTAD_PLACEHOLDER ?? 'Todas las facultades';
  const FACULTAD_PLACEHOLDER_PROG = config.FACULTAD_PLACEHOLDER_PROG ?? 'Todas las facultades / programas';
  const SAT_KEYS = config.SAT_KEYS ?? [
    'Totalmente satisfecho',
    'Muy satisfecho',
    'Satisfecho',
    'Insatisfecho',
    'Totalmente insatisfecho',
  ];
  const SAT_TOP3_KEYS = SAT_KEYS.slice(0, 3);

  // ── Módulos Externos Reutilizables ──
  const _fmt = window.SurveyFormatters;
  const _san = window.SurveySanitizer;
  const _dh = window.SurveyDOMHelpers;
  const _ttp = window.SurveyTooltip;
  const _pb = window.SurveyProgressBar;
  const _fc = window.SurveyFilterController;
  const _rc = window.SurveyRadarChart;
  const _sv = window.SurveySentimentView;

  // Cache Central de Datos
  const cache = {
    dashboard: null,
    dimensiones: null,
    ids: null,
    npsCicloCarrera: null,
    csatCicloCarrera: null,
    npsCarrera: null,
    csatCarrera: null,
    filtros: null,
    sentimiento: null,
  };

  // Referencias a Elementos DOM Clave
  const DOM = {
    tooltip: document.getElementById('tooltip'),
    footerAnio: document.getElementById('footer-anio'),
    footerPeriodo: document.getElementById('footer-periodo'),
    footerFuenteTexto: document.getElementById('footer-fuente-texto'),
    kpiNpsValue: document.getElementById('kpi-nps-value'),
    kpiNpsBar: document.getElementById('kpi-nps-bar'),
    kpiNpsMeta: document.getElementById('kpi-nps-meta'),
    kpiCsatValue: document.getElementById('kpi-csat-value'),
    kpiCsatBar: document.getElementById('kpi-csat-bar'),
    kpiCsatMeta: document.getElementById('kpi-csat-meta'),
    kpiEmpleaValue: document.getElementById('kpi-emplea-value'),
    kpiEmpleaBar: document.getElementById('kpi-emplea-bar'),
    kpiEmpleaMeta: document.getElementById('kpi-emplea-meta'),
    kpiEmpleaCard: document.getElementById('kpi-emplea-card'),
    npsBar: document.getElementById('nps-bar'),
    npsLegend: document.getElementById('nps-legend'),
    csatBar: document.getElementById('csat-bar'),
    csatLegend: document.getElementById('csat-legend'),
    insightHallazgos: document.getElementById('insight-hallazgos'),
    insightFortaleza: document.getElementById('insight-fortaleza'),
    insightAtencion: document.getElementById('insight-atencion'),
    radarChart: document.getElementById('radar-chart'),
    detallePromedioRef: document.getElementById('detalle-promedio-ref'),
    detallePromedioNpsRef: document.getElementById('detalle-promedio-nps-ref'),
    progressFill: document.getElementById('progress-fill'),
  };

  let csatScoreGlobal = 0;

  const $ = (id) => document.getElementById(id);
  const pct = (value, total) => (total > 0 ? Math.round((value / total) * 100) : 0);
  const esEstudiosGen = (fac) => fac === PROGRAMA_ESTUDIOS_GENERALES;
  const sumKeys = (row, keys) => keys.reduce((acc, key) => acc + (row[key] || 0), 0);

  /**
   * Carga asíncrona de datos con resiliencia y degradación gradual.
   */
  async function loadAllData() {
    const criticalEndpoints = {
      dashboard: 'dashboard_data',
      filtros: 'filtros',
      dimensiones: 'dimensiones',
    };
    const optionalEndpoints = {
      ids: 'ids',
      npsCicloCarrera: 'nps_ciclo_carrera',
      csatCicloCarrera: 'csat_ciclo_carrera',
      npsCarrera: 'nps_carrera',
      csatCarrera: 'csat_carrera',
      sentimiento: 'sentimiento',
    };

    try {
      // 1. Cargar endpoints críticos (fallan globalmente ante error)
      const criticalKeys = Object.keys(criticalEndpoints);
      const criticalPromises = criticalKeys.map((key) =>
        fetch(`${BASE_URL}/${criticalEndpoints[key]}.json`).then((r) => {
          if (!r.ok) throw new Error(`Archivo crítico no disponible: ${criticalEndpoints[key]}`);
          return r.json();
        })
      );
      const criticalResults = await Promise.all(criticalPromises);
      criticalKeys.forEach((key, index) => {
        cache[key] = criticalResults[index];
      });

      // 2. Cargar endpoints opcionales de forma segura (tolerante a fallos de red/períodos vacíos)
      const optionalKeys = Object.keys(optionalEndpoints);
      const optionalPromises = optionalKeys.map((key) =>
        fetch(`${BASE_URL}/${optionalEndpoints[key]}.json`)
          .then((r) => (r.ok ? r.json() : null))
          .catch((err) => {
            console.warn(`JSON opcional no cargado [${optionalEndpoints[key]}]:`, err);
            return null;
          })
      );
      const optionalResults = await Promise.all(optionalPromises);
      optionalKeys.forEach((key, index) => {
        cache[key] = optionalResults[index];
      });

      csatScoreGlobal = cache.dashboard.resumen.csat.score;
      return true;
    } catch (error) {
      console.error('Fallo grave al cargar los datos esenciales del dashboard:', error);
      return false;
    }
  }

  /**
   * Filtra los datos de Zoho Survey aplicando los filtros activos de Facultad, Carrera y Ciclo.
   */
  function filtrarDatos(datos, facultad, carrera, ciclo) {
    if (!datos) return [];
    const ciclos = Array.isArray(ciclo) ? ciclo : ciclo ? [ciclo] : null;
    return datos.filter((row) => {
      if (esEstudiosGen(facultad)) {
        return (
          CICLOS_ESTUDIOS_GENERALES.includes(row.ciclo) &&
          (!carrera || row.carrera === carrera) &&
          (!ciclos || ciclos.includes(row.ciclo))
        );
      }
      return (
        (!facultad || row.facultad === facultad) &&
        (!carrera || row.carrera === carrera) &&
        (!ciclos || ciclos.includes(row.ciclo))
      );
    });
  }

  /**
   * Renderiza el encabezado, KPIs globales del negocio y el bloque de texto con insights.
   */
  function renderEjecutivo() {
    const { resumen, hallazgos, nps, csat } = cache.dashboard;
    if (DOM.footerAnio) DOM.footerAnio.textContent = resumen.año ?? resumen.ano;
    if (DOM.footerPeriodo) {
      DOM.footerPeriodo.textContent = `Periodo: ${_fmt.formatDate(resumen.fecha_inicio)} - ${_fmt.formatDate(resumen.fecha_fin)} · Dirección de Planificación y Acreditación`;
    }
    if (DOM.footerFuenteTexto) {
      const nivel = resumen.empleabilidad ? 'GRADUADOS - PREGRADO' : 'ESTUDIANTIL- PREGRADO';
      const periodo = resumen.periodo || (resumen.año ?? resumen.ano);
      DOM.footerFuenteTexto.textContent = `ENCUESTA DE SATISFACCIÓN ${nivel} - ${periodo}`;
    }

    DOM.kpiNpsValue.textContent = _fmt.formatDecimal(resumen.nps.score);
    DOM.kpiNpsBar.style.width = `${Math.min(100, Math.max(0, resumen.nps.score))}%`;
    DOM.kpiNpsMeta.textContent = `Meta ${_fmt.formatInteger(META_NPS)}`;

    DOM.kpiCsatValue.textContent = _fmt.formatPercent(resumen.csat.score);
    DOM.kpiCsatBar.style.width = `${resumen.csat.score}%`;
    DOM.kpiCsatMeta.textContent = `Meta ${_fmt.formatPercent(META_CSAT)}`;

    if (DOM.kpiEmpleaCard && resumen.empleabilidad) {
      DOM.kpiEmpleaCard.style.display = '';
      DOM.kpiEmpleaValue.textContent = _fmt.formatPercent(resumen.empleabilidad.score);
      DOM.kpiEmpleaBar.style.width = `${resumen.empleabilidad.score}%`;
      DOM.kpiEmpleaMeta.textContent = `Meta ${META_EMPLEABILIDAD} %`;
    } else if (DOM.kpiEmpleaCard) {
      DOM.kpiEmpleaCard.style.display = 'none';
    }

    renderNPSBar(nps);
    renderCSATBar(csat);

    const { nps_etapas: etapas } = hallazgos;
    const empleaPct = resumen.empleabilidad ? _fmt.formatInteger(Math.round(resumen.empleabilidad.score)) : '';
    DOM.insightHallazgos.innerHTML = resumen.empleabilidad
      ? _san.sanitizeHTML(`
      Actualmente, <strong>+${_fmt.formatInteger(hallazgos.csat_pct)} %</strong> de graduados están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos, que es de <strong>+${_fmt.formatInteger(hallazgos.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${hallazgos.nps_tipo}</strong>" a nivel global.
      La empleabilidad es de <strong>+${empleaPct}%</strong> respecto a la meta trazada para este año.
    `)
      : _san.sanitizeHTML(`
      Actualmente, <strong>+${_fmt.formatInteger(hallazgos.csat_pct)} %</strong> de estudiantes están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos, que es de <strong>+${_fmt.formatInteger(hallazgos.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${hallazgos.nps_tipo}</strong>" a nivel global,
      pero <strong>${hallazgos.tendencia}</strong> conforme avanza la carrera:
      <strong>Inicial (${_fmt.formatDecimal(etapas.Inicial || 0)})</strong> →
      <strong>Intermedio (${_fmt.formatDecimal(etapas.Intermedio || 0)})</strong> →
      <strong>Avanzado (${_fmt.formatDecimal(etapas.Avanzado || 0)})</strong>.
      Teniendo una diferencia de <strong>-${_fmt.formatInteger(hallazgos.delta)}</strong> puntos en el ciclo de vida estudiantil.
    `);
  }

  function renderNPSBar(nps) {
    const prom = nps.Promotores ?? nps.promotores ?? 0;
    const pas = nps.Pasivos ?? nps.pasivos ?? 0;
    const det = nps.Detractores ?? nps.detractores ?? 0;
    const total = prom + pas + det;
    DOM.npsBar.innerHTML = `<div class="csat-bar-row">`
      + `<div class="csat-segment" style="width:${pct(prom, total)}%; background:var(--gray-700);"
           data-label="Promotores (9-10)" data-value="${_fmt.formatInteger(prom)} (${_fmt.formatPctDecimal(prom, total)})"><span class="csat-label">${_fmt.formatPctSimple(prom, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(pas, total)}%; background:var(--gray-400);"
           data-label="Pasivos (7-8)" data-value="${_fmt.formatInteger(pas)} (${_fmt.formatPctDecimal(pas, total)})"><span class="csat-label">${_fmt.formatPctSimple(pas, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(det, total)}%; background:var(--ulima-orange);"
           data-label="Detractores (0-6)" data-value="${_fmt.formatInteger(det)} (${_fmt.formatPctDecimal(det, total)})"><span class="csat-label">${_fmt.formatPctSimple(det, total)}</span></div>`
      + `</div>`;
    DOM.npsLegend.innerHTML = `
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-700);"></div>Promotores: ${_fmt.formatInteger(prom)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-400);"></div>Pasivos: ${_fmt.formatInteger(pas)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--ulima-orange);"></div>Detractores: ${_fmt.formatInteger(det)}</div>
    `;
    if (_ttp) _ttp.bindToSegments('#nps-bar .csat-segment');
    adjustSegmentLabels('#nps-bar');
  }

  function renderCSATBar(csat) {
    const labels = [
      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' },
      { key: 'Muy satisfecho', color: 'var(--gray-600)' },
      { key: 'Satisfecho', color: 'var(--gray-400)' },
      { key: 'Insatisfecho', color: 'var(--ulima-orange)' },
      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' },
    ];
    const total = labels.reduce((accSum, item) => accSum + (csat[item.key] || 0), 0);
    const visibleLabels = labels.filter((item) => csat[item.key] > 0);
    DOM.csatBar.innerHTML = `<div class="csat-bar-row">`
      + visibleLabels
        .map((item) => {
          const p = pct(csat[item.key], total);
          return `<div class="csat-segment" style="width:${p}%; background:${item.color};"
                data-label="${item.key}" data-value="${_fmt.formatInteger(csat[item.key])} (${_fmt.formatPctDecimal(csat[item.key], total)})"><span class="csat-label">${_fmt.formatPctSimple(csat[item.key], total)}</span></div>`;
        })
        .join('')
      + `</div>`;
    DOM.csatLegend.innerHTML = visibleLabels
      .map((item) =>
        `<div class="legend-item"><div class="legend-dot" style="background:${item.color};"></div>${item.key}: ${_fmt.formatInteger(csat[item.key])}</div>`
      )
      .join('');
    if (_ttp) _ttp.bindToSegments('#csat-bar .csat-segment');
    adjustSegmentLabels('#csat-bar');
  }

  /**
   * Mide y ajusta de forma responsiva las etiquetas de segmentos de distribución.
   * Si la barra no cabe, renderiza etiquetas con líneas callout hacia arriba o abajo.
   */
  function adjustSegmentLabels(target) {
    let container, barRow;
    if (typeof target === 'string') {
      container = document.querySelector(target);
      if (!container) return;
      barRow = container.querySelector('.csat-bar-row');
    } else {
      barRow = target;
      container = barRow.parentElement;
    }
    if (!barRow || !container) return;

    const isDistBar = barRow.classList.contains('distribution-bar') || barRow.classList.contains('visibility-bar');
    const segSelector = isDistBar ? '.distribution-segment, .visibility-segment' : '.csat-segment';

    // Limpiar elementos de ejecuciones anteriores
    container.querySelectorAll('.csat-labels-above, .csat-labels-below').forEach((el) => el.remove());

    barRow.querySelectorAll(isDistBar ? '.dist-label' : '.csat-label').forEach((lbl) => {
      lbl.style.visibility = '';
    });

    const SAFETY_MARGIN = 16;
    const barWidth = barRow.offsetWidth;

    if (!barWidth) {
      barRow.addEventListener('animationend', function onEnd() {
        barRow.removeEventListener('animationend', onEnd);
        requestAnimationFrame(() => adjustSegmentLabels(target));
      }, { once: true });
      setTimeout(() => requestAnimationFrame(() => adjustSegmentLabels(target)), config.ANIMATION_FALLBACK_MS ?? 1200);
      if (!container.dataset._visListener) {
        container.dataset._visListener = '1';
        document.addEventListener('visibilitychange', function visHandler() {
          if (!document.hidden) {
            document.removeEventListener('visibilitychange', visHandler);
            delete container.dataset._visListener;
            adjustSegmentLabels(target);
          }
        });
      }
      return;
    }

    const smallSegs = [];
    barRow.querySelectorAll(segSelector).forEach((seg) => {
      const segPct = isDistBar
        ? (parseFloat(seg.style.width) || 0) / 100
        : seg.offsetWidth / barWidth;
      const tooNarrow = isDistBar
        ? segPct < 0.015
        : seg.offsetWidth < (config.MIN_SEGMENT_WIDTH ?? 30);
      const tooSmall = segPct < (config.SEGMENT_EXTERNAL_LABEL_PCT ?? 0.02);
      const textContent = (seg.textContent || '').trim();
      const textOverflows = isDistBar
        ? (textContent.length * 8 + SAFETY_MARGIN > seg.offsetWidth)
        : (() => { const lbl = seg.querySelector('.csat-label'); return lbl ? lbl.scrollWidth + SAFETY_MARGIN > seg.offsetWidth : false; })();
      const selected = textOverflows || tooNarrow || tooSmall;
      const isZero = isDistBar ? (parseFloat(seg.style.width) || 0) === 0 : segPct < (config.SEGMENT_LABEL_HIDE_PCT ?? 0.005);
      if (isZero || parseFloat(textContent) === 0) {
        const lbl = isDistBar ? seg.querySelector('.dist-label') : seg.querySelector('.csat-label');
        if (lbl) lbl.style.visibility = 'hidden';
        return;
      }
      if (selected) smallSegs.push(seg);
    });

    if (!smallSegs.length) {
      if (isDistBar) {
        const ROW_H = 6;
        const wa = document.createElement('div');
        wa.className = 'csat-labels-above';
        wa.style.height = (ROW_H + 4) + 'px';
        container.insertBefore(wa, barRow);
        const wb = document.createElement('div');
        wb.className = 'csat-labels-below';
        wb.style.height = (ROW_H + 4) + 'px';
        container.appendChild(wb);
      }
      return;
    }

    smallSegs.sort((a, b) => a.offsetWidth - b.offsetWidth);
    const aboveSegs = [];
    const belowSegs = [];
    smallSegs.forEach((seg, i) => {
      if (i % 2 === 0) aboveSegs.push(seg);
      else belowSegs.push(seg);
    });

    const ROW_H = 6;

    function createLabelWrap(className) {
      const w = document.createElement('div');
      w.className = className;
      return w;
    }

    const wrapAbove = createLabelWrap('csat-labels-above');
    container.insertBefore(wrapAbove, barRow);

    const wrapBelow = createLabelWrap('csat-labels-below');
    container.appendChild(wrapBelow);

    let distCumulativePct = 0;
    const distSegOffsets = [];
    if (isDistBar) {
      barRow.querySelectorAll(segSelector).forEach((seg) => {
        const pctWidth = parseFloat(seg.style.width) || 0;
        distSegOffsets.push({ seg, leftPct: distCumulativePct, pct: pctWidth });
        distCumulativePct += pctWidth;
      });
    }

    function renderLabelGroup(segs, wrap, isBelow) {
      if (!segs.length) return;
      const rows = [];
      const assignments = [];
      const wrapLeft = wrap.getBoundingClientRect().left;

      segs.forEach((seg) => {
        let cx;
        if (isDistBar) {
          const info = distSegOffsets.find((d) => d.seg === seg);
          cx = info ? ((info.leftPct + info.pct / 2) / 100) * barWidth : 0;
        } else {
          cx = (seg.getBoundingClientRect().left - wrapLeft) + seg.getBoundingClientRect().width / 2;
        }
        const txt = isDistBar ? (seg.textContent || '').trim() : (seg.querySelector('.csat-label')?.textContent || '');
        const temp = document.createElement('div');
        temp.className = 'csat-label-above';
        temp.textContent = txt;
        temp.style.cssText = 'position:absolute;left:-9999px';
        document.body.appendChild(temp);
        const labelW = temp.scrollWidth || 30;
        document.body.removeChild(temp);

        const labelL = cx - labelW / 2;
        let row = 0;
        for (let r = 0; r <= rows.length; r++) {
          if (!rows[r] || labelL >= rows[r] + 10) { row = r; rows[r] = cx + labelW / 2; break; }
        }
        assignments.push({ seg, cx, labelW, row, txt });
      });

      const totalRows = rows.length || 1;

      assignments.forEach(({ seg, cx, row, txt }) => {
        const lbl = isDistBar ? seg.querySelector('.dist-label') : seg.querySelector('.csat-label');
        if (lbl) lbl.style.visibility = 'hidden';

        const segColor = getComputedStyle(seg).backgroundColor;
        const el = document.createElement('div');
        el.className = 'csat-label-above';
        el.textContent = txt;
        el.style.color = segColor;
        wrap.appendChild(el);
        el.style.left = cx + 'px';

        if (isBelow) {
          el.style.top = (row * ROW_H + 4) + 'px';
        } else {
          el.style.top = ((totalRows - row) * ROW_H - 12) + 'px';
        }

        const line = document.createElement('span');
        line.className = 'callout-line';
        line.style.background = segColor;
        if (isBelow) {
          line.style.top = 'auto';
          line.style.bottom = '100%';
          line.style.height = Math.max(4, (row * ROW_H + 4)) + 'px';
        } else {
          line.style.height = Math.max(4, (totalRows * ROW_H + 4) - el.offsetTop - el.offsetHeight) + 'px';
        }
        el.appendChild(line);

        const arm = document.createElement('span');
        arm.className = 'callout-arm';
        arm.style.background = segColor;
        line.appendChild(arm);

        const dot = document.createElement('span');
        dot.className = 'callout-dot';
        dot.style.background = segColor;
        el.appendChild(dot);
      });

      wrap.style.height = (totalRows * ROW_H + 4) + 'px';
    }

    renderLabelGroup(aboveSegs, wrapAbove, false);
    renderLabelGroup(belowSegs, wrapBelow, true);

    const hAbove = parseFloat(wrapAbove.style.height) || 0;
    const hBelow = parseFloat(wrapBelow.style.height) || 0;
    const maxH = Math.max(hAbove, hBelow);
    if (maxH > 0) {
      wrapAbove.style.height = maxH + 'px';
      wrapBelow.style.height = maxH + 'px';
    }
  }

  // ==================== SECCIÓN OPERATIVO ====================
  function renderTop3Bars(containerId, data) {
    const container = $(containerId);
    if (!container) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item, index) => {
      const barClass = item.pct >= META_CSAT ? 'high' : item.pct >= 80 ? 'medium' : 'low';
      const barValueOutside = item.pct < 12;
      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label">${_fmt.formatDimensionName(item.dim)}</div>
        <div class="bar-container">
          <div class="bar-fill animated ${barClass}" style="width:${item.pct}%; animation-delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${_fmt.formatPercent(item.pct, 2)}</span>
          </div>
        </div>
      `;
      barItem.querySelector('.bar-container').addEventListener('mousemove', (e) => {
        const fac = $('filter-facultad-top3').value;
        const car = $('filter-carrera-top3').value;
        const cic = _dh.getSelectedValues($('filter-ciclo-top3'));
        const rows = filtrarDatos(cache.dimensiones, fac, car, cic).filter((r) => r.dimension === item.dim);
        const counts = {
          'Totalmente satisfecho': 0,
          'Muy satisfecho': 0,
          Satisfecho: 0,
          Insatisfecho: 0,
          'Totalmente insatisfecho': 0,
          'No utilizo': 0,
          'No conozco': 0,
        };
        rows.forEach((r) => {
          Object.keys(counts).forEach((key) => {
            counts[key] += r[key] || 0;
          });
        });
        const lines = Object.entries(counts)
          .filter(([, val]) => val > 0)
          .map(([key, val]) => `${key}: ${_fmt.formatInteger(val)}`);
        if (!lines.length) return _ttp ? _ttp.hide() : null;
        if (_ttp) _ttp.show(e, lines.join('<br>'));
      });
      barItem.querySelector('.bar-container').addEventListener('mouseleave', () => _ttp?.hide());
      fragment.appendChild(barItem);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  function updateTop3Filters() {
    const fac = $('filter-facultad-top3').value;
    const car = $('filter-carrera-top3').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-top3'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const categories = {
      academico: 'Académico',
      infraestructura: 'Infraestructura',
      tecnologia: 'Tecnología',
      adminBienestar: 'Administrativo y Bienestar',
      docencia: 'Docencia',
      desarrollo: 'Desarrollo Profesional',
    };
    const top3Data = {};
    Object.entries(categories).forEach(([key, nombre]) => {
      const dims = {};
      filtered
        .filter((r) => r.categoria === nombre)
        .forEach((r) => {
          if (!_rc.dimensionAplica(filtered, r.dimension)) return;
          if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0 };
          dims[r.dimension].total += sumKeys(r, SAT_KEYS);
          dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
        });
      top3Data[key] = Object.entries(dims)
        .map(([dim, val]) => ({ dim, pct: val.total ? (val.top3 / val.total) * 100 : 0 }))
        .sort((a, b) => b.pct - a.pct);
    });

    renderTop3Bars('chart-academico', top3Data.academico);
    renderTop3Bars('chart-infraestructura', top3Data.infraestructura);
    renderTop3Bars('chart-tecnologia', top3Data.tecnologia);
    renderTop3Bars('chart-admin-bienestar', top3Data.adminBienestar);
    renderTop3Bars('chart-docencia', top3Data.docencia);
    renderTop3Bars('chart-desarrollo', top3Data.desarrollo);

    ['chart-docencia', 'chart-desarrollo'].forEach((id) => {
      const chart = $(id);
      if (chart && chart.children.length === 0) {
        const card = chart.closest('.card');
        if (card) card.style.display = 'none';
      } else if (chart) {
        const card = chart.closest('.card');
        if (card) card.style.display = '';
      }
    });
  }

  function renderRadarIndependiente() {
    const fac = $('filter-facultad-radar').value;
    const car = $('filter-carrera-radar').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-radar'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);

    if (_rc) {
      _rc.render({
        svgId: 'radar-chart',
        filteredDimensions: filtered,
        rawDimensions: cache.dimensiones,
        fac,
        car,
        cic,
      });
    }
  }

  // ==================== SECCIÓN DETALLADO ====================
  function renderPreguntas() {
    const fac = $('filter-facultad-preguntas').value;
    const car = $('filter-carrera-preguntas').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-preguntas'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) {
        dimMap[r.dimension] = {
          categoria: r.categoria,
          totSat: 0,
          muySat: 0,
          sat: 0,
          insat: 0,
          totInsat: 0,
        };
      }
      dimMap[r.dimension].totSat += r['Totalmente satisfecho'] || 0;
      dimMap[r.dimension].muySat += r['Muy satisfecho'] || 0;
      dimMap[r.dimension].sat += r['Satisfecho'] || 0;
      dimMap[r.dimension].insat += r['Insatisfecho'] || 0;
      dimMap[r.dimension].totInsat += r['Totalmente insatisfecho'] || 0;
    });

    const data = Object.entries(dimMap)
      .map(([dim, val]) => {
        const total = val.totSat + val.muySat + val.sat + val.insat + val.totInsat;
        const top3 = val.totSat + val.muySat + val.sat;
        const p1 = total > 0 ? Math.round((val.totSat / total) * 100) : 0;
        const p2 = total > 0 ? Math.round((val.muySat / total) * 100) : 0;
        const p3 = total > 0 ? Math.round((val.sat / total) * 100) : 0;
        const p4 = total > 0 ? Math.round((val.insat / total) * 100) : 0;
        const p5 = total > 0 ? Math.max(0, 100 - p1 - p2 - p3 - p4) : 0;
        return {
          dimension: dim,
          categoria: val.categoria,
          top3box: total > 0 ? ((top3 / total) * 100).toFixed(2) : '0.00',
          totSat: val.totSat,
          muySat: val.muySat,
          sat: val.sat,
          insat: val.insat,
          totInsat: val.totInsat,
          total,
          pctTotSat: p1,
          pctMuySat: p2,
          pctSat: p3,
          pctInsat: p4,
          pctTotInsat: p5,
        };
      })
      .filter((item) => parseFloat(item.top3box) > 0)
      .sort((a, b) => parseFloat(b.top3box) - parseFloat(a.top3box));

    const tbody = $('tbody-preguntas');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const catCorta =
        item.categoria === 'Administrativo y Bienestar' ? 'Servicios' :
        item.categoria === 'Desarrollo Profesional' ? 'Desarrollo' :
        item.categoria;
      const heatClass =
        parseFloat(item.top3box) >= META_CSAT ? 'heat-high' :
        parseFloat(item.top3box) >= 80 ? 'heat-medium' : 'heat-low';

      tr.innerHTML = `
        <td>${_fmt.formatDimensionName(item.dimension)}</td>
        <td class="text-center"><span class="heatmap-cell ${heatClass}">${_fmt.formatPercent(parseFloat(item.top3box), 2)}</span></td>
        <td class="text-center">${_san.escapeHTML(catCorta)}</td>
        <td>
          <div class="distribution-bar animated">
            <div class="distribution-segment" style="width:${item.pctTotSat}%;background:var(--gray-800);" data-label="Totalmente satisfecho" data-value="${_fmt.formatInteger(item.totSat)}"><span class="dist-label">${item.pctTotSat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctMuySat}%;background:var(--gray-500);" data-label="Muy satisfecho" data-value="${_fmt.formatInteger(item.muySat)}"><span class="dist-label">${item.pctMuySat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctSat}%;background:var(--gray-300);color:var(--gray-700);" data-label="Satisfecho" data-value="${_fmt.formatInteger(item.sat)}"><span class="dist-label">${item.pctSat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctInsat}%;background:var(--ulima-orange);" data-label="Insatisfecho" data-value="${_fmt.formatInteger(item.insat)}"><span class="dist-label">${item.pctInsat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctTotInsat}%;background:var(--ulima-red);" data-label="Totalmente insatisfecho" data-value="${_fmt.formatInteger(item.totInsat)}"><span class="dist-label">${item.pctTotInsat}%</span></div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.distribution-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          if (_ttp) _ttp.show(e, `${seg.dataset.label}: ${seg.dataset.value}`);
        });
        seg.addEventListener('mouseleave', () => _ttp?.hide());
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    tbody.querySelectorAll('.distribution-bar').forEach((bar) => adjustSegmentLabels(bar));
    setTimeout(() => normalizeDistributionHeights(tbody), 800);
  }

  function normalizeDistributionHeights(tbody) {
    const aboveW = tbody.querySelectorAll('.csat-labels-above');
    const belowW = tbody.querySelectorAll('.csat-labels-below');
    let maxH = 0;
    aboveW.forEach((w) => { const h = parseFloat(w.style.height) || 0; if (h > maxH) maxH = h; });
    belowW.forEach((w) => { const h = parseFloat(w.style.height) || 0; if (h > maxH) maxH = h; });
    if (maxH > 0) {
      tbody.querySelectorAll('.distribution-bar, .visibility-bar').forEach((bar) => {
        const td = bar.parentElement;
        let wa = td.querySelector('.csat-labels-above');
        let wb = td.querySelector('.csat-labels-below');
        if (!wa) { wa = document.createElement('div'); wa.className = 'csat-labels-above'; td.insertBefore(wa, bar); }
        if (!wb) { wb = document.createElement('div'); wb.className = 'csat-labels-below'; td.appendChild(wb); }
        wa.style.height = maxH + 'px';
        wb.style.height = maxH + 'px';
      });
    }
  }

  function renderDetalleCarreras() {
    const fac = $('filter-facultad-detalle').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-detalle'));
    const filteredIds = filtrarDatos(cache.ids, fac, null, cic);
    const countsMap = {};
    filteredIds.forEach((r) => {
      countsMap[r.carrera] = (countsMap[r.carrera] || 0) + (r.total ?? r.count);
    });

    const hasCiclo = cache.npsCicloCarrera?.length > 0;
    const npsSource = hasCiclo ? cache.npsCicloCarrera : cache.npsCarrera;
    const csatSource = hasCiclo ? cache.csatCicloCarrera : cache.csatCarrera;

    const npsMap = {};
    (npsSource || []).forEach((r) => {
      if (fac && r.facultad && r.facultad !== fac) return;
      if (!npsMap[r.carrera]) npsMap[r.carrera] = { prom: 0, pas: 0, det: 0 };
      npsMap[r.carrera].prom += r.Promotores ?? r.promotores ?? 0;
      npsMap[r.carrera].pas += r.Pasivos ?? r.pasivos ?? 0;
      npsMap[r.carrera].det += r.Detractores ?? r.detractores ?? 0;
    });

    const csatMap = {};
    (csatSource || []).forEach((r) => {
      if (fac && r.facultad && r.facultad !== fac) return;
      if (!csatMap[r.carrera]) csatMap[r.carrera] = { t3b: 0, total: 0 };
      const t3b = sumKeys(r, SAT_TOP3_KEYS);
      const total = t3b + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
      csatMap[r.carrera].t3b += t3b;
      csatMap[r.carrera].total += total;
    });

    let csatRef = csatScoreGlobal;
    let npsRef = 0;
    {
      let prom = 0, pas = 0, det = 0;
      Object.values(npsMap).forEach((val) => {
        prom += val.prom;
        pas += val.pas;
        det += val.det;
      });
      const total = prom + pas + det;
      npsRef = total > 0 ? ((prom - det) / total) * 100 : 0;
    }
    if (esEstudiosGen(fac)) {
      let tt = 0, tr = 0;
      Object.values(csatMap).forEach((val) => {
        tt += val.t3b;
        tr += val.total;
      });
      csatRef = tr > 0 ? (tt / tr) * 100 : csatScoreGlobal;
    }
    DOM.detallePromedioRef.textContent = `(${_fmt.formatDecimal(csatRef, 2)} %)`;
    DOM.detallePromedioNpsRef.textContent = `(${_fmt.formatDecimal(npsRef, 2)})`;

    const data = Object.entries(countsMap)
      .map(([carrera, encuestas]) => {
        const npsVal = npsMap[carrera];
        const csatVal = csatMap[carrera];
        const npsT = npsVal ? npsVal.prom + npsVal.pas + npsVal.det : 0;
        const npsS = npsT > 0 ? ((npsVal.prom - npsVal.det) / npsT) * 100 : 0;
        const csatS = csatVal?.total > 0 ? (csatVal.t3b / csatVal.total) * 100 : 0;
        return {
          carrera,
          encuestas,
          nps: npsS,
          csat: csatS,
          vsPromCsat: csatS - csatRef,
          vsPromNps: npsS - npsRef,
        };
      })
      .sort((a, b) => a.carrera.localeCompare(b.carrera));

    const tbody = $('tbody-detalle');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const vsCsatTxt =
        item.vsPromCsat >= 0
          ? `<span style="color:#00B04F;font-weight:600;">+${_fmt.formatDecimal(item.vsPromCsat, 2)}</span>`
          : `<span style="color:#FF0000;font-weight:600;">${_fmt.formatDecimal(item.vsPromCsat, 2)}</span>`;

      const vsNpsTxt =
        item.vsPromNps >= 0
          ? `<span style="color:#00B04F;font-weight:600;">+${_fmt.formatDecimal(item.vsPromNps, 2)}</span>`
          : `<span style="color:#FF0000;font-weight:600;">${_fmt.formatDecimal(item.vsPromNps, 2)}</span>`;

      tr.innerHTML = `
        <td>${_san.escapeHTML(item.carrera)}</td>
        <td class="text-center">${_fmt.formatInteger(item.encuestas)}</td>
        <td class="text-center" style="font-weight:700;">${_fmt.formatPercent(item.csat, 2)}</td>
        <td class="text-center">${vsCsatTxt}</td>
        <td class="text-center" style="font-weight:700;">${_fmt.formatDecimal(item.nps, 2)}</td>
        <td class="text-center">${vsNpsTxt}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  function renderVisibilidad() {
    const fac = $('filter-facultad-visibilidad').value;
    const car = $('filter-carrera-visibilidad').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-visibilidad'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) dimMap[r.dimension] = { noConozco: 0, noUtilizo: 0, conoce: 0 };
      dimMap[r.dimension].noConozco += r['No conozco'] || 0;
      dimMap[r.dimension].noUtilizo += r['No utilizo'] || 0;
      dimMap[r.dimension].conoce += sumKeys(r, SAT_KEYS);
    });
    const data = Object.entries(dimMap)
      .filter(([, val]) => val.noConozco > 0 || val.noUtilizo > 0)
      .map(([dim, val]) => {
        const total = val.noConozco + val.noUtilizo + val.conoce;
        return {
          dimension: dim,
          noConozco: val.noConozco,
          noUtilizo: val.noUtilizo,
          conoce: val.conoce,
          pctNoConozco: total > 0 ? (val.noConozco / total) * 100 : 0,
          pctNoUtilizo: total > 0 ? (val.noUtilizo / total) * 100 : 0,
          pctConoce: total > 0 ? (val.conoce / total) * 100 : 0,
          total,
        };
      })
      .sort((a, b) => a.pctNoConozco + a.pctNoUtilizo - (b.pctNoConozco + b.pctNoUtilizo));

    const tbody = $('tbody-visibilidad');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    const fmtV = (val) => (val < 0 ? '' : Math.round(val) + '%');
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${_fmt.formatDimensionName(item.dimension)}</td>
        <td class="text-center">${_fmt.formatInteger(item.noConozco)} (${_fmt.formatDecimal(item.pctNoConozco, 2)} %)</td>
        <td class="text-center">${_fmt.formatInteger(item.noUtilizo)} (${_fmt.formatDecimal(item.pctNoUtilizo, 2)} %)</td>
        <td>
          <div class="visibility-bar animated">
            <div class="visibility-segment no-conozco" style="width:${item.pctNoConozco}%;" data-label="No conozco" data-value="${_fmt.formatInteger(item.noConozco)}"><span class="dist-label">${fmtV(item.pctNoConozco)}</span></div>
            <div class="visibility-segment no-utilizo" style="width:${item.pctNoUtilizo}%;" data-label="No utilizo" data-value="${_fmt.formatInteger(item.noUtilizo)}"><span class="dist-label">${fmtV(item.pctNoUtilizo)}</span></div>
            <div class="visibility-segment conocido"   style="width:${item.pctConoce}%;"    data-label="Conozco/Utilizo" data-value="${_fmt.formatInteger(item.conoce)}"><span class="dist-label">${fmtV(item.pctConoce)}</span></div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.visibility-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          if (_ttp) _ttp.show(e, `${seg.dataset.label}: ${seg.dataset.value}`);
        });
        seg.addEventListener('mouseleave', () => _ttp?.hide());
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    tbody.querySelectorAll('.visibility-bar').forEach((bar) => adjustSegmentLabels(bar));
    setTimeout(() => normalizeDistributionHeights(tbody), 800);
    updateInsightAtencion(data, fac, car, cic);
  }

  function updateInsightAtencion(data, fac, car, cic) {
    if (!DOM.insightAtencion || !data.length) {
      if (DOM.insightAtencion) DOM.insightAtencion.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const sorted = [...data].sort((a, b) => b.pctNoConozco + b.pctNoUtilizo - (a.pctNoConozco + a.pctNoUtilizo));
    const criticos = sorted.filter((d) => d.pctNoConozco + d.pctNoUtilizo >= 50);
    const moderados = sorted.filter((d) => {
      const sumVal = d.pctNoConozco + d.pctNoUtilizo;
      return sumVal >= 25 && sumVal < 50;
    });
    const hayFiltro = fac || car || (Array.isArray(cic) ? cic.length > 0 : cic);
    const contexto = hayFiltro ? [fac, car, Array.isArray(cic) ? cic.join(', ') : cic].filter(Boolean).join(' · ') : '';
    const cleanContexto = _san.escapeHTML(contexto);
    const fmtP = (v) => _fmt.formatDecimal(v, 2) + ' %';
    const fmtD = (d) => _san.escapeHTML(_fmt.formatDimensionName(d));
    let txt = '';

    if (hayFiltro) {
      txt += `<strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">${cleanContexto}</strong><br>`;
      if (criticos.length) {
        txt += `${criticos.length === 1 ? 'El servicio con <strong>menor visibilidad</strong> es' : 'Los servicios con <strong>menor visibilidad</strong> son'} `;
        txt += criticos
          .slice(0, 3)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(', ');
        txt += `. En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones tienen más del 50 % de desconocimiento o no uso.`;
      } else if (moderados.length) {
        txt += `No hay servicios con desconocimiento crítico (>50 %). Las dimensiones con mayor oportunidad son `;
        txt += moderados
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(' y ');
        txt += `.`;
      } else {
        txt += `Los servicios presentan niveles aceptables de visibilidad. Las dimensiones con mayor margen de mejora son `;
        txt += sorted
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(' y ');
        txt += `.`;
      }
    } else {
      if (sorted.length >= 2) {
        const [first, second] = sorted;
        txt += `<strong>${fmtD(first.dimension)}</strong> (${fmtP(first.pctNoConozco)} · No conozco + ${fmtP(first.pctNoUtilizo)} · No utilizo) y `;
        txt += `<strong>${fmtD(second.dimension)}</strong> (${fmtP(second.pctNoConozco)} · No conozco + ${fmtP(second.pctNoUtilizo)} · No utilizo) `;
        txt += `son las que presentan <strong>menor visibilidad</strong>.`;
        if (criticos.length) {
          txt += ` En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones superan el 50 % de desconocimiento o no uso.`;
        }
      } else if (sorted.length === 1) {
        const [first] = sorted;
        txt += `<strong>${fmtD(first.dimension)}</strong> (${fmtP(first.pctNoConozco)} · No conozco + ${fmtP(first.pctNoUtilizo)} · No utilizo) es la que presenta <strong>menor visibilidad</strong>.`;
      }
    }
    DOM.insightAtencion.innerHTML = txt;
  }

  // ==================== SECCIÓN SENTIMIENTO ====================
  function renderSentimiento() {
    if (_sv) _sv.render(cache.sentimiento);
  }

  function setupSentimientoFilters() {
    const selSent = $('filter-sentimiento');
    if (selSent) {
      selSent.addEventListener('change', () => {
        if (_sv) _sv.renderInsightsCards(cache.sentimiento);
      });
    }

    if (_fc) {
      _fc.setup('sent', cache.filtros, () => {
        if (_sv) {
          _sv.renderInsightsCards(cache.sentimiento);
          _sv.renderTablaSentimientoCarrera(cache.sentimiento);
        }
      });
    }
  }

  // ==================== BARRA DE PROGRESO ====================
  function setupProgressBar() {
    if (_pb) _pb.init();
  }

  // ==================== INICIALIZACIÓN ====================
  async function init() {
    if (!(await loadAllData())) {
      console.error('No se pudieron cargar los datos del dashboard.');
      return;
    }

    const tieneDatosCualitativos =
      cache.sentimiento &&
      cache.sentimiento.resumen &&
      cache.sentimiento.resumen.total_con_comentario > 0 &&
      cache.sentimiento.topicos &&
      cache.sentimiento.topicos.length > 0;

    // Ocultar ciclo si el período no lo contiene
    if (cache.filtros && !cache.filtros.has_ciclo) {
      document.querySelectorAll('.filter-ciclo-actions').forEach((el) => {
        el.style.display = 'none';
      });
    }

    if (!tieneDatosCualitativos) {
      const secSentimiento = document.getElementById('cualitativo');
      if (secSentimiento) secSentimiento.style.display = 'none';

      const navLinkSentimiento = document.querySelector('.nav-links a[href="#cualitativo"]');
      if (navLinkSentimiento) {
        const liSentimiento = navLinkSentimiento.closest('li');
        if (liSentimiento) liSentimiento.style.display = 'none';
        else navLinkSentimiento.style.display = 'none';
      }
    }

    renderEjecutivo();

    // Enlazar los controladores de filtros usando el módulo FilterController
    if (_fc) {
      _fc.setup('top3', cache.filtros, updateTop3Filters);
      _fc.setup('radar', cache.filtros, renderRadarIndependiente);
      _fc.setup('preguntas', cache.filtros, renderPreguntas);
      _fc.setup('detalle', cache.filtros, renderDetalleCarreras);
      _fc.setup('visibilidad', cache.filtros, renderVisibilidad);
    }

    if (tieneDatosCualitativos) {
      renderSentimiento();
      setupSentimientoFilters();
    }

    setupProgressBar();

    // Redimensionamiento Responsivo
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        adjustSegmentLabels('#nps-bar');
        adjustSegmentLabels('#csat-bar');
        document.querySelectorAll('.distribution-bar').forEach((bar) => adjustSegmentLabels(bar));
        document.querySelectorAll('.visibility-bar').forEach((bar) => adjustSegmentLabels(bar));
        setTimeout(() => {
          const tPreguntas = $('tbody-preguntas');
          const tVisibilidad = $('tbody-visibilidad');
          if (tPreguntas) normalizeDistributionHeights(tPreguntas);
          if (tVisibilidad) normalizeDistributionHeights(tVisibilidad);
        }, 800);
      }, 250);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
