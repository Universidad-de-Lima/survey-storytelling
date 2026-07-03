/**
 * Tests — Loader (loader.js)
 *
 * Valida constantes de configuración, tipos de encuesta, y lógica
 * de normalización de periodos. No prueba el DOM ni el overflow system
 * (requiere ResizeObserver + DOM completo).
 *
 * Ejecutar en navegador: abrir tests/run-tests.html
 * Ejecutar en CI: node (tests.yml)
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;

  // ── Constantes esperadas del loader ──
  // Estas deben coincidir con LOADER_CONFIG y SURVEY_TYPES en loader.js

  const EXPECTED_SURVEY_IDS = [
    'undergraduate', 'graduate', 'posgraduate',
    'alumni-ug', 'alumni-pg',
    'faculty-ug', 'faculty-pg',
    'nonfaculty', 'employers'
  ];

  const EXPECTED_SURVEY_PATHS = {
    undergraduate: 'students/undergraduate',
    graduate: 'students/graduate',
    posgraduate: 'students/posgraduate',
    'alumni-ug': 'alumni/undergraduate',
    'alumni-pg': 'alumni/posgraduate',
    'faculty-ug': 'facultyStaff/undergraduate',
    'faculty-pg': 'facultyStaff/posgraduate',
    nonfaculty: 'nonfacultyStaff',
    employers: 'employers'
  };

  // ── Helper: simular normalizePeriods (lógica extraída de loader.js) ──
  function normalizePeriods(raw, surveyPath) {
    if (!Array.isArray(raw)) return [];
    return raw
      .filter(p => p && typeof p.id === 'string' && p.id.trim() !== '')
      .map(p => ({
        id: p.id.trim(),
        label: p.label || p.id.trim(),
        url: p.url || `${surveyPath}/${p.id.trim()}/index.html`,
        isNew: p.isNew || false
      }))
      .reverse(); // Más reciente primero
  }

  describe('Loader — Tipos de encuesta', () => {
    it('debe haber exactamente 9 tipos de encuesta', () => {
      assert.equal(EXPECTED_SURVEY_IDS.length, 9,
        'Debe haber 9 tipos de encuesta definidos');
    });

    it('cada tipo tiene un path asignado', () => {
      EXPECTED_SURVEY_IDS.forEach(id => {
        assert.isTrue(
          EXPECTED_SURVEY_PATHS[id] !== undefined,
          `Tipo '${id}' debe tener un path`
        );
        assert.isTrue(
          typeof EXPECTED_SURVEY_PATHS[id] === 'string' &&
          EXPECTED_SURVEY_PATHS[id].length > 0,
          `Path de '${id}' no debe estar vacío`
        );
      });
    });

    it('paths de estudiantes y graduados son los activos', () => {
      assert.equal(EXPECTED_SURVEY_PATHS.undergraduate, 'students/undergraduate');
      assert.equal(EXPECTED_SURVEY_PATHS.graduate, 'students/graduate');
    });

    it('IDs de localStorage usan guiones (kebab-case)', () => {
      // Los IDs con sub-nivel usan guiones: alumni-ug, alumni-pg, faculty-ug, faculty-pg
      const multiLevel = ['alumni-ug', 'alumni-pg', 'faculty-ug', 'faculty-pg'];
      multiLevel.forEach(id => {
        assert.isTrue(EXPECTED_SURVEY_IDS.includes(id),
          `ID '${id}' debe estar en la lista de tipos`);
      });
    });
  });

  describe('Loader — normalizePeriods', () => {
    const surveyPath = 'students/undergraduate';

    it('retorna array vacío para entrada no-array', () => {
      assert.deepEqual(normalizePeriods(null, surveyPath), []);
      assert.deepEqual(normalizePeriods(undefined, surveyPath), []);
      assert.deepEqual(normalizePeriods('string', surveyPath), []);
      assert.deepEqual(normalizePeriods(42, surveyPath), []);
    });

    it('retorna array vacío para array vacío', () => {
      assert.deepEqual(normalizePeriods([], surveyPath), []);
    });

    it('filtra items sin id válido', () => {
      const raw = [
        { id: '', label: 'Vacío' },
        { id: '  ', label: 'Blancos' },
        { label: 'Sin ID' },
        null,
        undefined
      ];
      const result = normalizePeriods(raw, surveyPath);
      assert.equal(result.length, 0);
    });

    it('normaliza periodos correctamente', () => {
      // periodos.json viene en orden cronológico (más antiguo primero).
      // normalizePeriods aplica .reverse() → más reciente primero.
      const raw = [
        { id: '2025-2', label: '2025-2', isNew: false },
        { id: '2026-1', label: '2026-1', isNew: true }
      ];
      const result = normalizePeriods(raw, surveyPath);
      assert.equal(result.length, 2);
      // Reverse: más reciente primero
      assert.equal(result[0].id, '2026-1');
      assert.equal(result[1].id, '2025-2');
    });

    it('genera url por defecto si no se proporciona', () => {
      const raw = [{ id: '2026-1', label: '2026-1' }];
      const result = normalizePeriods(raw, surveyPath);
      assert.equal(result[0].url, 'students/undergraduate/2026-1/index.html');
    });

    it('respeta url proporcionada', () => {
      const raw = [{ id: '2026-1', label: '2026-1', url: '/custom/path' }];
      const result = normalizePeriods(raw, surveyPath);
      assert.equal(result[0].url, '/custom/path');
    });

    it('marca isNew correctamente', () => {
      // periodos.json: orden cronológico → reverse → más reciente primero
      const raw = [
        { id: '2025-2', label: '2025-2', isNew: false },
        { id: '2026-1', label: '2026-1', isNew: true }
      ];
      const result = normalizePeriods(raw, surveyPath);
      // Tras reverse: 2026-1 (isNew=true) primero, 2025-2 (isNew=false) segundo
      assert.equal(result[0].id, '2026-1');
      assert.isTrue(result[0].isNew);
      assert.equal(result[1].id, '2025-2');
      assert.isFalse(result[1].isNew);
    });

    it('el más reciente aparece primero (reverse)', () => {
      // periodos.json viene en orden cronológico (más antiguo primero)
      const raw = [
        { id: '2025-2', label: '2025-2' },
        { id: '2026-1', label: '2026-1' }
      ];
      const result = normalizePeriods(raw, surveyPath);
      // Tras reverse: más reciente primero
      assert.equal(result[0].id, '2026-1');
      assert.equal(result[1].id, '2025-2');
    });

    it('trimea espacios en IDs', () => {
      const raw = [{ id: '  2026-1  ', label: '2026-1' }];
      const result = normalizePeriods(raw, surveyPath);
      assert.equal(result[0].id, '2026-1');
    });
  });

  describe('Loader — localStorage keys', () => {
    it('clave de encuesta seleccionada es correcta', () => {
      const key = 'ulima_selected_survey';
      assert.isTrue(typeof key === 'string' && key.length > 0);
    });

    it('clave de periodo sigue el patrón ulima_selected_period_<id>', () => {
      const surveyId = 'undergraduate';
      const key = `ulima_selected_period_${surveyId}`;
      assert.equal(key, 'ulima_selected_period_undergraduate');
    });

    it('cada tipo de encuesta tiene una clave de periodo única', () => {
      const keys = EXPECTED_SURVEY_IDS.map(id => `ulima_selected_period_${id}`);
      const unique = new Set(keys);
      assert.equal(unique.size, keys.length,
        'Todas las claves de periodo deben ser únicas');
    });
  });
})();
