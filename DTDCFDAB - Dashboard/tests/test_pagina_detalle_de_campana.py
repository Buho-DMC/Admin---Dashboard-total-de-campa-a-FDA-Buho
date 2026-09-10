"""Tests de pages/detalle_de_campana.py."""

from streamlit.testing.v1 import AppTest

import api_client

_CAMPANAS = [{'id_campana': 1, 'nombre': 'FDA Salud Visual 26'}]
_EVENTOS_DE_CAMPANA = [{'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'fecha': None, 'actualizado_en': None}]


def _preparar(monkeypatch, campanas=None, snapshot=None, job=None):
    monkeypatch.setattr(api_client, 'list_campanas', lambda: campanas if campanas is not None else _CAMPANAS)
    monkeypatch.setattr(api_client, 'list_eventos_de_campana', lambda id_campana: _EVENTOS_DE_CAMPANA)
    monkeypatch.setattr(api_client, 'get_snapshot_de_campana', lambda id_campana: snapshot)
    monkeypatch.setattr(api_client, 'get_ultimo_job_de_campana', lambda id_campana: job or {'estado': 'exitoso'})


def test_detalle_muestra_mensaje_si_no_hay_campanas(monkeypatch):
    _preparar(monkeypatch, campanas=[])
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    assert len(app_test.info) == 1


def test_detalle_muestra_info_si_snapshot_no_calculado(monkeypatch):
    _preparar(monkeypatch, snapshot=None)
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    assert any('Aún no se ha calculado' in mensaje.value for mensaje in app_test.info)


def test_detalle_muestra_snapshot_cuando_existe(monkeypatch):
    _preparar(monkeypatch, snapshot={'numero_envios': 100})
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    assert len(app_test.json) == 1


def test_detalle_usa_campana_preseleccionada(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.session_state['id_campana_seleccionada'] = 1
    app_test.run()
    assert app_test.selectbox[0].value == 1
