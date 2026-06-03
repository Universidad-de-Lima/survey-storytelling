/**
 * SURVEY MULTISELECT — Dropdown de selección múltiple con checkboxes.
 *
 * Reemplaza un <select multiple> nativo por un dropdown visual con:
 * - Checkboxes para selección múltiple
 * - Botón muestra conteo ("3 ciclos seleccionados")
 * - Cierre al hacer click fuera
 * - ARIA attributes para accesibilidad
 *
 * Extraído de dashboard.js (v2.0). Sin dependencias externas.
 *
 * @module components/multiselect
 * @version 1.0.0
 */
window.SurveyMultiselect = (() => {
  'use strict';

  // ── Utilidades internas (self-contained) ──

  function getSelectedValues(sel) {
    if (!sel) return '';
    if (sel.multiple) {
      const vals = Array.from(sel.selectedOptions).map((opt) => opt.value).filter(Boolean);
      return vals.length ? vals : '';
    }
    const opt = sel.options[sel.selectedIndex];
    return opt ? opt.value : '';
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
    if (values.length === 1) return values[0];
    return `${values.length} ciclos seleccionados`;
  }

  // ── Factory ──

  /**
   * Crea un dropdown multiselect que reemplaza visualmente un <select multiple>.
   *
   * @param {HTMLSelectElement} selCic - El elemento <select multiple> original
   * @param {Function} [onChangeCallback] - Callback opcional al cambiar selección
   * @returns {HTMLElement} El elemento wrapper (tiene método .update())
   */
  function create(selCic, onChangeCallback) {
    if (!selCic) return null;

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
          if (onChangeCallback) onChangeCallback();
        });
        const span = document.createElement('span');
        span.textContent = opt.textContent || opt.value;
        item.appendChild(checkbox);
        item.appendChild(span);
        panel.appendChild(item);
      });
      const anySelected =
        Array.from(panel.querySelectorAll('input[type="checkbox"]:checked')).length > 0;
      button.classList.toggle('filter-active', anySelected);
    };

    const openPanel = () => {
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      wrapper.classList.add('open');
      button.classList.add('filter-active');
      selCic.classList.add('filter-active');
    };

    const closePanel = () => {
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      wrapper.classList.remove('open');
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

    // Ocultar el select original (accesible para screen readers, invisible visualmente)
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
  }

  return { create };
})();
