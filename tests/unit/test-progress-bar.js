/**
 * TESTS — SurveyProgressBar
 *
 * Prueba la barra de progreso de scroll.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const PB = window.SurveyProgressBar;

  if (!PB) {
    console.error('SurveyProgressBar no encontrado.');
    return;
  }

  describe('SurveyProgressBar.init', () => {
    it('init es una función', () => {
      assert.typeOf(PB.init, 'function', 'init debe ser función');
    });

    it('init sin opciones no lanza error', () => {
      PB.init();
      assert.true(true, 'init() sin opciones no debe lanzar error');
    });

    it('init con fillSelector personalizado no lanza error', () => {
      PB.init({ fillSelector: '#progress-fill' });
      assert.true(true, 'init con fillSelector no debe lanzar error');
    });

    it('init con todas las opciones no lanza error', () => {
      PB.init({
        fillSelector: '#progress-fill',
        navSelector: '.nav',
        sectionIds: ['ejecutivo', 'radar', 'preguntas', 'cualitativo']
      });
      assert.true(true, 'init completo no debe lanzar error');
    });
  });
})();
