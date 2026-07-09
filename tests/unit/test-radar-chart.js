/**
 * TESTS — SurveyRadarChart
 *
 * Prueba el gráfico radar SVG.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const RC = window.SurveyRadarChart;

  if (!RC) {
    console.error('SurveyRadarChart no encontrado.');
    return;
  }

  describe('SurveyRadarChart.dimensionAplica', () => {
    it('dimensionAplica es función', () => {
      assert.typeOf(RC.dimensionAplica, 'function', 'debe ser función');
    });

    it('dimensionAplica retorna true si la dimensión existe en rows', () => {
      const rows = [
        { dimension: 'Aulas de clase', t3b: 50, total: 100 },
        { dimension: 'Biblioteca', t3b: 80, total: 100 }
      ];
      const result = RC.dimensionAplica(rows, 'Aulas de clase');
      assert.true(result, 'debe retornar true para dimensión existente');
    });

    it('dimensionAplica retorna false si la dimensión no existe', () => {
      const rows = [
        { dimension: 'Aulas de clase', t3b: 50, total: 100 }
      ];
      const result = RC.dimensionAplica(rows, 'Inexistente');
      assert.isFalse(result, 'debe retornar false para dimensión inexistente');
    });

    it('dimensionAplica maneja array vacío', () => {
      const result = RC.dimensionAplica([], 'Cualquiera');
      assert.isFalse(result, 'debe retornar false para array vacío');
    });

    it('dimensionAplica maneja rows sin dimension', () => {
      const rows = [{ t3b: 50 }];
      const result = RC.dimensionAplica(rows, 'test');
      assert.isFalse(result, 'debe retornar false si rows no tienen dimension');
    });
  });

  describe('SurveyRadarChart.render', () => {
    it('render sin opciones no lanza error', () => {
      RC.render();
      assert.true(true, 'render() sin opciones no debe lanzar error');
    });

    it('render con svgId existente no lanza error', () => {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.id = 'radar-test';
      document.body.appendChild(svg);
      RC.render({ svgId: 'radar-test' });
      assert.true(true, 'render con svgId no debe lanzar error');
      svg.remove();
    });

    it('render con datos vacíos no lanza error', () => {
      RC.render({ filteredDimensions: [], rawDimensions: [] });
      assert.true(true, 'render con datos vacíos no debe lanzar error');
    });

    it('render con filteredDimensions no lanza error', () => {
      RC.render({
        filteredDimensions: [
          { dim: 'Aulas', pct: 75, categoria: 'Infraestructura' }
        ],
        rawDimensions: [
          { dim: 'Aulas', pct: 75, categoria: 'Infraestructura' }
        ]
      });
      assert.true(true, 'render con dimensiones no debe lanzar error');
    });
  });
})();
