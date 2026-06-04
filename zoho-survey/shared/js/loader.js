(() => {
  'use strict';

  // ── Configuración del loader ──
  const LOADER_CONFIG = {
    PERIODS_FILE: 'periodos.json',
    FALLBACK_PAGE: 'underconstruction.html',
    SPLASH_DELAY_MS: 1200,
    SPLASH_FADE_MS: 900,
  };

  const SURVEY_TYPES = [
    { id: 'undergraduate', label: 'ESTUDIANTES PREGRADO', path: 'students/undergraduate' },
    { id: 'graduate', label: 'GRADUADOS PREGRADO', path: 'students/graduate' },
    { id: 'posgraduate', label: 'ESTUDIANTES POSGRADO', path: 'students/posgraduate' },
    { id: 'alumni-ug', label: 'EGRESADOS PREGRADO', path: 'alumni/undergraduate' },
    { id: 'alumni-pg', label: 'EGRESADOS POSGRADO', path: 'alumni/posgraduate' },
    { id: 'faculty-ug', label: 'DOCENTES PREGRADO', path: 'facultyStaff/undergraduate' },
    { id: 'faculty-pg', label: 'DOCENTES POSGRADO', path: 'facultyStaff/posgraduate' },
    { id: 'nonfaculty', label: 'NO DOCENTES', path: 'nonfacultyStaff' },
    { id: 'employers', label: 'EMPLEADORES', path: 'employers' },
  ];

  let currentSurvey = null;
  let currentPeriod = null;
  let PERIODS = [];
  let _initializing = true;

  const tabsEl = document.getElementById('survey-tabs');
  const surveySelect = document.getElementById('survey-select');
  const pillsEl = document.getElementById('pills-container');
  const periodSelect = document.getElementById('period-select');
  const periodBar = document.getElementById('period-bar');
  const frame = document.getElementById('dashboard-frame');
  const overlay = document.getElementById('overlay');
  const ovMsg = document.getElementById('overlay-msg');
  const splash = document.getElementById('splash');

  // ── Render survey tabs ──
  SURVEY_TYPES.forEach((s, i) => {
    // Desktop tab
    const btn = document.createElement('button');
    btn.className = 'survey-tab' + (i === 0 ? ' active' : '');
    btn.textContent = s.label;
    btn.disabled = !s.path;
    btn.addEventListener('click', () => selectSurvey(s.id));
    tabsEl?.appendChild(btn);

    // Mobile select option
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.label;
    opt.disabled = !s.path;
    if (i === 0) opt.selected = true;
    surveySelect?.appendChild(opt);
  });

  surveySelect?.addEventListener('change', (e) => selectSurvey(e.target.value));

  // Init custom selects for mobile (after options populated)
  if (window.SurveyCustomSelect) {
    surveySelect._customSelect = SurveyCustomSelect.create(surveySelect);
  }

  // ── ▼ MÁS overflow dropdown ──
  let moreBtn = null;
  let morePanel = null;
  let hiddenTabs = [];
  let _overflowBusy = false;
  let _overflowPending = false;

  function initMoreOverflow() {
    if (!tabsEl || _overflowBusy) return;
    const tabs = Array.from(tabsEl.querySelectorAll('.survey-tab'));
    if (tabs.length < 2) return;

    _overflowBusy = true;

    // Cleanup previous
    if (moreBtn) { moreBtn.remove(); moreBtn = null; }
    if (morePanel) { morePanel.remove(); morePanel = null; }
    hiddenTabs = [];

    // Show all tabs temporarily to measure real widths
    tabs.forEach(t => { t.style.display = ''; });

    const containerWidth = tabsEl.clientWidth;
    const gap = 4; // CSS gap between tabs

    // Guard: if tabs haven't been laid out yet, retry later
    const hasWidth = tabs.some(t => t.offsetWidth > 0);
    if (!hasWidth || containerWidth === 0) {
      _overflowBusy = false;
      scheduleOverflowCheck();
      return;
    }

    // Check if all tabs fit without ▼ MÁS
    const totalWidth = tabs.reduce((sum, t, i) => sum + t.offsetWidth + (i > 0 ? gap : 0), 0);
    if (totalWidth <= containerWidth) {
      _overflowBusy = false;
      return; // All fit — nothing to do
    }

    // Calculate how many tabs fit + ▼ MÁS button
    // Create a temporary button to measure its real width
    const tempBtn = document.createElement('button');
    tempBtn.className = 'survey-more-btn';
    tempBtn.textContent = '▼ MÁS';
    tempBtn.style.position = 'absolute';
    tempBtn.style.visibility = 'hidden';
    tabsEl.appendChild(tempBtn);
    const moreBtnWidth = tempBtn.offsetWidth || 85; // fallback if measurement fails
    tempBtn.remove();

    let usedWidth = 0;
    let visibleCount = 0;

    for (let i = 0; i < tabs.length; i++) {
      const tabWidth = tabs[i].offsetWidth;
      const addGap = visibleCount > 0 ? gap : 0;
      const isLastVisible = (i === tabs.length - 1);
      // If this is the last tab we'd show, we also need space for ▼ MÁS
      const needMoreSpace = !isLastVisible ? gap + moreBtnWidth : 0;

      if (usedWidth + addGap + tabWidth + needMoreSpace <= containerWidth) {
        usedWidth += addGap + tabWidth;
        visibleCount++;
      } else {
        break;
      }
    }

    // Safety: at least 1 visible tab
    if (visibleCount < 1) visibleCount = 1;
    // If we somehow marked all as visible but they don't fit, hide the last one
    if (visibleCount >= tabs.length) visibleCount = tabs.length - 1;

    // Hide overflow tabs
    for (let i = visibleCount; i < tabs.length; i++) {
      tabs[i].style.display = 'none';
      hiddenTabs.push(tabs[i]);
    }

    // Create ▼ MÁS button
    moreBtn = document.createElement('button');
    moreBtn.className = 'survey-more-btn';
    moreBtn.textContent = '▼ MÁS';
    moreBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMorePanel();
    });
    tabsEl.appendChild(moreBtn);

    // Create dropdown panel
    morePanel = document.createElement('div');
    morePanel.className = 'survey-more-panel';
    morePanel.hidden = true;
    morePanel.setAttribute('role', 'listbox');

    // Make parent relative for absolute positioning
    const barLeft = tabsEl.parentElement;
    if (barLeft && window.getComputedStyle(barLeft).position === 'static') {
      barLeft.style.position = 'relative';
    }
    barLeft.appendChild(morePanel);

    // Populate panel
    hiddenTabs.forEach(t => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'survey-more-item';
      item.textContent = t.textContent;
      if (t.classList.contains('active')) item.classList.add('active');
      if (t.disabled) item.disabled = true;
      item.addEventListener('click', () => {
        t.click(); // trigger original tab click
        closeMorePanel();
      });
      morePanel.appendChild(item);
    });

    _overflowBusy = false;
    if (_overflowPending) {
      _overflowPending = false;
      initMoreOverflow();
    }
  }

  function toggleMorePanel() {
    if (!morePanel) return;
    if (morePanel.hidden) openMorePanel();
    else closeMorePanel();
  }

  function openMorePanel() {
    if (!morePanel || !moreBtn) return;
    morePanel.hidden = false;
    moreBtn.classList.add('open');
  }

  function closeMorePanel() {
    if (!morePanel || !moreBtn) return;
    morePanel.hidden = true;
    moreBtn.classList.remove('open');
  }

  // Close panel on outside click
  document.addEventListener('click', (e) => {
    if (morePanel && !morePanel.hidden) {
      if (!morePanel.contains(e.target) && e.target !== moreBtn) {
        closeMorePanel();
      }
    }
  });

  // Run overflow detection after tabs render + on resize (debounced)
  let _overflowTimer = null;
  function scheduleOverflowCheck() {
    if (_overflowBusy) {
      _overflowPending = true;
      return;
    }
    clearTimeout(_overflowTimer);
    _overflowTimer = setTimeout(() => initMoreOverflow(), 100);
  }

  // Observe resize
  if (tabsEl && window.ResizeObserver) {
    const ro = new ResizeObserver(() => scheduleOverflowCheck());
    ro.observe(tabsEl);
  }
  window.addEventListener('resize', () => scheduleOverflowCheck());

  // ── ▼ MÁS overflow for periods ──
  let periodMoreBtn = null;
  let periodMorePanel = null;
  let hiddenPills = [];
  let _periodOverflowBusy = false;

  function initPeriodOverflow() {
    if (!pillsEl || _periodOverflowBusy) return;
    const pills = Array.from(pillsEl.querySelectorAll('.pill'));
    if (pills.length < 2) return;

    _periodOverflowBusy = true;

    // Cleanup
    if (periodMoreBtn) { periodMoreBtn.remove(); periodMoreBtn = null; }
    if (periodMorePanel) { periodMorePanel.remove(); periodMorePanel = null; }
    hiddenPills = [];

    // Show all
    pills.forEach(p => { p.style.display = ''; });

    const containerWidth = pillsEl.clientWidth;
    if (containerWidth === 0) { _periodOverflowBusy = false; return; }

    const gap = 6;
    const totalWidth = pills.reduce((sum, p, i) => sum + p.offsetWidth + (i > 0 ? gap : 0), 0);
    if (totalWidth <= containerWidth) { _periodOverflowBusy = false; return; }

    // Measure ▼ MÁS button
    const tempBtn = document.createElement('button');
    tempBtn.className = 'survey-more-btn';
    tempBtn.textContent = '▼ MÁS';
    tempBtn.style.position = 'absolute';
    tempBtn.style.visibility = 'hidden';
    pillsEl.appendChild(tempBtn);
    const moreW = tempBtn.offsetWidth || 85;
    tempBtn.remove();

    let used = 0;
    let count = 0;
    for (let i = 0; i < pills.length; i++) {
      const pw = pills[i].offsetWidth;
      const addGap = count > 0 ? gap : 0;
      const needMore = (i < pills.length - 1) ? gap + moreW : 0;
      if (used + addGap + pw + needMore <= containerWidth) {
        used += addGap + pw;
        count++;
      } else { break; }
    }
    if (count < 1) count = 1;
    if (count >= pills.length) count = pills.length - 1;

    for (let i = count; i < pills.length; i++) {
      pills[i].style.display = 'none';
      hiddenPills.push(pills[i]);
    }

    periodMoreBtn = document.createElement('button');
    periodMoreBtn.className = 'survey-more-btn';
    periodMoreBtn.textContent = '▼ MÁS';
    periodMoreBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (periodMorePanel && !periodMorePanel.hidden) {
        periodMorePanel.hidden = true;
        periodMoreBtn.classList.remove('open');
      } else {
        if (periodMorePanel) periodMorePanel.hidden = false;
        periodMoreBtn.classList.add('open');
      }
    });
    pillsEl.appendChild(periodMoreBtn);

    periodMorePanel = document.createElement('div');
    periodMorePanel.className = 'survey-more-panel';
    periodMorePanel.hidden = true;
    periodMorePanel.setAttribute('role', 'listbox');
    periodMorePanel.style.right = 'auto';
    periodMorePanel.style.left = '0';
    const bar = pillsEl.parentElement;
    if (bar && window.getComputedStyle(bar).position === 'static') {
      bar.style.position = 'relative';
    }
    bar.appendChild(periodMorePanel);

    hiddenPills.forEach(p => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'survey-more-item';
      item.textContent = p.textContent.replace('nuevo', '').trim();
      if (p.classList.contains('active')) item.classList.add('active');
      item.addEventListener('click', () => {
        p.click();
        if (periodMorePanel) periodMorePanel.hidden = true;
        if (periodMoreBtn) periodMoreBtn.classList.remove('open');
      });
      periodMorePanel.appendChild(item);
    });

    _periodOverflowBusy = false;
  }

  // Close period panel on outside click
  document.addEventListener('click', (e) => {
    if (periodMorePanel && !periodMorePanel.hidden) {
      if (!periodMorePanel.contains(e.target) && e.target !== periodMoreBtn) {
        periodMorePanel.hidden = true;
        if (periodMoreBtn) periodMoreBtn.classList.remove('open');
      }
    }
  });

  function schedulePeriodOverflow() {
    if (_periodOverflowBusy) return;
    setTimeout(() => initPeriodOverflow(), 100);
  }

  if (pillsEl && window.ResizeObserver) {
    const pro = new ResizeObserver(() => schedulePeriodOverflow());
    pro.observe(pillsEl);
  }

  // ── Select survey type ──
  async function selectSurvey(id) {
    const survey = SURVEY_TYPES.find((s) => s.id === id);
    if (!survey || !survey.path) return;
    if (!_initializing && survey.id === currentSurvey?.id) return;
    _initializing = false;

    currentSurvey = survey;
    currentPeriod = null;

    // Update tabs
    document.querySelectorAll('.survey-tab').forEach((b) => {
      b.classList.toggle('active', b.textContent === survey.label);
    });
    if (surveySelect) surveySelect.value = survey.id;

    // Fetch periods
    try {
      const res = await fetch(`${survey.path}/${LOADER_CONFIG.PERIODS_FILE}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      PERIODS = normalizePeriods(await res.json());
    } catch (err) {
      showLoaderError(`Sin datos para ${survey.label}`, err);
      periodBar.classList.remove('visible');
      // Load "en construcción" page
      frame.src = LOADER_CONFIG.FALLBACK_PAGE;
      overlay?.classList.remove('show');
      frame.classList.add('loaded');
      return;
    }

    // Show period bar
    periodBar.classList.add('visible');
    renderPeriods();
    schedulePeriodOverflow();

    // Load latest period
    const latest = PERIODS[0];
    if (latest) loadPeriod(latest.id);
  }

  // ── Normalize periods ──
  function normalizePeriods(raw) {
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((p) => p && typeof p.id === 'string' && p.id.trim())
      .map((p) => ({
        ...p,
        id: p.id.trim(),
        label: p.label || p.id,
        url: p.url || `${currentSurvey.path}/${p.id.trim()}/index.html`,
      }))
      .reverse();
  }

  // ── Render period pills ──
  function renderPeriods() {
    pillsEl.innerHTML = '';
    periodSelect.innerHTML = '';

    PERIODS.forEach((p) => {
      const btn = document.createElement('button');
      btn.className = 'pill' + (p.id === currentPeriod ? ' active' : '');
      btn.dataset.id = p.id;
      btn.textContent = p.label;
      if (p.isNew) {
        const badge = document.createElement('span');
        badge.className = 'pill-badge';
        badge.textContent = 'nuevo';
        btn.appendChild(badge);
      }
      btn.addEventListener('click', () => loadPeriod(p.id));
      pillsEl?.appendChild(btn);

      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.label + (p.isNew ? ' ★' : '');
      if (p.id === currentPeriod) opt.selected = true;
      periodSelect?.appendChild(opt);
    });

    // Update/recreate custom select for mobile
    if (periodSelect._customSelect) {
      periodSelect._customSelect.update();
    } else if (window.SurveyCustomSelect) {
      periodSelect._customSelect = SurveyCustomSelect.create(periodSelect);
    }
  }

  // ── Load period ──
  function loadPeriod(id) {
    const p = PERIODS.find((x) => x.id === id);
    if (!p || id === currentPeriod) return;

    currentPeriod = id;

    document.querySelectorAll('.pill').forEach((b) => {
      b.classList.toggle('active', b.dataset.id === p.id);
    });
    if (periodSelect) periodSelect.value = id;

    ovMsg.textContent = `Cargando ${p.label}...`;
    overlay?.classList.add('show');
    frame?.classList.remove('loaded');
    frame.src = p.url;
  }

  periodSelect?.addEventListener('change', (e) => loadPeriod(e.target.value));

  // ── Helpers ──
  function showLoaderError(msg, err) {
    if (err) console.error(msg, err);
    if (ovMsg) ovMsg.textContent = msg;
    overlay?.classList.add('show');
    frame?.classList.remove('loaded');
  }

  window.selectSurvey = selectSurvey;
  window.loadPeriod = loadPeriod;

  // ── Events ──
  frame?.addEventListener('load', () => {
    overlay?.classList.remove('show');
    frame.classList.add('loaded');
  });

  window.addEventListener('load', () => {
    setTimeout(() => {
      splash?.classList.add('hide');
      setTimeout(() => splash?.remove(), LOADER_CONFIG.SPLASH_FADE_MS);
    }, LOADER_CONFIG.SPLASH_DELAY_MS);
  });

  // ── Init ──
  selectSurvey('undergraduate').then(() => scheduleOverflowCheck());
})();
