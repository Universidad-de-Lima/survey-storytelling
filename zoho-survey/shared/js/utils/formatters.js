/**
 * SURVEY FORMATTERS — Funciones puras de formateo.
 *
 * Extraídas de dashboard.js (v2.0). Sin dependencias externas.
 * Usar como: SurveyFormatters.formatDecimal(3.14159, 2) → "3,14"
 *
 * Contrato:
 * - formatDecimal(n, digits=2): siempre muestra `digits` decimales, excepto
 *   cuando TODOS son cero (caso entero) que devuelve el entero sin decimales.
 *   Ejemplo: formatDecimal(1.5) → "1,50"; formatDecimal(3.0) → "3".
 *   Usa toFixed() que trunca (no redondea) en casos de float impreciso
 *   (ej. 1.2345 → "1,234" porque 1.2345 en float es 1.2344999...).
 *
 * @module utils/formatters
 * @version 1.0.0
 */
window.SurveyFormatters = (() => {
  'use strict';

  // ── Números ──
  const formatInteger = (n) => n.toString();

  const formatDecimal = (n, digits = 2) => {
    if (n === null || n === undefined) return '';
    const rounded = n.toFixed(digits);
    if (rounded.endsWith('0'.repeat(digits))) return Math.round(n).toString();
    return rounded.replace('.', ',');
  };

  const formatPercent = (n, digits = 2) => formatDecimal(n, digits) + ' %';

  const formatPctSimple = (v, t) => (t === 0 ? '0%' : Math.round((v / t) * 100) + '%');

  const formatPctDecimal = (v, t) => {
    if (t === 0) return '0,0 %';
    return formatDecimal((v / t) * 100, 1) + ' %';
  };

  // ── Fechas ──
  const formatDate = (ds) =>
    new Date(`${ds}T12:00:00`).toLocaleDateString('es-PE', { day: 'numeric', month: 'long' });

  // ── Ciclos ──
  const formatCicloText = (ciclo) => {
    const match = ciclo.match(/^(\d+)/);
    if (!match) return ciclo;
    const num = match[1];
    return num === '1' || num === '3' ? `${num}.ᵉʳ ciclo` : `${num}.º ciclo`;
  };

  // ── Texto ──
  const cortarTexto = (t, max) => (t.length > max ? `${t.slice(0, max - 1)}…` : t);

  // ── Nombres de dimensión ──
  const formatDimensionName = (dim) => {
    if (dim === 'Software especializado empleado en la carrera') {
      return '<span><i>Software</i> especializado empleado en la carrera</span>';
    }
    return dim;
  };

  const formatDimensionNameSVG = (dim, maxLen = 26) => {
    const plain = formatDimensionName(dim).replace(/<[^>]*>/g, '');
    const truncated = cortarTexto(plain, maxLen);
    if (
      dim === 'Software especializado empleado en la carrera' &&
      truncated.startsWith('Software')
    ) {
      return `<tspan font-style="italic">Software</tspan>${truncated.slice('Software'.length)}`;
    }
    return truncated;
  };

  const formatDimensionNameForAttr = (dim) =>
    formatDimensionName(dim).replace(/</g, '&lt;').replace(/>/g, '&gt;');

  return {
    formatInteger,
    formatDecimal,
    formatPercent,
    formatPctSimple,
    formatPctDecimal,
    formatDate,
    formatCicloText,
    cortarTexto,
    formatDimensionName,
    formatDimensionNameSVG,
    formatDimensionNameForAttr,
  };
})();
