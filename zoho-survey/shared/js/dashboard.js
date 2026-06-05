(() => {
  'use strict';

  // ── Constantes de negocio ──
  // Fuente primaria: window.SURVEY_CONFIG (config/constants.js)
  // Fallback: valores hardcodeados (compatibilidad backward)
  const C = window.SURVEY_CONFIG || {};
  const BASE_URL = './json';
  const META_NPS = C.META_NPS ?? 50;
  const META_CSAT = C.META_CSAT ?? 93;
  const CARRERAS_12_CICLOS = C.CARRERAS_12_CICLOS ?? ['Derecho', 'Psicología'];
  const FACULTADES_12_CICLOS = C.FACULTADES_12_CICLOS ?? ['Facultad de Derecho', 'Facultad de Psicología'];
  const PROGRAMA_ESTUDIOS_GENERALES = C.PROGRAMA_ESTUDIOS_GENERALES ?? 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = C.CICLOS_ESTUDIOS_GENERALES ?? ['1° Ciclo', '2° Ciclo'];
  const FACULTAD_PLACEHOLDER = C.FACULTAD_PLACEHOLDER ?? 'Todas las facultades';
  const FACULTAD_PLACEHOLDER_PROG = C.FACULTAD_PLACEHOLDER_PROG ?? 'Todas las facultades / programas';
  const SAT_KEYS = C.SAT_KEYS ?? [
    'Totalmente satisfecho',
    'Muy satisfecho',
    'Satisfecho',
    'Insatisfecho',
    'Totalmente insatisfecho',
  ];
  const SAT_TOP3_KEYS = SAT_KEYS.slice(0, 3);

  const cache = {
    dashboard: null,
    dimensiones: null,
    ids: null,
    nps_ciclo_carrera: null,
    csat_ciclo_carrera: null,
    nps_carrera: null,
    csat_carrera: null,
    filtros: null,
    sentimiento: null,
  };

  const DOM = {
    tooltip: document.getElementById('tooltip'),
    footerAnio: document.getElementById('footer-anio'),
    footerPeriodo: document.getElementById('footer-periodo'),
    kpiNpsValue: document.getElementById('kpi-nps-value'),
    kpiNpsBar: document.getElementById('kpi-nps-bar'),
    kpiNpsMeta: document.getElementById('kpi-nps-meta'),
    kpiCsatValue: document.getElementById('kpi-csat-value'),
    kpiCsatBar: document.getElementById('kpi-csat-bar'),
    kpiCsatMeta: document.getElementById('kpi-csat-meta'),
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

  // ── Utilidades: delegar a módulos externos si disponibles (v2.0) ──
  // Fallback a definiciones inline para compatibilidad backward con HTMLs
  // que aún no cargan los scripts modulares.
  const _fmt = window.SurveyFormatters;
  const _san = window.SurveySanitizer;

  const formatInteger = _fmt ? _fmt.formatInteger : ((n) => n.toString());
  const formatDecimal = _fmt ? _fmt.formatDecimal : ((n, digits = 2) => {
    if (n === null || n === undefined) return '';
    const rounded = n.toFixed(digits);
    if (rounded.endsWith('0'.repeat(digits))) return Math.round(n).toString();
    return rounded.replace('.', ',');
  });
  const formatPercent = _fmt ? _fmt.formatPercent : ((n, d) => formatDecimal(n, d) + ' %');
  const formatPctSimple = _fmt ? _fmt.formatPctSimple : ((v, t) => (t === 0 ? '0%' : Math.round((v / t) * 100) + '%'));
  const formatPctDecimal = _fmt ? _fmt.formatPctDecimal : ((v, t) => {
    if (t === 0) return '0,0 %';
    return formatDecimal((v / t) * 100, 1) + ' %';
  });
  const formatDate = _fmt ? _fmt.formatDate : ((ds) =>
    new Date(`${ds}T12:00:00`).toLocaleDateString('es-PE', { day: 'numeric', month: 'long' }));
  const formatCicloText = _fmt ? _fmt.formatCicloText : ((ciclo) => {
    const match = ciclo.match(/^(\d+)/);
    if (!match) return ciclo;
    const num = match[1];
    return num === '1' || num === '3' ? `${num}.ᵉʳ ciclo` : `${num}.º ciclo`;
  });
  const cortarTexto = _fmt ? _fmt.cortarTexto : ((t, max) => (t.length > max ? `${t.slice(0, max - 1)}…` : t));
  const formatDimensionName = _fmt ? _fmt.formatDimensionName : ((dim) => {
    if (dim === 'Software especializado empleado en la carrera') {
      return '<span><i>Software</i> especializado empleado en la carrera</span>';
    }
    return dim;
  });
  const formatDimensionNameSVG = _fmt ? _fmt.formatDimensionNameSVG : ((dim, maxLen = (C.RADAR_LABEL_MAXLEN ?? 26)) => {
    const plain = formatDimensionName(dim).replace(/<[^>]*>/g, '');
    const truncated = cortarTexto(plain, maxLen);
    if (dim === 'Software especializado empleado en la carrera' && truncated.startsWith('Software')) {
      return `<tspan font-style="italic">Software</tspan>${truncated.slice('Software'.length)}`;
    }
    return truncated;
  });
  const formatDimensionNameForAttr = _fmt ? _fmt.formatDimensionNameForAttr : ((dim) =>
    formatDimensionName(dim).replace(/</g, '&lt;').replace(/>/g, '&gt;'));

  const pct = (v, t) => (t > 0 ? Math.round((v / t) * 100) : 0);
  const esEstudiosGen = (f) => f === PROGRAMA_ESTUDIOS_GENERALES;
  const sumKeys = (row, keys) => keys.reduce((acc, k) => acc + (row[k] || 0), 0);

  // ── Sanitización HTML (delegar a SurveySanitizer si disponible) ──
  const escapeHTML = _san ? _san.escapeHTML : ((str) => {
    if (!str || typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  });
  const sanitizeHTML = _san ? _san.sanitizeHTML : ((html) => {
    if (!html || typeof html !== 'string') return '';
    const allowedTags = ['br', 'strong', 'em', 'i', 'span'];
    let safe = escapeHTML(html);
    allowedTags.forEach((tag) => {
      safe = safe.split(`&lt;${tag}&gt;`).join(`<${tag}>`);
      safe = safe.split(`&lt;/${tag}&gt;`).join(`</${tag}>`);
    });
    safe = safe.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, '');
    safe = safe.replace(/\s+on\w+\s*=\s*[^\s>]*/gi, '');
    return safe;
  });

  function filtrarDatos(datos, fac, car, cic) {
    if (!datos) return [];
    const ciclos = Array.isArray(cic) ? cic : cic ? [cic] : null;
    return datos.filter((r) => {
      if (esEstudiosGen(fac)) {
        return (
          CICLOS_ESTUDIOS_GENERALES.includes(r.ciclo) &&
          (!car || r.carrera === car) &&
          (!ciclos || ciclos.includes(r.ciclo))
        );
      }
      return (
        (!fac || r.facultad === fac) &&
        (!car || r.carrera === car) &&
        (!ciclos || ciclos.includes(r.ciclo))
      );
    });
  }

  function getCarrerasForFiltro(facultad) {
    const { filtros } = cache;
    if (!facultad || esEstudiosGen(facultad)) return filtros.carreras;
    return filtros.facultad_carrera[facultad] || [];
  }

  /** Opciones de ciclo según CONSIDERACIONES: EG → 1-2; Derecho/Psicología → 1-12; resto → 1-10. */
  function getCiclosForFiltro(facultad, carrera) {
    if (esEstudiosGen(facultad)) return CICLOS_ESTUDIOS_GENERALES;
    const max =
      FACULTADES_12_CICLOS.includes(facultad) || CARRERAS_12_CICLOS.includes(carrera) ? (C.MAX_CICLOS_ESPECIALES ?? 12) : (C.MAX_CICLOS_DEFAULT ?? 10);
    return cache.filtros.ciclos.filter((c) => (parseInt(c) || 0) <= max);
  }

  function syncFilterActiveState(selFac, selCar, selCic) {
    const isActive = (sel) => {
      if (!sel) return false;
      const val = getSelectedValues(sel);
      return Array.isArray(val) ? val.length > 0 : val !== '';
    };
    [selFac, selCar, selCic].forEach((sel) => {
      if (sel) sel.classList.toggle('filter-active', isActive(sel));
    });
  }

  const ordenarFacultades = (lista, hasCiclo) =>
    hasCiclo ? [PROGRAMA_ESTUDIOS_GENERALES, ...lista.sort()] : [...lista.sort()];

  // ── Tooltip: delegar a SurveyTooltip si disponible ──
  const _ttp = window.SurveyTooltip;
  const showTooltip = _ttp ? _ttp.show : ((e, content) => {
    const { tooltip } = DOM;
    tooltip.innerHTML = sanitizeHTML(content);
    tooltip.style.display = 'block';
    tooltip.style.left = `${e.clientX + 10}px`;
    tooltip.style.top = `${e.clientY - 10}px`;
  });
  const hideTooltip = _ttp ? _ttp.hide : (() => { DOM.tooltip.style.display = 'none'; });
  window.showTooltip = showTooltip;
  window.hideTooltip = hideTooltip;

  const addTooltipToSegments = _ttp ? _ttp.bindToSegments : ((selector) => {
    document.querySelectorAll(selector).forEach((seg) => {
      seg.addEventListener('mousemove', (e) =>
        showTooltip(e, `${seg.dataset.label}: ${seg.dataset.value}`),
      );
      seg.addEventListener('mouseleave', hideTooltip);
    });
  });

  function populateSelect(sel, placeholder, items, texts) {
    const current = getSelectedValues(sel);
    sel.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach((item, i) => {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = texts ? texts[i] : item;
      if (Array.isArray(current) ? current.includes(item) : item === current) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
  }

  function getSelectedValues(sel) {
    if (!sel) return '';
    if (sel.multiple) {
      const vals = Array.from(sel.selectedOptions)
        .map((opt) => opt.value)
        .filter(Boolean);
      return vals.length ? vals : '';
    }
    const opt = sel.options[sel.selectedIndex];
    return opt ? opt.value : '';
  }

  function clearFilterSelect(sel) {
    if (!sel) return;
    const emptyOpt = Array.from(sel.options).find((opt) => opt.value === '');
    Array.from(sel.options).forEach((opt) => {
      opt.selected = emptyOpt ? opt === emptyOpt : false;
    });
    if (!sel.multiple) {
      sel.selectedIndex = emptyOpt ? Array.from(sel.options).indexOf(emptyOpt) : 0;
      if (emptyOpt) sel.value = '';
    }
  }

  function populateFacultadSelect(selFac, filtros) {
    const items = ordenarFacultades(filtros.facultades, filtros.has_ciclo);
    const placeholder = filtros.has_ciclo ? FACULTAD_PLACEHOLDER_PROG : FACULTAD_PLACEHOLDER;
    selFac.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach((f) => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = f;
      selFac.appendChild(opt);
    });
    selFac.selectedIndex = 0;
    selFac.value = '';
  }

  function syncFacultadCustomUI(selFac, hasCiclo) {
    if (!selFac?.__custom) return;
    selFac.__custom.update();
    selFac.__custom.button.textContent = hasCiclo ? FACULTAD_PLACEHOLDER_PROG : FACULTAD_PLACEHOLDER;
    selFac.__custom.button.classList.remove('filter-active');
    selFac.classList.remove('filter-active');
    selFac.__custom.wrapper.classList.remove('open');
  }

  function setSelectedValues(sel, values) {
    if (!sel) return;
    if (!sel.multiple) {
      sel.value = Array.isArray(values) ? values[0] || '' : values || '';
    } else {
      const normalized = new Set((Array.isArray(values) ? values : [values]).filter(Boolean));
      Array.from(sel.options).forEach((opt) => {
        opt.selected = normalized.has(opt.value);
      });
    }
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function formatMultiselectLabel(values, placeholder) {
    if (!values || !values.length) return placeholder;
    if (values.length === 1) return formatCicloText(values[0]) || values[0];
    return `${values.length} ciclos seleccionados`;
  }

  const getPlaceholderText = (sel) => {
    const emptyOption = sel.querySelector('option[value=""]');
    return emptyOption ? emptyOption.textContent : 'Seleccione';
  };

  const formatCustomLabel = (sel) => {
    const selected = getSelectedValues(sel);
    if (!selected) return getPlaceholderText(sel);
    const selectedOption = Array.from(sel.options).find((opt) => opt.value === selected);
    return selectedOption ? selectedOption.textContent : selected;
  };

  // ── Custom Select: delegar a SurveyCustomSelect si disponible ──
  const _cs = window.SurveyCustomSelect;
  const createCustomSelectDropdown = _cs
    ? (sel, cb) => _cs.create(sel, cb)
    : (function(sel, onChangeCallback) {
    const wrapper = document.createElement('div');
    wrapper.className = 'filter-custom-select';
    wrapper.style.position = 'relative';

    sel.classList.add('filter-select-hidden');
    sel.parentNode.insertBefore(wrapper, sel);
    wrapper.appendChild(sel);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-select filter-custom-toggle';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');
    button.textContent = formatCustomLabel(sel);
    wrapper.appendChild(button);

    const panel = document.createElement('div');
    panel.className = 'filter-custom-panel';
    panel.setAttribute('role', 'listbox');
    panel.hidden = true;
    wrapper.appendChild(panel);

    const renderOptions = () => {
      const currentValue = getSelectedValues(sel);
      panel.innerHTML = '';
      Array.from(sel.options).forEach((opt) => {
        if (!opt.value) return;
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'filter-custom-item';
        item.setAttribute('role', 'option');
        item.dataset.value = opt.value;
        item.textContent = opt.textContent || opt.value;
        if (opt.value === currentValue) {
          item.classList.add('active');
          item.setAttribute('aria-selected', 'true');
        }
        item.addEventListener('click', () => {
          setSelectedValues(sel, opt.value);
          button.textContent = item.textContent;
          renderOptions();
          closePanel();
        });
        panel.appendChild(item);
      });
      const any = Boolean(getSelectedValues(sel));
      button.classList.toggle('filter-active', any);
    };

    const openPanel = () => {
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      wrapper.classList.add('open');
      button.classList.add('filter-active');
      sel.classList.add('filter-active');
    };

    const closePanel = () => {
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      wrapper.classList.remove('open');
      if (!getSelectedValues(sel)) {
        button.classList.remove('filter-active');
        sel.classList.remove('filter-active');
      }
    };

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (panel.hidden) openPanel();
      else closePanel();
    });

    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openPanel();
      }
    });

    document.addEventListener('click', (event) => {
      if (!wrapper.contains(event.target)) closePanel();
    });

    sel.addEventListener('change', () => {
      const selected = getSelectedValues(sel);
      button.textContent = selected ? formatCustomLabel(sel) : getPlaceholderText(sel);
      const any = Boolean(selected);
      button.classList.toggle('filter-active', any);
      sel.classList.toggle('filter-active', any);
      renderOptions();
    });

    const update = () => {
      renderOptions();
      const selected = getSelectedValues(sel);
      button.textContent = selected ? formatCustomLabel(sel) : getPlaceholderText(sel);
      const active = Boolean(selected);
      button.classList.toggle('filter-active', active);
      sel.classList.toggle('filter-active', active);
    };

    renderOptions();
    return { update, close: closePanel, button, wrapper };
  });

  // ── Multiselect: delegar a SurveyMultiselect si disponible ──
  const _ms = window.SurveyMultiselect;
  const createMultiselectDropdown = _ms
    ? (sel, cb) => _ms.create(sel, cb)
    : (function(selCic, onChangeCallback) {
    const wrapper = document.createElement('div');
    wrapper.className = 'filter-multiselect';
    wrapper.style.position = 'relative';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-select filter-multiselect-toggle';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');
    button.textContent = formatMultiselectLabel(getSelectedValues(selCic), 'Todos los ciclos');
    wrapper.appendChild(button);

    const panel = document.createElement('div');
    panel.className = 'filter-multiselect-panel';
    panel.setAttribute('role', 'listbox');
    panel.hidden = true;
    wrapper.appendChild(panel);

    const renderOptions = () => {
      const selected = getSelectedValues(selCic);
      panel.innerHTML = '';
      Array.from(selCic.options).forEach((opt) => {
        if (!opt.value) return;
        const item = document.createElement('label');
        item.className = 'filter-multiselect-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = opt.value;
        checkbox.checked = Array.isArray(selected)
          ? selected.includes(opt.value)
          : selected === opt.value;
        checkbox.addEventListener('change', () => {
          const checkedValues = Array.from(
            panel.querySelectorAll('input[type="checkbox"]:checked'),
          ).map((i) => i.value);
          setSelectedValues(selCic, checkedValues);
          button.textContent = formatMultiselectLabel(checkedValues, 'Todos los ciclos');
          selCic.classList.toggle('filter-active', checkedValues.length > 0);
          button.classList.toggle('filter-active', checkedValues.length > 0);
        });
        const span = document.createElement('span');
        span.textContent = opt.textContent || opt.value;
        item.appendChild(checkbox);
        item.appendChild(span);
        panel.appendChild(item);
      });
      // Reflect active state on the visible button
      const anySelected =
        Array.from(panel.querySelectorAll('input[type="checkbox"]:checked')).length > 0;
      button.classList.toggle('filter-active', anySelected);
    };

    const openPanel = () => {
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      wrapper.classList.add('open');
      // show active border when opened (even without selection)
      button.classList.add('filter-active');
      selCic.classList.add('filter-active');
    };

    const closePanel = () => {
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      wrapper.classList.remove('open');
      // only keep active state if there are selected values
      const vals = getSelectedValues(selCic);
      const any = Array.isArray(vals) ? vals.length > 0 : !!vals;
      if (!any) {
        button.classList.remove('filter-active');
        selCic.classList.remove('filter-active');
      }
    };

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (panel.hidden) openPanel();
      else closePanel();
    });
    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openPanel();
      }
    });
    document.addEventListener('click', (event) => {
      if (!wrapper.contains(event.target)) closePanel();
    });

    wrapper.update = () => {
      renderOptions();
      const vals = getSelectedValues(selCic);
      const any = Array.isArray(vals) ? vals.length > 0 : !!vals;
      button.textContent = formatMultiselectLabel(vals, 'Todos los ciclos');
      button.classList.toggle('filter-active', any);
    };

    selCic.style.position = 'absolute';
    selCic.style.opacity = '0';
    selCic.style.pointerEvents = 'none';
    selCic.style.width = '1px';
    selCic.style.height = '1px';
    selCic.style.margin = '0';
    selCic.style.border = 'none';
    selCic.setAttribute('aria-hidden', 'true');
    selCic.tabIndex = -1;

    selCic.parentNode.insertBefore(wrapper, selCic.nextSibling);
    return wrapper;
  });

  async function loadAllData() {
    try {
      const endpoints = [
        'dashboard_data',
        'dimensiones',
        'ids',
        'nps_ciclo_carrera',
        'csat_ciclo_carrera',
        'nps_carrera',
        'csat_carrera',
        'filtros',
        'sentimiento',
      ];
      const results = await Promise.all(
        endpoints.map((name) =>
          fetch(`${BASE_URL}/${name}.json`)
            .then((r) => (r.ok ? r.json() : null))
            .catch(() => null),
        ),
      );
      const [
        dashboard,
        dimensiones,
        ids,
        nps_cc,
        csat_cc,
        nps_car,
        csat_car,
        filtros,
        sentimiento,
      ] = results;
      Object.assign(cache, {
        dashboard,
        dimensiones,
        ids,
        nps_ciclo_carrera: nps_cc,
        csat_ciclo_carrera: csat_cc,
        nps_carrera: nps_car,
        csat_carrera: csat_car,
        filtros,
        sentimiento,
      });
      csatScoreGlobal = dashboard.resumen.csat.score;
      return true;
    } catch (error) {
      console.error('Error cargando datos:', error);
      return false;
    }
  }

  function renderEjecutivo() {
    const { resumen: r, hallazgos: h, nps, csat } = cache.dashboard;
    DOM.footerAnio.textContent = r.año;
    DOM.footerPeriodo.textContent = `Periodo: ${formatDate(r.fecha_inicio)} - ${formatDate(r.fecha_fin)} · Dirección de Planificación y Acreditación`;

    DOM.kpiNpsValue.textContent = formatDecimal(r.nps.score);
    DOM.kpiNpsBar.style.width = `${Math.min(100, Math.max(0, r.nps.score))}%`;
    DOM.kpiNpsMeta.textContent = `Meta ${formatInteger(META_NPS)}`;

    DOM.kpiCsatValue.textContent = formatPercent(r.csat.score);
    DOM.kpiCsatBar.style.width = `${r.csat.score}%`;
    DOM.kpiCsatMeta.textContent = `Meta ${formatPercent(META_CSAT)}`;

    renderNPSBar(nps);
    renderCSATBar(csat);

    const { nps_etapas: etapas } = h;
    DOM.insightHallazgos.innerHTML = `
      Actualmente, <strong>+${formatInteger(h.csat_pct)} %</strong> de estudiantes están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos, que es de <strong>+${formatInteger(h.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${h.nps_tipo}</strong>" a nivel global,
      pero <strong>${h.tendencia}</strong> conforme avanza la carrera:
      <strong>Inicial (${formatDecimal(etapas.Inicial || 0)})</strong> →
      <strong>Intermedio (${formatDecimal(etapas.Intermedio || 0)})</strong> →
      <strong>Avanzado (${formatDecimal(etapas.Avanzado || 0)})</strong>.
      Teniendo una diferencia de <strong>-${formatInteger(h.delta)}</strong> puntos en el ciclo de vida estudiantil.
    `;
  }

  function renderNPSBar(nps) {
    const total = nps.Promotores + nps.Pasivos + nps.Detractores;
    DOM.npsBar.innerHTML = `<div class="csat-bar-row">`
      + `<div class="csat-segment" style="width:${pct(nps.Promotores, total)}%; background:var(--gray-700);"
           data-label="Promotores (9-10)" data-value="${formatInteger(nps.Promotores)} (${formatPctDecimal(nps.Promotores, total)})"><span class="csat-label">${formatPctSimple(nps.Promotores, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(nps.Pasivos, total)}%; background:var(--gray-400);"
           data-label="Pasivos (7-8)" data-value="${formatInteger(nps.Pasivos)} (${formatPctDecimal(nps.Pasivos, total)})"><span class="csat-label">${formatPctSimple(nps.Pasivos, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(nps.Detractores, total)}%; background:var(--ulima-orange);"
           data-label="Detractores (0-6)" data-value="${formatInteger(nps.Detractores)} (${formatPctDecimal(nps.Detractores, total)})"><span class="csat-label">${formatPctSimple(nps.Detractores, total)}</span></div>`
      + `</div>`;
    DOM.npsLegend.innerHTML = `
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-700);"></div>Promotores: ${formatInteger(nps.Promotores)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--gray-400);"></div>Pasivos: ${formatInteger(nps.Pasivos)}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--ulima-orange);"></div>Detractores: ${formatInteger(nps.Detractores)}</div>
    `;
    addTooltipToSegments('#nps-bar .csat-segment');
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
    const total = labels.reduce((s, l) => s + (csat[l.key] || 0), 0);
    const visibleLabels = labels.filter((l) => csat[l.key] > 0);
    DOM.csatBar.innerHTML = `<div class="csat-bar-row">`
      + visibleLabels
        .map((l) => {
          const p = pct(csat[l.key], total);
          return `<div class="csat-segment" style="width:${p}%; background:${l.color};"
                data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})"><span class="csat-label">${formatPctSimple(csat[l.key], total)}</span></div>`;
        })
        .join('')
      + `</div>`;
    DOM.csatLegend.innerHTML = visibleLabels
      .map(
        (l) =>
          `<div class="legend-item"><div class="legend-dot" style="background:${l.color};"></div>${l.key}: ${formatInteger(csat[l.key])}</div>`,
      )
      .join('');
    addTooltipToSegments('#csat-bar .csat-segment');
    adjustSegmentLabels('#csat-bar');
  }

  // Mide cada segmento: si la etiqueta no cabe, muestra etiqueta externa encima
  function adjustSegmentLabels(target) {
    // target: CSS selector string or bar-row DOM element
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

    // Detect bar type
    const isDistBar = barRow.classList.contains('distribution-bar') || barRow.classList.contains('visibility-bar');
    const segSelector = isDistBar ? '.distribution-segment, .visibility-segment' : '.csat-segment';

    // Limpiar contenedores previos de etiquetas externas
    container.querySelectorAll('.csat-labels-above, .csat-labels-below').forEach(el => el.remove());

    // Restaurar visibilidad de etiquetas internas ocultadas en ejecuciones previas
    if (isDistBar) {
      barRow.querySelectorAll('.dist-label').forEach((lbl) => {
        if (lbl.style.visibility === 'hidden') lbl.style.removeProperty('visibility');
      });
    } else {
      barRow.querySelectorAll('.csat-label').forEach((lbl) => {
        if (lbl.style.visibility === 'hidden') lbl.style.removeProperty('visibility');
      });
    }

    const SAFETY_MARGIN = 16;
    const barWidth = barRow.offsetWidth;

    if (!barWidth) {
      barRow.addEventListener('animationend', function onEnd() {
        barRow.removeEventListener('animationend', onEnd);
        requestAnimationFrame(() => adjustSegmentLabels(target));
      }, { once: true });
      setTimeout(() => requestAnimationFrame(() => adjustSegmentLabels(target)), (C.ANIMATION_FALLBACK_MS ?? 1200));
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
      // For dist bars, get % from inline style (offsetWidth may be 0 for narrow segments)
      const segPct = isDistBar
        ? (parseFloat(seg.style.width) || 0) / 100
        : seg.offsetWidth / barWidth;
      const tooNarrow = isDistBar
        ? segPct < 0.015 // ~1.5% threshold for dist bars
        : seg.offsetWidth < (C.MIN_SEGMENT_WIDTH ?? 30);
      const tooSmall = segPct < (C.SEGMENT_EXTERNAL_LABEL_PCT ?? 0.02);
      // For dist bars, text is directly in the segment (no .csat-label span)
      const textContent = (seg.textContent || '').trim();
      const textOverflows = isDistBar
        ? (textContent.length * 8 + SAFETY_MARGIN > seg.offsetWidth) // rough estimate
        : (() => { const lbl = seg.querySelector('.csat-label'); return lbl ? lbl.scrollWidth + SAFETY_MARGIN > seg.offsetWidth : false; })();
      const selected = textOverflows || tooNarrow || tooSmall;
      // Skip zero-value segments; sub-1% only hidden in narrow distribution bars
      const numericValue = parseFloat(textContent);
      const belowThreshold = isDistBar && segPct < 0.01;
      const isZero = isDistBar ? (parseFloat(seg.style.width) || 0) === 0 : segPct < (C.SEGMENT_LABEL_HIDE_PCT ?? 0.005);
      if (isZero || numericValue === 0 || belowThreshold) {
        const lbl = isDistBar ? seg.querySelector('.dist-label') : seg.querySelector('.csat-label');
        if (lbl) lbl.style.visibility = 'hidden';
        return;
      }
      if (selected) smallSegs.push(seg);
    });

    if (!smallSegs.length) return;

    // Interleave: split segments between above and below the bar
    smallSegs.sort((a, b) => a.offsetWidth - b.offsetWidth);
    const aboveSegs = [];
    const belowSegs = [];
    smallSegs.forEach((seg, i) => {
      if (i % 2 === 0) aboveSegs.push(seg);
      else belowSegs.push(seg);
    });

    const ROW_H = 22;

    // Helper: create label wrapper
    function createLabelWrap(className) {
      const w = document.createElement('div');
      w.className = className;
      return w;
    }

    const wrapAbove = createLabelWrap('csat-labels-above');
    container.insertBefore(wrapAbove, barRow);

    // Always create both wrappers so the bar stays vertically centered
    // even when only one side has external labels
    const wrapBelow = createLabelWrap('csat-labels-below');
    container.appendChild(wrapBelow);

    // Precompute segment positions for dist bars
    let distCumulativePct = 0;
    const distSegOffsets = isDistBar ? [] : null;
    if (isDistBar) {
      barRow.querySelectorAll(segSelector).forEach((seg) => {
        const pct = parseFloat(seg.style.width) || 0;
        distSegOffsets.push({ seg, leftPct: distCumulativePct, pct });
        distCumulativePct += pct;
      });
    }

    // Helper: render labels for a group (above or below)
    function renderLabelGroup(segs, wrap, isBelow) {
      if (!segs.length) return;
      const rows = [];
      const assignments = [];
      const wrapLeft = wrap.getBoundingClientRect().left;

      segs.forEach((seg) => {
        let cx;
        if (isDistBar) {
          const info = distSegOffsets.find(d => d.seg === seg);
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
        // Hide internal label
        if (isDistBar) {
          const dl = seg.querySelector('.dist-label');
          if (dl) dl.style.visibility = 'hidden';
        } else {
          const lbl = seg.querySelector('.csat-label');
          if (lbl) lbl.style.visibility = 'hidden';
        }
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
          // Position close to bar: wrapper bottom - 4px gap - label height
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
          // Mirror below: line fills from label bottom to wrapper bottom (bar)
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

      // Both wrappers same height: symmetric above/below
      wrap.style.height = (totalRows * ROW_H + 4) + 'px';
    }

    renderLabelGroup(aboveSegs, wrapAbove, false);
    renderLabelGroup(belowSegs, wrapBelow, true);

    // Equalize wrapper heights: bar stays centered even with one-sided labels
    const hAbove = parseFloat(wrapAbove.style.height) || 0;
    const hBelow = parseFloat(wrapBelow.style.height) || 0;
    const maxH = Math.max(hAbove, hBelow);
    if (maxH > 0) {
      wrapAbove.style.height = maxH + 'px';
      wrapBelow.style.height = maxH + 'px';
    }
  }
  // ==================== SECCIÓN OPERATIVO ====================
  function dimensionAplica(rows, dimension) {
    return rows.some((r) => r.dimension === dimension && sumKeys(r, SAT_KEYS) > 0);
  }

  function renderTop3Bars(containerId, data) {
    const container = $(containerId);
    const fragment = document.createDocumentFragment();
    data.forEach((item, idx) => {
      const barClass = item.pct >= META_CSAT ? 'high' : item.pct >= 80 ? 'medium' : 'low';
      const barValueOutside = item.pct < 12;
      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label">${formatDimensionName(item.dim)}</div>
        <div class="bar-container">
          <div class="bar-fill animated ${barClass}" style="width:${item.pct}%; animation-delay:${idx * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${formatPercent(item.pct, 2)}</span>
          </div>
        </div>
      `;
      barItem.querySelector('.bar-container').addEventListener('mousemove', (e) => {
        const fac = $('filter-facultad-top3').value;
        const car = $('filter-carrera-top3').value;
        const cic = getSelectedValues($('filter-ciclo-top3'));
        const rows = filtrarDatos(cache.dimensiones, fac, car, cic).filter(
          (r) => r.dimension === item.dim,
        );
        const conteos = {
          'Totalmente satisfecho': 0,
          'Muy satisfecho': 0,
          Satisfecho: 0,
          Insatisfecho: 0,
          'Totalmente insatisfecho': 0,
          'No utilizo': 0,
          'No conozco': 0,
        };
        rows.forEach((r) =>
          Object.keys(conteos).forEach((k) => {
            conteos[k] += r[k] || 0;
          }),
        );
        const lines = Object.entries(conteos)
          .filter(([, v]) => v > 0)
          .map(([k, v]) => `${k}: ${formatInteger(v)}`);
        if (!lines.length) return hideTooltip();
        showTooltip(e, lines.join('<br>'));
      });
      barItem.querySelector('.bar-container').addEventListener('mouseleave', hideTooltip);
      fragment.appendChild(barItem);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  function updateTop3Filters() {
    const fac = $('filter-facultad-top3').value;
    const car = $('filter-carrera-top3').value;
    const cic = getSelectedValues($('filter-ciclo-top3'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const categorias = {
      academico: 'Académico',
      infraestructura: 'Infraestructura',
      tecnologia: 'Tecnología',
      adminBienestar: 'Administrativo y Bienestar',
    };
    const top3Data = {};
    Object.entries(categorias).forEach(([key, nombre]) => {
      const dims = {};
      filtered
        .filter((r) => r.categoria === nombre)
        .forEach((r) => {
          if (!dimensionAplica(filtered, r.dimension)) return;
          if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0 };
          dims[r.dimension].total += sumKeys(r, SAT_KEYS);
          dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
        });
      top3Data[key] = Object.entries(dims)
        .map(([dim, v]) => ({ dim, pct: v.total ? (v.top3 / v.total) * 100 : 0 }))
        .sort((a, b) => b.pct - a.pct);
    });
    renderTop3Bars('chart-academico', top3Data.academico);
    renderTop3Bars('chart-infraestructura', top3Data.infraestructura);
    renderTop3Bars('chart-tecnologia', top3Data.tecnologia);
    renderTop3Bars('chart-admin-bienestar', top3Data.adminBienestar);
  }

  // Gráfico radar
  function renderRadarIndependiente() {
    const fac = $('filter-facultad-radar').value;
    const car = $('filter-carrera-radar').value;
    const cic = getSelectedValues($('filter-ciclo-radar'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dims = {};
    filtered.forEach((r) => {
      if (!dimensionAplica(filtered, r.dimension)) return;
      if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0, categoria: r.categoria };
      dims[r.dimension].total += sumKeys(r, SAT_KEYS);
      dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
    });
    const allDims = Object.entries(dims)
      .filter(([, v]) => v.total > 0)
      .map(([dim, v]) => ({ dim, pct: (v.top3 / v.total) * 100, categoria: v.categoria }));

    if (!allDims.length) {
      DOM.radarChart.innerHTML = '<text x="300" y="250" text-anchor="middle">Sin datos</text>';
      updateInsightFortaleza([], fac, car, cic);
      return;
    }
    allDims.sort((a, b) => b.pct - a.pct);

    const cx = 300,
      cy = 250,
      maxR = 200;
    const n = allDims.length;
    const parts = [];
    [0.25, 0.5, 0.75, 1].forEach((f) =>
      parts.push(
        `<circle cx="${cx}" cy="${cy}" r="${maxR * f}" fill="none" stroke="#E5E7EB" stroke-width="1"/>`,
      ),
    );
    allDims.forEach((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x2 = cx + maxR * Math.cos(angle);
      const y2 = cy + maxR * Math.sin(angle);
      parts.push(
        `<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="#E5E7EB" stroke-width="1"/>`,
      );
      const lx = cx + (maxR + 26) * Math.cos(angle);
      const ly = cy + (maxR + 26) * Math.sin(angle);
      const anchor = angle > Math.PI / 2 || angle < -Math.PI / 2 ? 'end' : 'start';
      parts.push(`<text x="${lx}" y="${ly}" font-size="10" font-weight="500" fill="#6B7280" style="cursor:pointer;"
                  text-anchor="${anchor}" dominant-baseline="middle"
                  onmousemove="showTooltip(event,'${formatDimensionNameForAttr(d.dim)}: ${formatPercent(d.pct, 2)}')"
                  onmouseleave="hideTooltip()">${formatDimensionNameSVG(d.dim, 26)}</text>`);
    });
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
    parts.push(`<polygon points="${outer}" fill="rgba(55,65,81,0.18)" stroke="#374151" stroke-width="2">
      <animate attributeName="points" from="${outer}" to="${data}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
    </polygon>`);
    allDims.forEach((d, i) => {
      const a = (Math.PI * 2 * i) / n - Math.PI / 2;
      const rFinal = (d.pct / 100) * maxR;
      const ox = cx + maxR * Math.cos(a);
      const oy = cy + maxR * Math.sin(a);
      const px = cx + rFinal * Math.cos(a);
      const py = cy + rFinal * Math.sin(a);
      const color = d.pct >= META_CSAT ? '#374151' : d.pct >= 80 ? '#9CA3AF' : '#FF0000';
      parts.push(`<circle cx="${ox}" cy="${oy}" r="4" fill="${color}" style="cursor:pointer;opacity:0">
                  <animate attributeName="cx" from="${ox}" to="${px}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="cy" from="${oy}" to="${py}" dur="0.8s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
                  <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
                </circle>`);
    });
    DOM.radarChart.innerHTML = parts.join('');
    setTimeout(() => {
      DOM.radarChart.querySelectorAll('animate').forEach((a) => {
        try {
          a.beginElement();
        } catch {}
      });
    }, 10);
    updateInsightFortaleza(allDims, fac, car, cic);
  }

  function updateInsightFortaleza(allDims, fac, car, cic) {
    if (!DOM.insightFortaleza || !allDims.length) {
      if (DOM.insightFortaleza)
        DOM.insightFortaleza.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const fortalezas = allDims.filter((d) => d.pct >= META_CSAT).sort((a, b) => b.pct - a.pct);
    const adecuados = allDims
      .filter((d) => d.pct >= 80 && d.pct < META_CSAT)
      .sort((a, b) => b.pct - a.pct);
    const atencion = allDims.filter((d) => d.pct < 80).sort((a, b) => a.pct - b.pct);
    const hayFiltro = fac || car || cic;
    const contexto = hayFiltro ? [fac, car, cic].filter(Boolean).join(' · ') : '';
    const fmtP = (v) => formatPercent(v, 2);
    const fmtD = (d) => formatDimensionName(d);
    let txt = '';

    if (hayFiltro) {
      txt += `<strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">${contexto}</strong><br>`;
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
    DOM.insightFortaleza.innerHTML = txt;
  }

  // ==================== SECCIÓN ANALÍTICO ====================
  function renderPreguntas() {
    const fac = $('filter-facultad-preguntas').value;
    const car = $('filter-carrera-preguntas').value;
    const cic = getSelectedValues($('filter-ciclo-preguntas'));
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
      .map(([dim, v]) => {
        const total = v.totSat + v.muySat + v.sat + v.insat + v.totInsat;
        const top3 = v.totSat + v.muySat + v.sat;
        const p1 = total > 0 ? Math.round((v.totSat / total) * 100) : 0;
        const p2 = total > 0 ? Math.round((v.muySat / total) * 100) : 0;
        const p3 = total > 0 ? Math.round((v.sat / total) * 100) : 0;
        const p4 = total > 0 ? Math.round((v.insat / total) * 100) : 0;
        const p5 = total > 0 ? Math.max(0, 100 - p1 - p2 - p3 - p4) : 0;
        return {
          dimension: dim,
          categoria: v.categoria,
          top3box: total > 0 ? ((top3 / total) * 100).toFixed(2) : '0.00',
          totSat: v.totSat,
          muySat: v.muySat,
          sat: v.sat,
          insat: v.insat,
          totInsat: v.totInsat,
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
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const catCorta =
        item.categoria === 'Administrativo y Bienestar' ? 'Servicios' : item.categoria;
      const heatClass =
        parseFloat(item.top3box) >= META_CSAT
          ? 'heat-high'
          : parseFloat(item.top3box) >= 80
            ? 'heat-medium'
            : 'heat-low';
      tr.innerHTML = `
        <td>${formatDimensionName(item.dimension)}</td>
        <td class="text-center"><span class="heatmap-cell ${heatClass}">${formatPercent(parseFloat(item.top3box), 2)}</span></td>
        <td class="text-center">${catCorta}</td>
        <td>
          <div class="distribution-bar animated">
            <div class="distribution-segment" style="width:${item.pctTotSat}%;background:var(--gray-800);" data-label="Totalmente satisfecho" data-value="${formatInteger(item.totSat)}"><span class="dist-label">${item.pctTotSat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctMuySat}%;background:var(--gray-500);" data-label="Muy satisfecho" data-value="${formatInteger(item.muySat)}"><span class="dist-label">${item.pctMuySat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctSat}%;background:var(--gray-300);color:var(--gray-700);" data-label="Satisfecho" data-value="${formatInteger(item.sat)}"><span class="dist-label">${item.pctSat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctInsat}%;background:var(--ulima-orange);" data-label="Insatisfecho" data-value="${formatInteger(item.insat)}"><span class="dist-label">${item.pctInsat}%</span></div>
            <div class="distribution-segment" style="width:${item.pctTotInsat}%;background:var(--ulima-red);" data-label="Totalmente insatisfecho" data-value="${formatInteger(item.totInsat)}"><span class="dist-label">${item.pctTotInsat}%</span></div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.distribution-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) =>
          showTooltip(e, `${seg.dataset.label}: ${seg.dataset.value}`),
        );
        seg.addEventListener('mouseleave', hideTooltip);
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
    // External labels for narrow segments (may defer via animationend)
    tbody.querySelectorAll('.distribution-bar').forEach(bar => adjustSegmentLabels(bar));

    // Normalize row heights after all async animations complete (stackedGrow = 0.6s)
    setTimeout(() => {
      const aboveW = tbody.querySelectorAll('.csat-labels-above');
      const belowW = tbody.querySelectorAll('.csat-labels-below');
      let maxH = 0;
      aboveW.forEach(w => { const h = parseFloat(w.style.height) || 0; if (h > maxH) maxH = h; });
      belowW.forEach(w => { const h = parseFloat(w.style.height) || 0; if (h > maxH) maxH = h; });
      if (maxH > 0) {
        tbody.querySelectorAll('.distribution-bar').forEach(bar => {
          const td = bar.parentElement;
          let wa = td.querySelector('.csat-labels-above');
          let wb = td.querySelector('.csat-labels-below');
          if (!wa) { wa = document.createElement('div'); wa.className = 'csat-labels-above'; td.insertBefore(wa, bar); }
          if (!wb) { wb = document.createElement('div'); wb.className = 'csat-labels-below'; td.appendChild(wb); }
          wa.style.height = maxH + 'px';
          wb.style.height = maxH + 'px';
        });
      }
    }, 800);
  }

  function renderDetalleCarreras() {
    const fac = $('filter-facultad-detalle').value;
    const cic = getSelectedValues($('filter-ciclo-detalle'));
    const filteredIds = filtrarDatos(cache.ids, fac, null, cic);
    const conteo = {};
    filteredIds.forEach((r) => {
      conteo[r.carrera] = (conteo[r.carrera] || 0) + r.count;
    });

    const npsMap = {};
    filtrarDatos(cache.nps_ciclo_carrera, fac, null, cic).forEach((r) => {
      if (!npsMap[r.carrera]) npsMap[r.carrera] = { prom: 0, pas: 0, det: 0 };
      npsMap[r.carrera].prom += r.Promotores;
      npsMap[r.carrera].pas += r.Pasivos || 0;
      npsMap[r.carrera].det += r.Detractores;
    });

    const csatMap = {};
    filtrarDatos(cache.csat_ciclo_carrera, fac, null, cic).forEach((r) => {
      if (!csatMap[r.carrera]) csatMap[r.carrera] = { t3b: 0, total: 0 };
      const t3b = sumKeys(r, SAT_TOP3_KEYS);
      const total = t3b + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
      csatMap[r.carrera].t3b += t3b;
      csatMap[r.carrera].total += total;
    });

    let csatRef = csatScoreGlobal;
    let npsRef = 0;
    {
      let prom = 0;
      let pas = 0;
      let det = 0;
      Object.values(npsMap).forEach((v) => {
        prom += v.prom;
        pas += v.pas;
        det += v.det;
      });
      const total = prom + pas + det;
      npsRef = total > 0 ? ((prom - det) / total) * 100 : 0;
    }
    if (esEstudiosGen(fac)) {
      let tt = 0,
        tr = 0;
      Object.values(csatMap).forEach((v) => {
        tt += v.t3b;
        tr += v.total;
      });
      csatRef = tr > 0 ? (tt / tr) * 100 : csatScoreGlobal;
    }
    DOM.detallePromedioRef.textContent = `(${formatDecimal(csatRef, 2)} %)`;
    DOM.detallePromedioNpsRef.textContent = `(${formatDecimal(npsRef, 2)})`;

    const data = Object.entries(conteo)
      .map(([carrera, encuestas]) => {
        const nps = npsMap[carrera];
        const csat = csatMap[carrera];
        const npsT = nps ? nps.prom + nps.pas + nps.det : 0;
        const npsS = npsT > 0 ? ((nps.prom - nps.det) / npsT) * 100 : 0;
        const csatS = csat?.total > 0 ? (csat.t3b / csat.total) * 100 : 0;
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
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const vsCsatTxt =
        item.vsPromCsat >= 0
          ? `<span style="color:#00B04F;font-weight:600;">+${formatDecimal(item.vsPromCsat, 2)}</span>`
          : `<span style="color:#FF0000;font-weight:600;">${formatDecimal(item.vsPromCsat, 2)}</span>`;

      const vsNpsTxt =
        item.vsPromNps >= 0
          ? `<span style="color:#00B04F;font-weight:600;">+${formatDecimal(item.vsPromNps, 2)}</span>`
          : `<span style="color:#FF0000;font-weight:600;">${formatDecimal(item.vsPromNps, 2)}</span>`;

      tr.innerHTML = `
        <td>${item.carrera}</td>
        <td class="text-center">${formatInteger(item.encuestas)}</td>
        <td class="text-center" style="font-weight:700;">${formatPercent(item.csat, 2)}</td>
        <td class="text-center">${vsCsatTxt}</td>
        <td class="text-center" style="font-weight:700;">${formatDecimal(item.nps, 2)}</td>
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
    const cic = getSelectedValues($('filter-ciclo-visibilidad'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) dimMap[r.dimension] = { noConozco: 0, noUtilizo: 0, conoce: 0 };
      dimMap[r.dimension].noConozco += r['No conozco'] || 0;
      dimMap[r.dimension].noUtilizo += r['No utilizo'] || 0;
      dimMap[r.dimension].conoce += sumKeys(r, SAT_KEYS);
    });
    const data = Object.entries(dimMap)
      .filter(([, v]) => v.noConozco > 0 || v.noUtilizo > 0)
      .map(([dim, v]) => {
        const total = v.noConozco + v.noUtilizo + v.conoce;
        return {
          dimension: dim,
          noConozco: v.noConozco,
          noUtilizo: v.noUtilizo,
          conoce: v.conoce,
          pctNoConozco: total > 0 ? (v.noConozco / total) * 100 : 0,
          pctNoUtilizo: total > 0 ? (v.noUtilizo / total) * 100 : 0,
          pctConoce: total > 0 ? (v.conoce / total) * 100 : 0,
          total,
        };
      })
      .sort((a, b) => a.pctNoConozco + a.pctNoUtilizo - (b.pctNoConozco + b.pctNoUtilizo));

    const tbody = $('tbody-visibilidad');
    const fragment = document.createDocumentFragment();
    const fmtV = (v) => (v < 0 ? '' : Math.round(v) + '%');
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${formatDimensionName(item.dimension)}</td>
        <td class="text-center">${formatInteger(item.noConozco)} (${formatDecimal(item.pctNoConozco, 2)} %)</td>
        <td class="text-center">${formatInteger(item.noUtilizo)} (${formatDecimal(item.pctNoUtilizo, 2)} %)</td>
        <td>
          <div class="visibility-bar animated">
            <div class="visibility-segment no-conozco" style="width:${item.pctNoConozco}%;" data-label="No conozco" data-value="${formatInteger(item.noConozco)}">${fmtV(item.pctNoConozco)}</div>
            <div class="visibility-segment no-utilizo" style="width:${item.pctNoUtilizo}%;" data-label="No utilizo" data-value="${formatInteger(item.noUtilizo)}">${fmtV(item.pctNoUtilizo)}</div>
            <div class="visibility-segment conocido"   style="width:${item.pctConoce}%;"    data-label="Conozco/Utilizo" data-value="${formatInteger(item.conoce)}">${fmtV(item.pctConoce)}</div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.visibility-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) =>
          showTooltip(e, `${seg.dataset.label}: ${seg.dataset.value}`),
        );
        seg.addEventListener('mouseleave', hideTooltip);
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
    updateInsightAtencion(data, fac, car, cic);
  }

  function updateInsightAtencion(data, fac, car, cic) {
    if (!DOM.insightAtencion || !data.length) {
      if (DOM.insightAtencion)
        DOM.insightAtencion.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const sorted = [...data].sort(
      (a, b) => b.pctNoConozco + b.pctNoUtilizo - (a.pctNoConozco + a.pctNoUtilizo),
    );
    const criticos = sorted.filter((d) => d.pctNoConozco + d.pctNoUtilizo >= 50);
    const moderados = sorted.filter((d) => {
      const c = d.pctNoConozco + d.pctNoUtilizo;
      return c >= 25 && c < 50;
    });
    const hayFiltro = fac || car || cic;
    const contexto = hayFiltro ? [fac, car, cic].filter(Boolean).join(' · ') : '';
    const fmtP = (v) => formatDecimal(v, 2) + ' %';
    const fmtD = (d) => formatDimensionName(d);
    let txt = '';

    if (hayFiltro) {
      txt += `<strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">${contexto}</strong><br>`;
      if (criticos.length) {
        txt += `${criticos.length === 1 ? 'El servicio con <strong>menor visibilidad</strong> es' : 'Los servicios con <strong>menor visibilidad</strong> son'} `;
        txt += criticos
          .slice(0, 3)
          .map(
            (d) =>
              `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`,
          )
          .join(', ');
        txt += `. En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones tienen más del 50 % de desconocimiento o no uso.`;
      } else if (moderados.length) {
        txt += `No hay servicios con desconocimiento crítico (>50 %). Las dimensiones con mayor oportunidad son `;
        txt += moderados
          .slice(0, 2)
          .map(
            (d) =>
              `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`,
          )
          .join(' y ');
        txt += `.`;
      } else {
        txt += `Los servicios presentan niveles aceptables de visibilidad. Las dimensiones con mayor margen de mejora son `;
        txt += sorted
          .slice(0, 2)
          .map(
            (d) =>
              `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`,
          )
          .join(' y ');
        txt += `.`;
      }
    } else {
      if (sorted.length >= 2) {
        const [a, b] = sorted;
        txt += `<strong>${fmtD(a.dimension)}</strong> (${fmtP(a.pctNoConozco)} · No conozco + ${fmtP(a.pctNoUtilizo)} · No utilizo) y `;
        txt += `<strong>${fmtD(b.dimension)}</strong> (${fmtP(b.pctNoConozco)} · No conozco + ${fmtP(b.pctNoUtilizo)} · No utilizo) `;
        txt += `son las que presentan <strong>menor visibilidad</strong>.`;
        if (criticos.length)
          txt += ` En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones superan el 50 % de desconocimiento o no uso.`;
      } else if (sorted.length === 1) {
        const [a] = sorted;
        txt += `<strong>${fmtD(a.dimension)}</strong> (${fmtP(a.pctNoConozco)} · No conozco + ${fmtP(a.pctNoUtilizo)} · No utilizo) es la que presenta <strong>menor visibilidad</strong>.`;
      }
    }
    DOM.insightAtencion.innerHTML = txt;
  }

  // ==================== SECCIÓN SENTIMIENTO ====================
  function renderSentimiento() {
    const s = cache.sentimiento;
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;

    if (!s || !s.topicos || !s.topicos.length) {
      kpiGrid.innerHTML = `<p style="color:var(--gray-500);font-size:13px;">
        No hay datos de análisis semántico disponibles para este período.</p>`;
      return;
    }

    const r = s.resumen;
    kpiGrid.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-value" style="font-size:28px;">${r.total_analizados}</div>
        <div class="kpi-label">Comentarios analizados</div>
        <div class="kpi-meta">Pasivos + Detractores</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="font-size:28px;color:var(--ulima-orange);">${r.pasivos}</div>
        <div class="kpi-label" style="color:var(--ulima-orange);">Pasivos con comentario</div>
        <div class="kpi-meta">NPS 7–8</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="font-size:28px;color:var(--ulima-red);">${r.detractores}</div>
        <div class="kpi-label" style="color:var(--ulima-red);">Detractores con comentario</div>
        <div class="kpi-meta">NPS 0–6</div>
      </div>
    `;

    const temasContainer = $('temas-container');
    if (temasContainer) {
      const chips = s.topicos
        .map((t) => {
          const colorMap = {
            negativo: 'var(--ulima-red)',
            mejora: 'var(--ulima-orange)',
            positivo: 'var(--success-text)',
          };
          const color = colorMap[t.tipo] || 'var(--gray-600)';
          return `<span class="tema-chip" data-topico="${t.topico}" style="
          display:inline-flex;align-items:center;gap:6px;padding:6px 12px;
          border-radius:20px;border:1px solid ${color};color:${color};
          font-size:11px;font-weight:600;cursor:pointer;background:var(--white);
          transition:background 0.2s;">
          ${t.icono} ${t.topico} <span style="background:${color};color:white;border-radius:10px;padding:1px 6px;font-size:10px;">${t.total_comentarios}</span>
        </span>`;
        })
        .join('');
      temasContainer.innerHTML = chips;
    }

    renderInsightsCards();
    renderTablaSentimientoCarrera();
  }

  function colorPorTipo(tipo) {
    if (tipo === 'negativo')
      return { border: 'var(--ulima-red)', bg: '#FEF2F2', label: 'Insatisfacción' };
    if (tipo === 'positivo')
      return { border: 'var(--success-text)', bg: '#ECFDF5', label: 'Fortaleza reconocida' };
    return { border: 'var(--ulima-orange)', bg: '#FFF7ED', label: 'Oportunidad de mejora' };
  }

  function renderInsightsCards() {
    const container = $('insights-container');
    if (!container || !cache.sentimiento) return;

    const filtroTipo = $('filter-sentimiento')?.value || 'todos';
    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCarr = $('filter-carrera-sent')?.value || '';
    const filtroCiclo = getSelectedValues($('filter-ciclo-sent')) || '';

    let topicos = cache.sentimiento.topicos || [];

    if (filtroTipo !== 'todos') {
      topicos = topicos.filter((t) => t.tipo === filtroTipo);
    }

    if (filtroCarr) {
      topicos = topicos
        .map((t) => {
          const count = t.por_carrera[filtroCarr] || 0;
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
            ${frases.map((f) => `<li style="font-size:12px;color:var(--gray-700);margin-bottom:4px;line-height:1.5;">"${f}"</li>`).join('')}
           </ul>`
        : '';
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
          <div>
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;
              letter-spacing:0.5px;color:${colores.border};">${colores.label}</span>
            <h4 style="font-size:14px;font-weight:700;color:var(--gray-900);margin:4px 0;">${t.icono} ${t.topico}</h4>
          </div>
          <span style="background:${colores.border};color:white;border-radius:12px;
            padding:3px 10px;font-size:11px;font-weight:700;white-space:nowrap;">
            ${displayCount} comentario${displayCount !== 1 ? 's' : ''}
          </span>
        </div>
        ${frasesHTML}
      `;
      fragment.appendChild(card);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  function renderTablaSentimientoCarrera() {
    const tbody = $('tbody-sentimiento-carrera');
    if (!tbody || !cache.sentimiento) return;

    const filtroFac = $('filter-facultad-sent')?.value || '';
    const filtroCarr = $('filter-carrera-sent')?.value || '';

    let data = cache.sentimiento.por_carrera || [];

    if (filtroFac) data = data.filter((r) => r.facultad === filtroFac);
    if (filtroCarr) data = data.filter((r) => r.carrera === filtroCarr);

    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${item.carrera}</td>
        <td class="text-center">${item.total}</td>
        <td class="text-center" style="color:var(--ulima-orange);font-weight:600;">${item.pasivos}</td>
        <td class="text-center" style="color:var(--ulima-red);font-weight:600;">${item.detractores}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    const insightEl = $('insight-sentimiento');
    if (!insightEl || !data.length) return;
    const topCarrera = [...data].sort((a, b) => b.total - a.total)[0];
    const totalGlobal = data.reduce((s, r) => s + r.total, 0);
    const topicosCount = (cache.sentimiento.topicos || []).length;
    insightEl.innerHTML = `
      Se identificaron <strong>${topicosCount} temas</strong> en los comentarios de Pasivos y Detractores.
      ${
        topCarrera
          ? `La carrera con más comentarios es <strong>${topCarrera.carrera}</strong>
           (${topCarrera.total} de ${totalGlobal} total),
           con <strong>${topCarrera.detractores}</strong> de Detractores y
           <strong>${topCarrera.pasivos}</strong> de Pasivos.`
          : ''
      }
      Las frases representativas muestran el contexto real de cada preocupación estudiantil.
    `;
  }

  // ==================== CONFIGURACIÓN DE FILTROS ====================
  function setupFilters(prefix, onChangeCallback) {
    const selFac = $(`filter-facultad-${prefix}`);
    const selCar = $(`filter-carrera-${prefix}`);
    const selCic = $(`filter-ciclo-${prefix}`);
    if (!selFac) return;

    const { filtros } = cache;

    populateFacultadSelect(selFac, filtros);

    const updateCascade = () => {
      const facVal = getSelectedValues(selFac);
      if (selFac.__custom) selFac.__custom.update();
      if (selCar) {
        populateSelect(selCar, 'Todas las carreras', [...getCarrerasForFiltro(facVal)].sort());
        if (selCar.__custom) selCar.__custom.update();
      }
      const carVal = selCar?.value ?? '';
      if (selCic) {
        const ciclos = facVal || carVal ? getCiclosForFiltro(facVal, carVal) : filtros.ciclos;
        populateSelect(selCic, 'Todos los ciclos', ciclos, ciclos.map(formatCicloText));
        if (selCic.__multiselect) selCic.__multiselect.update();
      }
      onChangeCallback?.();
      syncFilterActiveState(selFac, selCar, selCic);
    };

    selFac.addEventListener('change', updateCascade);
    selCar?.addEventListener('change', updateCascade);
    selCic?.addEventListener('change', updateCascade);
    if (selFac && selFac.dataset.multiselect !== 'true' && !selFac.__custom) {
      selFac.__custom = createCustomSelectDropdown(selFac, updateCascade);
    }
    if (selCar && selCar.dataset.multiselect !== 'true' && !selCar.__custom) {
      selCar.__custom = createCustomSelectDropdown(selCar, updateCascade);
    }
    if (selCic?.dataset.multiselect === 'true') {
      selCic.multiple = true;
      selCic.__multiselect = createMultiselectDropdown(selCic, updateCascade);
    }

    $(`reset-${prefix}`)?.addEventListener('click', () => {
      selFac.__custom?.close();
      selCar?.__custom?.close();
      populateFacultadSelect(selFac, filtros);
      syncFacultadCustomUI(selFac, filtros.has_ciclo);
      if (selCar) {
        clearFilterSelect(selCar);
        populateSelect(selCar, 'Todas las carreras', [...filtros.carreras].sort());
        selCar.__custom?.update();
      }
      if (selCic?.multiple) {
        Array.from(selCic.options).forEach((opt) => {
          opt.selected = false;
        });
        selCic.__multiselect?.update();
      } else if (selCic) {
        clearFilterSelect(selCic);
      }
      updateCascade();
    });
    updateCascade();
  }

  function setupSentimientoFilters() {
    $('filter-sentimiento')?.addEventListener('change', () => {
      renderInsightsCards();
    });
    setupFilters('sent', () => {
      renderInsightsCards();
      renderTablaSentimientoCarrera();
    });
  }

  // ==================== BARRA DE PROGRESO ====================
  function setupProgressBar() {
    const _pb = window.SurveyProgressBar;
    if (_pb) {
      _pb.init();
      return;
    }
    // Fallback inline (compatibilidad backward)
    const navLinks = document.querySelectorAll('.nav-links a');
    const sections = ['ejecutivo', 'operativo', 'analitico', 'sentimiento']
      .map((id) => document.getElementById(id))
      .filter((el) => el && el.style.display !== 'none');

    const setActive = (id) => {
      navLinks.forEach((a) => a.classList.toggle('active', a.getAttribute('href') === `#${id}`));
    };
    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id);
        }),
      { threshold: 0.3 },
    );
    sections.forEach((s) => observer.observe(s));
    navLinks.forEach((a) => {
      a.addEventListener('click', () => setActive(a.getAttribute('href').slice(1)));
    });

    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
          const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          DOM.progressFill.style.width = `${(scrollTop / scrollHeight) * 100}%`;
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  // ==================== INICIALIZACIÓN ====================
  async function init() {
    if (!(await loadAllData())) {
      console.error('No se pudieron cargar los datos.');
      return;
    }

    const tieneDatosCualitativos =
      cache.sentimiento &&
      cache.sentimiento.resumen &&
      cache.sentimiento.resumen.total_con_comentario > 0 &&
      cache.sentimiento.topicos &&
      cache.sentimiento.topicos.length > 0;

    // Si la encuesta no tiene columna Ciclo (ej: graduados, egresados),
    // ocultar todos los filtros de ciclo en el DOM.
    // Si la encuesta no tiene columna Ciclo, ocultar el grupo de filtro de ciclo
    // y redistribuir el espacio a los filtros de facultad y carrera
    if (!cache.filtros.has_ciclo) {
      document.querySelectorAll('.filter-ciclo-actions').forEach((el) => {
        const grp = el.querySelector('.filter-group');
        if (grp) grp.style.display = 'none';
        el.style.flex = 'none';
      });
    }

    if (!tieneDatosCualitativos) {
      // Ocultar sección del DOM
      const secSentimiento = document.getElementById('sentimiento');
      if (secSentimiento) {
        secSentimiento.style.display = 'none';
      }
      // Ocultar enlace de navegación en header
      const navLinkSentimiento = document.querySelector('.nav-links a[href="#sentimiento"]');
      if (navLinkSentimiento) {
        const liSentimiento = navLinkSentimiento.closest('li');
        if (liSentimiento) {
          liSentimiento.style.display = 'none';
        } else {
          navLinkSentimiento.style.display = 'none';
        }
      }
    }

    renderEjecutivo();
    setupFilters('top3', updateTop3Filters);
    setupFilters('radar', renderRadarIndependiente);
    setupFilters('preguntas', renderPreguntas);
    setupFilters('detalle', renderDetalleCarreras);
    setupFilters('visibilidad', renderVisibilidad);

    if (tieneDatosCualitativos) {
      renderSentimiento();
      setupSentimientoFilters();
    }

    setupProgressBar();

    // Re-ajustar etiquetas externas al redimensionar la ventana
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        adjustSegmentLabels('#nps-bar');
        adjustSegmentLabels('#csat-bar');
        document.querySelectorAll('.distribution-bar').forEach(bar => adjustSegmentLabels(bar));
      }, 250);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
