/**
 * TESTS — SurveyCustomSelect
 *
 * Prueba el wrapper de select personalizado.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const CS = window.SurveyCustomSelect;

  if (!CS) {
    console.error('SurveyCustomSelect no encontrado.');
    return;
  }

  describe('SurveyCustomSelect.create', () => {
    it('create devuelve un objeto con update, close, button, wrapper', () => {
      const sel = document.createElement('select');
      sel.innerHTML = '<option value="a">A</option><option value="b">B</option>';
      const result = CS.create(sel);
      assert.isDefined(result, 'result debe existir');
      assert.isDefined(result.update, 'debe tener update');
      assert.isDefined(result.close, 'debe tener close');
      assert.isDefined(result.button, 'debe tener button');
      assert.isDefined(result.wrapper, 'debe tener wrapper');
    });

    it('create reemplaza el select con un wrapper', () => {
      const sel = document.createElement('select');
      sel.innerHTML = '<option value="x">X</option>';
      const result = CS.create(sel);
      assert.true(result.wrapper.contains(sel), 'wrapper debe contener al select');
    });

    it('create acepta callback opcional sin errores', () => {
      const sel = document.createElement('select');
      sel.innerHTML = '<option value="1">1</option>';
      let called = false;
      const result = CS.create(sel, () => { called = true; });
      assert.isDefined(result, 'debe crear sin errores');
    });

    it('close oculta el dropdown', () => {
      const sel = document.createElement('select');
      sel.innerHTML = '<option value="a">A</option>';
      const result = CS.create(sel);
      result.close();
      assert.true(true, 'close no debe lanzar error');
    });

    it('update re-renderiza sin errores', () => {
      const sel = document.createElement('select');
      sel.innerHTML = '<option value="a">A</option>';
      const result = CS.create(sel);
      result.update();
      assert.true(true, 'update no debe lanzar error');
    });
  });
})();
