/**
 * SURVEY SANITIZER — Funciones de sanitización HTML.
 * 
 * Previene XSS en contenido dinámico insertado vía innerHTML.
 * Extraído de dashboard.js (v2.0). Sin dependencias externas.
 * 
 * @module utils/sanitizer
 * @version 1.0.0
 */
window.SurveySanitizer = (() => {
  'use strict';

  /**
   * Escapa caracteres HTML peligrosos.
   * @param {string} str - Texto a escapar
   * @returns {string} Texto seguro para insertar en HTML
   */
  const escapeHTML = (str) => {
    if (!str || typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  /**
   * Sanitiza HTML permitiendo solo una whitelist mínima de tags.
   * Tags permitidos: <br>, <strong>, <em>, <i>, <span> (sin atributos on*).
   * @param {string} html - HTML potencialmente inseguro
   * @returns {string} HTML sanitizado
   */
  const sanitizeHTML = (html) => {
    if (!html || typeof html !== 'string') return '';
    const allowedTags = ['br', 'strong', 'em', 'i', 'span'];
    // 1. Escapar todo
    let safe = escapeHTML(html);
    // 2. Restaurar tags permitidos (escapados a &lt; y &gt;)
    allowedTags.forEach((tag) => {
      const openEscaped = `&lt;${tag}&gt;`;
      const openReal = `<${tag}>`;
      const closeEscaped = `&lt;/${tag}&gt;`;
      const closeReal = `</${tag}>`;
      safe = safe.split(openEscaped).join(openReal);
      safe = safe.split(closeEscaped).join(closeReal);
    });
    // 3. Remover atributos on* remanentes
    safe = safe.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, '');
    safe = safe.replace(/\s+on\w+\s*=\s*[^\s>]*/gi, '');
    return safe;
  };

  return { escapeHTML, sanitizeHTML };
})();
