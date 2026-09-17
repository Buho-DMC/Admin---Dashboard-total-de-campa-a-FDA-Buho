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
_CAMPANAS = [
    {'id_campana': 1, 'id_claw': 501, 'cliente': 'FDA', 'nombre': 'Campaña Otoño 2026', 'inicio_campana': '2026-08-01T00:00:00', 'fecha_alta': '2026-08-01T00:00:00'},
]


def _preparar(monkeypatch, snapshots=None, eventos=None, job=None, campanas=None):
    st.cache_data.clear()
    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', lambda: snapshots if snapshots is not None else [_SNAPSHOT_1])
    monkeypatch.setattr(api_client, 'list_eventos_de_campana', lambda id_campana: eventos if eventos is not None else _EVENTOS_DE_CAMPANA)
    monkeypatch.setattr(api_client, 'get_ultimo_job_de_campana', lambda id_campana: job or {'estado': 'exitoso'})
    monkeypatch.setattr(api_client, 'borrar_campana', lambda id_campana: None)
    monkeypatch.setattr(api_client, 'list_campanas', lambda: campanas if campanas is not None else _CAMPANAS)


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


def test_campanas_selector_muestra_el_nombre_real_de_la_campana(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_campana = app_test.selectbox[0]
    assert selector_de_campana.options == ['Campaña Otoño 2026']


def test_campanas_selector_usa_fallback_si_list_campanas_no_trae_el_id(monkeypatch):
    _preparar(monkeypatch, campanas=[])
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_campana = app_test.selectbox[0]
    assert selector_de_campana.options == ['Campaña 1']


def test_campanas_grafica_incluye_hito_con_fecha_sin_lanzar_excepcion(monkeypatch):
    eventos = [
        {'id_evento': 6, 'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'fecha': '2026-08-10T00:00:00', 'actualizado_en': None},
    ]
    _preparar(monkeypatch, eventos=eventos)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.exception) == 0
    assert len(app_test.get('plotly_chart')) == 1


def test_campanas_tipo_de_analisis_es_dropdown(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_tipo = next(selectbox for selectbox in app_test.selectbox if 'Offset' in selectbox.options)
    assert selector_de_tipo.options == ['Duración', 'Offset', 'Fechas']
    assert not any('Offset' in radio.options for radio in app_test.radio)


def test_campanas_fechas_muestra_tarjetas_con_delta(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_tipo = next(selectbox for selectbox in app_test.selectbox if 'Offset' in selectbox.options)
    selector_de_tipo.set_value('Fechas').run()
    assert len(app_test.exception) == 0
    assert len(app_test.metric) >= 1


def test_campanas_fechas_ya_no_usa_texto_plano(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_tipo = next(selectbox for selectbox in app_test.selectbox if 'Offset' in selectbox.options)
    selector_de_tipo.set_value('Fechas').run()
    textos = [elemento.value for elemento in app_test.get('markdown')]
    assert not any('Inicio Carga de artes:' in texto for texto in textos)


def test_campanas_tiene_sliders_de_percentiles_en_sidebar(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    assert len(app_test.sidebar.slider) == 4
    etiquetas = [slider.label for slider in app_test.sidebar.slider]
    assert 'Inicio Pick & Pack (%)' in etiquetas
    assert 'Fin Pick & Pack (%)' in etiquetas
    assert 'Inicio Entregas (%)' in etiquetas
    assert 'Fin Entregas (%)' in etiquetas


def test_campanas_offset_muestra_tarjetas_cronologicas(monkeypatch):
    eventos = [
        {'id_evento': 1, 'codigo': 'arte', 'nombre': 'Arte aprobado', 'fecha': '2026-07-28T00:00:00', 'actualizado_en': None}
    ]
    _preparar(monkeypatch, eventos=eventos)
    app_test = AppTest.from_file('views/campanas.py')
    app_test.run()
    selector_de_tipo = next(selectbox for selectbox in app_test.selectbox if 'Offset' in selectbox.options)
    selector_de_tipo.set_value('Offset').run()
    assert len(app_test.exception) == 0
    assert len(app_test.metric) >= 1
    # Debe haber al menos una métrica para el hito o el Día 0
    valores_metricas = [metric.value for metric in app_test.metric]
    assert any('Día 0' in val or '0.0' in val or 'días' in val for val in valores_metricas)

