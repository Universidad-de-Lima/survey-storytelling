/**
 * TESTS — SurveyMultiselect
 *
 * Prueba el multiselect para ciclos.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const MS = window.SurveyMultiselect;

  if (!MS) {
    console.error('SurveyMultiselect no encontrado.');
    return;
  }

  describe('SurveyMultiselect.create', () => {
    it('create devuelve un HTMLElement', () => {
      const sel = document.createElement('select');
      sel.multiple = true;
      sel.innerHTML = '<option value="1">I</option><option value="2">II</option>';
      const wrapper = MS.create(sel);
      assert.isDefined(wrapper, 'wrapper debe existir');
      assert.true(wrapper instanceof HTMLElement, 'debe ser HTMLElement');
    });

    it('create asigna método update al wrapper', () => {
      const sel = document.createElement('select');
      sel.multiple = true;
      sel.innerHTML = '<option value="a">A</option>';
      const wrapper = MS.create(sel);
      assert.isDefined(wrapper.update, 'wrapper debe tener update');
      assert.typeOf(wrapper.update, 'function', 'update debe ser función');
    });

    it('create con callback opcional', () => {
      const sel = document.createElement('select');
      sel.multiple = true;
      sel.innerHTML = '<option value="x">X</option>';
      let called = false;
      const wrapper = MS.create(sel, () => { called = true; });
      assert.isDefined(wrapper, 'debe crear sin errores');
    });

    it('create con label e itemName personalizados', () => {
      const sel = document.createElement('select');
      sel.multiple = true;
      sel.innerHTML = '<option value="1">I</option>';
      const wrapper = MS.create(sel, null, 'Todos', 'items');
      assert.isDefined(wrapper, 'debe crear con parámetros personalizados');
    });

    it('update no lanza error', () => {
      const sel = document.createElement('select');
      sel.multiple = true;
      sel.innerHTML = '<option value="1">I</option>';
      const wrapper = MS.create(sel);
      wrapper.update();
      assert.true(true, 'update no debe lanzar error');
    });
  });
})();
