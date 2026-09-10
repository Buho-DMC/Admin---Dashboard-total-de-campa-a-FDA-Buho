"""Tests de app.py — gate de PIN y arranque de la navegación."""

from streamlit.testing.v1 import AppTest

import api_client


def test_gate_bloquea_sin_intentar_iniciar_sesion():
    app_test = AppTest.from_file('app.py')
    app_test.secrets['app_password'] = 'clave-correcta'
    app_test.run()

    assert len(app_test.text_input) == 1
    # SafeSessionState (AppTest, streamlit 1.58) no implementa .get(), solo
    # __getitem__ y __contains__ — de ahí el uso de `in` en vez de .get().
    assert 'autenticado' not in app_test.session_state


def test_gate_muestra_error_con_contrasena_incorrecta():
    app_test = AppTest.from_file('app.py')
    app_test.secrets['app_password'] = 'clave-correcta'
    app_test.run()
    app_test.text_input[0].set_value('clave-incorrecta').run()
    app_test.button[0].click().run()

    assert len(app_test.error) == 1
    assert 'autenticado' not in app_test.session_state


def test_gate_permite_acceso_con_contrasena_correcta(monkeypatch):
    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', lambda: [])

    app_test = AppTest.from_file('app.py')
    app_test.secrets['app_password'] = 'clave-correcta'
    app_test.run()
    app_test.text_input[0].set_value('clave-correcta').run()
    app_test.button[0].click().run()

    assert app_test.session_state['autenticado'] is True
