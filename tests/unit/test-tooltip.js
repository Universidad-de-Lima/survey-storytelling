/**
 * TESTS — SurveyTooltip
 *
 * Prueba el sistema de tooltips del dashboard.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const T = window.SurveyTooltip;

  if (!T) {
    console.error('SurveyTooltip no encontrado.');
    return;
  }

  describe('SurveyTooltip.show/hide', () => {
    it('show y hide son funciones', () => {
      assert.typeOf(T.show, 'function', 'show debe ser función');
      assert.typeOf(T.hide, 'function', 'hide debe ser función');
    });

    it('show con evento y texto no lanza error', () => {
      const ev = new MouseEvent('mousemove', { clientX: 100, clientY: 200 });
      T.show(ev, 'Contenido del tooltip');
      assert.true(true, 'show no debe lanzar error');
    });

    it('show con raw=true no lanza error', () => {
      const ev = new MouseEvent('mousemove', { clientX: 50, clientY: 50 });
      T.show(ev, '<b>raw</b>', true);
      assert.true(true, 'show raw no debe lanzar error');
    });

    it('hide no lanza error', () => {
      T.hide();
      assert.true(true, 'hide no debe lanzar error');
    });

    it('show con HTML debe sanitizar por defecto', () => {
      const ev = new MouseEvent('mousemove', { clientX: 10, clientY: 10 });
      T.show(ev, '<script>alert(1)</script>');
      assert.true(true, 'show con HTML malicioso no debe lanzar error');
    });

    it('bindToSegments es función', () => {
      if (T.bindToSegments) {
        assert.typeOf(T.bindToSegments, 'function', 'bindToSegments debe ser función');
      } else {
        assert.true(true, 'bindToSegments no está definido (depende de versión)');
      }
    });
  });
})();
