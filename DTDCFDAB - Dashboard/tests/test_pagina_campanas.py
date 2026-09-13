"""Tests de views/campanas.py (fusión de Campañas + Detalle de campaña)."""

from datetime import date

import streamlit as st
from streamlit.testing.v1 import AppTest

import api_client

_SNAPSHOT_1 = {
    'id_campana': 1, 'numero_envios': 100, 'porcentaje_alcanzado_entregas': 0.87,
    'ultima_entrega': '2026-09-01T00:00:00', 'calculado_en': '2026-09-02T00:00:00',
    'inicio_carga_artes': '2026-08-01T00:00:00', 'fin_carga_artes': '2026-08-03T00:00:00',
    'inicio_entregas': '2026-08-20T00:00:00', 'fin_entregas': '2026-08-25T00:00:00',
}
_EVENTOS_DE_CAMPANA = [{'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'fecha': None, 'actualizado_en': None}]


def _preparar(monkeypatch, snapshots=None, eventos=None, job=None):
    st.cache_data.clear()
    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', lambda: snapshots if snapshots is not None else [_SNAPSHOT_1])
    monkeypatch.setattr(api_client, 'list_eventos_de_campana', lambda id_campana: eventos if eventos is not None else _EVENTOS_DE_CAMPANA)
    monkeypatch.setattr(api_client, 'get_ultimo_job_de_campana', lambda id_campana: job or {'estado': 'exitoso'})
    monkeypatch.setattr(api_client, 'borrar_campana', lambda id_campana: None)


def test_campanas_muestra_error_si_la_api_falla(monkeypatch):
    def _lanza_error():
        raise RuntimeError('boom')

    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', _lanza_error)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.error) == 1
    assert len(app_test.exception) == 1
    assert 'boom' in app_test.exception[0].value


def test_campanas_muestra_mensaje_si_no_hay_snapshots(monkeypatch):
    _preparar(monkeypatch, snapshots=[])
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.info) == 1


def test_campanas_no_tiene_tabla_ni_boton_ver_detalle(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.dataframe) == 0
    etiquetas_de_botones = [boton.label for boton in app_test.button]
    assert not any('Ver detalle' in etiqueta for etiqueta in etiquetas_de_botones)
    assert 'Dar de alta una campaña nueva' in etiquetas_de_botones


def test_campanas_selecciona_la_primera_campana_por_defecto(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert app_test.selectbox[0].value == 1


def test_campanas_muestra_grafica_por_actividad_por_defecto(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.exception) == 0
    assert len(app_test.get('plotly_chart')) == 1


def test_campanas_cambia_a_grafica_por_responsable(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    radios_de_grafica = next(radio for radio in app_test.radio if 'Por responsable' in radio.options)
    radios_de_grafica.set_value('Por responsable').run()
    assert len(app_test.exception) == 0
    assert len(app_test.get('plotly_chart')) == 1


def test_campanas_analisis_de_fechas_muestra_duracion_por_defecto(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.exception) == 0
    assert any('Análisis de fechas' in encabezado.value for encabezado in app_test.subheader)


def test_campanas_muestra_el_error_del_job_fallido(monkeypatch):
    _preparar(monkeypatch, job={'estado': 'fallido', 'error': 'Claw no devolvió escaneos de Pick & Pack.'})
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert any('Claw no devolvió escaneos de Pick & Pack.' in mensaje.value for mensaje in app_test.error)


def test_campanas_boton_de_borrar_deshabilitado_sin_confirmar(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    boton_borrar = next(boton for boton in app_test.button if boton.label == 'Borrar campaña')
    assert boton_borrar.disabled is True


def test_campanas_borra_la_campana_al_confirmar(monkeypatch):
    _preparar(monkeypatch)
    llamadas_a_borrar = []
    monkeypatch.setattr(api_client, 'borrar_campana', lambda id_campana: llamadas_a_borrar.append(id_campana))
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    app_test.checkbox[0].check().run()
    boton_borrar = next(boton for boton in app_test.button if boton.label == 'Borrar campaña')
    boton_borrar.click().run()
    assert llamadas_a_borrar == [1]
    assert len(app_test.success) == 1


def test_campanas_actualizar_hitos_solo_manda_los_campos_modificados(monkeypatch):
    eventos = [
        {'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'fecha': '2026-08-01T00:00:00', 'actualizado_en': None},
        {'id_evento': 2, 'codigo': 'preproyecto', 'nombre': 'Preproyecto', 'fecha': '2026-08-05T00:00:00', 'actualizado_en': None},
    ]
    _preparar(monkeypatch, eventos=eventos)
    llamadas_guardadas = []
    monkeypatch.setattr(
        api_client, 'upsert_evento_de_campana',
        lambda id_campana, codigo_evento, fecha: llamadas_guardadas.append((id_campana, codigo_evento, fecha)),
    )
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    app_test.date_input[0].set_value(date(2026, 9, 15))  # solo cambia 'arte'
    boton_actualizar = next(boton for boton in app_test.button if boton.label == 'Actualizar fechas modificadas')
    boton_actualizar.click().run()
    assert llamadas_guardadas == [(1, 'arte', '2026-09-15')]


def test_campanas_actualizar_hitos_sin_cambios_no_llama_a_la_api(monkeypatch):
    _preparar(monkeypatch)
    llamadas_guardadas = []
    monkeypatch.setattr(
        api_client, 'upsert_evento_de_campana',
        lambda id_campana, codigo_evento, fecha: llamadas_guardadas.append((id_campana, codigo_evento, fecha)),
    )
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    boton_actualizar = next(boton for boton in app_test.button if boton.label == 'Actualizar fechas modificadas')
    boton_actualizar.click().run()
    assert llamadas_guardadas == []
    assert len(app_test.info) >= 1
