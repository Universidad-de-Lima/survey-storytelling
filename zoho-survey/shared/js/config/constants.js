/**
 * SURVEY CONFIG — Constantes de negocio externalizadas.
 * 
 * Este archivo es la fuente canónica de configuración para todos los dashboards.
 * dashboard.js usará estos valores si están disponibles, con fallback a sus
 * hardcodeados internos para mantener compatibilidad backward.
 * 
 * Para modificar metas, ciclos especiales o labels:
 * 1. Editar este archivo
 * 2. El cambio aplica a TODOS los dashboards sin tocar dashboard.js
 * 
 * @module config/constants
 * @version 1.0.0
 */

window.SURVEY_CONFIG = {
  // ── Metas institucionales ──
  META_NPS: 50,
  META_CSAT: 93,

  // ── Carreras y facultades con 12 ciclos (en lugar de 10) ──
  CARRERAS_12_CICLOS: ['Derecho', 'Psicología'],
  FACULTADES_12_CICLOS: ['Facultad de Derecho', 'Facultad de Psicología'],

  // ── Programa de Estudios Generales ──
  PROGRAMA_ESTUDIOS_GENERALES: 'Programa de Estudios Generales',
  CICLOS_ESTUDIOS_GENERALES: ['1° Ciclo', '2° Ciclo'],

  // ── Claves de niveles de satisfacción ──
  // NO modificar a menos que Zoho Survey cambie sus etiquetas
  SAT_KEYS: [
    'Totalmente satisfecho',
    'Muy satisfecho',
    'Satisfecho',
    'Insatisfecho',
    'Totalmente insatisfecho',
  ],

  // ── Placeholder texts ──
  FACULTAD_PLACEHOLDER: 'Todas las facultades',
  FACULTAD_PLACEHOLDER_PROG: 'Todas las facultades / programas',

  // ── Umbrales visuales ──
  // Porcentaje mínimo para mostrar etiqueta en barra
  MIN_BAR_LABEL_PCT: 4,
  // Porcentaje mínimo para generar etiqueta externa
  MIN_EXTERNAL_LABEL_PCT: 0.5,
  // Ancho mínimo (px) para etiqueta en segmento
  MIN_SEGMENT_WIDTH: 30,
};
