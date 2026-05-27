(() => {
  'use strict';

  let PERIODS       = [];
  let currentPeriod = null;

  const pillsEl  = document.getElementById('pills-container');
  const selectEl = document.getElementById('period-select');
  const frame    = document.getElementById('dashboard-frame');
  const overlay  = document.getElementById('overlay');
  const ovMsg    = document.getElementById('overlay-msg');
  const splash   = document.getElementById('splash');

  function showLoaderError(message, error) {
    if (error) console.error(message, error);
    if (ovMsg) ovMsg.textContent = message;
    overlay?.classList.add('show');
    frame?.classList.remove('loaded');
  }

  function normalizePeriods(rawPeriods) {
    if (!Array.isArray(rawPeriods)) return [];

    return rawPeriods
      .filter(p => p && typeof p.id === 'string' && p.id.trim())
      .map(p => ({
        ...p,
        id: p.id.trim(),
        label: typeof p.label === 'string' && p.label.trim() ? p.label.trim() : p.id.trim(),
        url: p.url || `./${p.id.trim()}/index.html`
      }));
  }

  async function initPeriods() {
    try {
      const res = await fetch('./periodos.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      PERIODS = normalizePeriods(await res.json());
      if (!PERIODS.length) throw new Error('periodos.json no contiene periodos validos');
    } catch (err) {
      showLoaderError('Error al cargar periodos.', err);
      return;
    }

    currentPeriod = PERIODS[PERIODS.length - 1].id;

    PERIODS.forEach(p => {
      const btn = document.createElement('button');
      btn.className  = 'pill' + (p.id === currentPeriod ? ' active' : '');
      btn.dataset.id = p.id;
      btn.type       = 'button';
      btn.textContent = p.label;
      if (p.isNew) {
        const badge = document.createElement('span');
        badge.className   = 'pill-badge';
        badge.textContent = 'nuevo';
        btn.appendChild(badge);
      }
      btn.addEventListener('click', () => loadPeriod(p.id));
      pillsEl?.appendChild(btn);

      const opt       = document.createElement('option');
      opt.value       = p.id;
      opt.textContent = p.label + (p.isNew ? ' ★' : '');
      if (p.id === currentPeriod) opt.selected = true;
      selectEl?.appendChild(opt);
    });

    const initial = PERIODS.find(p => p.id === currentPeriod);
    if (!initial) {
      showLoaderError('No se encontro el periodo inicial.');
      return;
    }

    ovMsg.textContent = `Cargando periodo ${initial.label}...`;
    overlay.classList.add('show');
    frame.src = initial.url;
  }

  function loadPeriod(id) {
    if (id === currentPeriod) return;

    const p = PERIODS.find(x => x.id === id);
    if (!p) {
      showLoaderError('No se encontro el periodo seleccionado.');
      return;
    }

    currentPeriod = id;

    document.querySelectorAll('.pill').forEach(b => {
      b.classList.toggle('active', b.dataset.id === id);
    });
    if (selectEl) selectEl.value = id;

    ovMsg.textContent = `Cargando periodo ${p.label}...`;
    overlay.classList.add('show');
    frame.classList.remove('loaded');
    frame.src = p.url;
  }

  window.loadPeriod = loadPeriod;

  frame?.addEventListener('load', () => {
    overlay?.classList.remove('show');
    frame.classList.add('loaded');
  });

  window.addEventListener('load', () => {
    setTimeout(() => {
      splash?.classList.add('hide');
      setTimeout(() => splash?.remove(), 900);
    }, 1200);
  });

  initPeriods();
})();
