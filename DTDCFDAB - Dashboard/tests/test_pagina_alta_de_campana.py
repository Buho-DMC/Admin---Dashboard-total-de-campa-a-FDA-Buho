"""Tests de pages/alta_de_campana.py."""

from streamlit.testing.v1 import AppTest

import api_client

_CAMPANAS_RETOOL = [
    {
        'id_claw': 212,
        'campana': 'FDA Salud Visual 26',
        'cliente': 'Farmacias del Ahorro',
        'cliente_clave': 'FDA',
        'inicio_campana': '2026-09-01',
    }
]
_EVENTOS = [{'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'orden': 1}]


def _preparar(monkeypatch, campanas_retool=None, eventos=None):
    monkeypatch.setattr(api_client, 'list_campanas_retool', lambda: campanas_retool if campanas_retool is not None else _CAMPANAS_RETOOL)
    monkeypatch.setattr(api_client, 'list_eventos', lambda: eventos if eventos is not None else _EVENTOS)


def test_alta_de_campana_muestra_mensaje_si_no_hay_campanas(monkeypatch):
    _preparar(monkeypatch, campanas_retool=[])
    app_test = AppTest.from_file('pages/alta_de_campana.py')
    app_test.run()
    assert len(app_test.info) == 1


def test_alta_de_campana_muestra_selector_y_fechas(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('pages/alta_de_campana.py')
    app_test.run()
    assert len(app_test.selectbox) == 1
    assert len(app_test.date_input) == 1


def test_alta_de_campana_da_de_alta_al_confirmar(monkeypatch):
    _preparar(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'dar_de_alta_campana',
        lambda **kwargs: {'campana': {'id_campana': 1, 'nombre': 'FDA Salud Visual 26'}, 'job': {'id_job': 9}},
    )
    app_test = AppTest.from_file('pages/alta_de_campana.py')
    app_test.run()
    app_test.button[0].click().run()
    assert len(app_test.success) == 1
    assert app_test.session_state['id_job_seleccionado'] == 9


def test_alta_de_campana_muestra_error_si_falla_la_carga(monkeypatch):
    def _lanza_error():
        raise RuntimeError('boom')

    monkeypatch.setattr(api_client, 'list_campanas_retool', _lanza_error)
    monkeypatch.setattr(api_client, 'list_eventos', lambda: _EVENTOS)
    app_test = AppTest.from_file('pages/alta_de_campana.py')
    app_test.run()
    assert len(app_test.error) == 1
