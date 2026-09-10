"""Tests de pages/detalle_de_campana.py."""

from datetime import date

from streamlit.testing.v1 import AppTest

import api_client

_CAMPANAS = [{'id_campana': 1, 'nombre': 'FDA Salud Visual 26'}]
_EVENTOS_DE_CAMPANA = [{'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'fecha': None, 'actualizado_en': None}]


def _preparar(monkeypatch, campanas=None, snapshot=None, job=None):
    monkeypatch.setattr(api_client, 'list_campanas', lambda: campanas if campanas is not None else _CAMPANAS)
    monkeypatch.setattr(api_client, 'list_eventos_de_campana', lambda id_campana: _EVENTOS_DE_CAMPANA)
    monkeypatch.setattr(api_client, 'get_snapshot_de_campana', lambda id_campana: snapshot)
    monkeypatch.setattr(api_client, 'get_ultimo_job_de_campana', lambda id_campana: job or {'estado': 'exitoso'})
    monkeypatch.setattr(api_client, 'borrar_campana', lambda id_campana: None)


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


def test_detalle_muestra_el_error_del_job_fallido(monkeypatch):
    _preparar(monkeypatch, job={'estado': 'fallido', 'error': 'Claw no devolvió escaneos de Pick & Pack.'})
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    assert any('Claw no devolvió escaneos de Pick & Pack.' in mensaje.value for mensaje in app_test.error)


def test_detalle_boton_de_borrar_deshabilitado_sin_confirmar(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    boton_borrar = next(boton for boton in app_test.button if boton.label == 'Borrar campaña')
    assert boton_borrar.disabled is True


def test_detalle_borra_la_campana_al_confirmar(monkeypatch):
    _preparar(monkeypatch)
    llamadas_a_borrar = []
    monkeypatch.setattr(api_client, 'borrar_campana', lambda id_campana: llamadas_a_borrar.append(id_campana))
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    app_test.checkbox[0].check().run()
    boton_borrar = next(boton for boton in app_test.button if boton.label == 'Borrar campaña')
    boton_borrar.click().run()
    assert llamadas_a_borrar == [1]
    assert len(app_test.success) == 1


def test_detalle_no_muestra_error_si_el_job_no_fallo(monkeypatch):
    _preparar(monkeypatch, job={'estado': 'exitoso', 'error': None})
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    assert len(app_test.error) == 0


def test_detalle_guarda_la_fecha_de_un_hito_al_confirmar(monkeypatch):
    _preparar(monkeypatch)
    llamadas_guardadas = []
    monkeypatch.setattr(
        api_client,
        'upsert_evento_de_campana',
        lambda id_campana, codigo_evento, fecha: llamadas_guardadas.append((id_campana, codigo_evento, fecha)),
    )
    app_test = AppTest.from_file('pages/detalle_de_campana.py')
    app_test.run()
    app_test.date_input[0].set_value(date(2026, 9, 15))
    boton_guardar = next(boton for boton in app_test.button if boton.label == 'Guardar Arte aprobado')
    boton_guardar.click().run()
    assert len(llamadas_guardadas) == 1
    assert llamadas_guardadas[0][0] == 1
    assert llamadas_guardadas[0][1] == 'arte'
    assert len(app_test.success) == 1
