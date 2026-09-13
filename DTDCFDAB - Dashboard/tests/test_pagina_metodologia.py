"""Tests de views/metodologia.py."""

from streamlit.testing.v1 import AppTest

import api_client
import charts

_CONFIGURACION_VIGENTE = {
    'id_configuracion': 1,
    'nombre': 'Metodología (etl.ipynb, 2026-09-04)',
    'porcentaje_fin': 0.99,
    'porcentaje_inicio': 0.01,
    'porcentaje_bloque_minimo': 0.05,
    'hueco_entregas_dias': 10.0,
    'desfase_rescate_dias': 0.622,
    'cobertura_aviso': 0.95,
}


def _preparar(monkeypatch):
    monkeypatch.setattr(api_client, 'get_configuracion_vigente', lambda: _CONFIGURACION_VIGENTE)
    monkeypatch.setattr(api_client, 'list_historial_configuracion', lambda: [_CONFIGURACION_VIGENTE])


def test_metodologia_muestra_una_sola_grafica_combinada(monkeypatch):
    _preparar(monkeypatch)
    llamadas_capturadas = []
    construir_grafica_original = charts.construir_grafica_de_percentiles_combinada

    def _construir_grafica_y_contar(valores_percentil):
        llamadas_capturadas.append(valores_percentil)
        return construir_grafica_original(valores_percentil)

    monkeypatch.setattr(charts, 'construir_grafica_de_percentiles_combinada', _construir_grafica_y_contar)

    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()

    assert len(app_test.exception) == 0
    assert len(llamadas_capturadas) == 1
    assert set(llamadas_capturadas[0].keys()) == {'Porcentaje inicio', 'Porcentaje fin', 'Cobertura de aviso'}


def test_metodologia_no_tiene_expanders_de_justificacion(monkeypatch):
    # Antes había 1 expander de justificación por cada uno de los 6 parámetros
    # (más el de historial). Ahora las justificaciones están siempre visibles:
    # solo debe quedar el expander de historial.
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()

    assert len(app_test.exception) == 0
    assert len(app_test.expander) == 1
    assert app_test.expander[0].label == 'Historial de combinaciones ya usadas'


def test_metodologia_explica_cada_parametro_con_actividad_afectada(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()

    assert len(app_test.exception) == 0
    texto_completo = '\n'.join(elemento.value for elemento in app_test.markdown)
    assert 'Entregas' in texto_completo
    assert 'Pick & Pack' in texto_completo
    assert 'No afecta ningún cálculo del ETL' in texto_completo


def test_metodologia_fila_final_tiene_nombre_checkbox_y_boton_juntos(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()

    assert len(app_test.text_input) == 1
    assert len(app_test.checkbox) == 1
    boton_guardar = next(boton for boton in app_test.button if boton.label == 'Guardar y recalcular')
    assert boton_guardar.disabled is True


def test_metodologia_guarda_al_confirmar_checkbox_y_boton(monkeypatch):
    _preparar(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'crear_configuracion',
        lambda **kwargs: {'configuracion': {'id_configuracion': 2}, 'id_lote': 'lote-1', 'total_campanas': 19},
    )
    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()
    app_test.checkbox[0].check().run()
    boton_guardar = next(boton for boton in app_test.button if boton.label == 'Guardar y recalcular')
    boton_guardar.click().run()
    assert len(app_test.success) == 1
    assert app_test.session_state['id_lote_seleccionado'] == 'lote-1'


def test_metodologia_muestra_error_si_falla_la_carga(monkeypatch):
    def _lanza_error():
        raise RuntimeError('boom')

    monkeypatch.setattr(api_client, 'get_configuracion_vigente', _lanza_error)
    app_test = AppTest.from_file('views/metodologia.py')
    app_test.run()
    assert len(app_test.error) == 1
