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

  // ── ▼ MÁS overflow (shared logic for surveys + periods) ──
  function createOverflowSystem(container, itemSelector, btnClass, panelClass, itemClass, gap) {
    let busy = false, pending = false, timer = null;
    let moreBtn = null, morePanel = null, hiddenItems = [];

    function init() {
      if (!container || busy) return;
      const items = Array.from(container.querySelectorAll(itemSelector));
      if (items.length < 2) return;
      busy = true;

      // Cleanup
      if (moreBtn) { moreBtn.remove(); moreBtn = null; }
      if (morePanel) { morePanel.remove(); morePanel = null; }
      hiddenItems = [];

      items.forEach(el => { el.style.display = ''; });

      const cw = container.clientWidth;
      if (!items.some(el => el.offsetWidth > 0) || cw === 0) {
        busy = false;
        schedule();
        return;
      }

      const total = items.reduce((s, el, i) => s + el.offsetWidth + (i > 0 ? gap : 0), 0);
      if (total <= cw) { busy = false; return; }

      const temp = document.createElement('button');
      temp.className = btnClass;
      temp.textContent = '▼ MÁS';
      temp.style.cssText = 'position:absolute;visibility:hidden';
      container.appendChild(temp);
      const moreW = temp.offsetWidth || 85;
      temp.remove();

      let used = 0, count = 0;
      for (let i = 0; i < items.length; i++) {
        const w = items[i].offsetWidth;
        const g = count > 0 ? gap : 0;
        const need = (i < items.length - 1) ? gap + moreW : 0;
        if (used + g + w + need <= cw) { used += g + w; count++; }
        else break;
      }
      if (count < 1) count = 1;
      if (count >= items.length) count = items.length - 1;

      for (let i = count; i < items.length; i++) {
        items[i].style.display = 'none';
        hiddenItems.push(items[i]);
      }

      moreBtn = document.createElement('button');
      moreBtn.className = btnClass;
      moreBtn.textContent = '▼ MÁS';
      moreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (morePanel && !morePanel.hidden) close();
        else open();
      });
      container.appendChild(moreBtn);

      morePanel = document.createElement('div');
      morePanel.className = panelClass;
      morePanel.hidden = true;
      morePanel.setAttribute('role', 'listbox');

      const parent = container.parentElement;
      if (parent && getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
      }
      parent.appendChild(morePanel);

      hiddenItems.forEach(el => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = itemClass;
        item.textContent = el.textContent.replace('nuevo', '').trim();
        if (el.classList.contains('active')) item.classList.add('active');
        if (el.disabled) item.disabled = true;
        item.addEventListener('click', () => { el.click(); close(); });
        morePanel.appendChild(item);
      });

      busy = false;
      if (pending) { pending = false; init(); }
    }

    function open() {
      if (!morePanel || !moreBtn) return;
      morePanel.hidden = false;
      moreBtn.classList.add('open');
    }

    function close() {
      if (!morePanel || !moreBtn) return;
      morePanel.hidden = true;
      moreBtn.classList.remove('open');
    }

    function schedule() {
      if (busy) { pending = true; return; }
      clearTimeout(timer);
      timer = setTimeout(init, 100);
    }

    // Outside click
    document.addEventListener('click', (e) => {
      if (morePanel && !morePanel.hidden && !morePanel.contains(e.target) && e.target !== moreBtn) {
        close();
      }
    });

    // ResizeObserver
    if (window.ResizeObserver) {
      new ResizeObserver(() => schedule()).observe(container);
    }

    return { init, schedule, open, close };
  }

  // Survey overflow
  const surveyOverflow = tabsEl ? createOverflowSystem(
    tabsEl, '.survey-tab', 'survey-more-btn', 'survey-more-panel', 'survey-more-item', 4
  ) : null;

  // Period overflow
  const periodOverflow = pillsEl ? createOverflowSystem(
    pillsEl, '.pill', 'survey-more-btn', 'survey-more-panel', 'survey-more-item', 6
  ) : null;

  window.addEventListener('resize', () => {
    if (surveyOverflow) surveyOverflow.schedule();
    if (periodOverflow) periodOverflow.schedule();
  });

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
    if (periodOverflow) periodOverflow.schedule();

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
  selectSurvey('undergraduate').then(() => {
    if (surveyOverflow) surveyOverflow.schedule();
  });
})();
