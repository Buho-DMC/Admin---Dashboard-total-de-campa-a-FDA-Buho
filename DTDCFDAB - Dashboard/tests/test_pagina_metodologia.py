"""Tests de pages/metodologia.py."""

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


def test_metodologia_muestra_tres_graficas_de_percentil(monkeypatch):
    # AppTest (streamlit 1.58) no expone un accesor para st.plotly_chart —
    # renderiza vía JS y no queda en el árbol de elementos introspeccionable
    # en modo bare. Se verifica el efecto real: la función que arma cada
    # gráfica se invocó 3 veces y la página corrió sin excepciones.
    _preparar(monkeypatch)
    llamadas_capturadas = []
    construir_grafica_original = charts.construir_grafica_de_percentil

    def _construir_grafica_y_contar(valor_percentil, titulo):
        llamadas_capturadas.append(titulo)
        return construir_grafica_original(valor_percentil, titulo)

    monkeypatch.setattr(charts, 'construir_grafica_de_percentil', _construir_grafica_y_contar)

    app_test = AppTest.from_file('pages/metodologia.py')
    app_test.run()

    assert len(app_test.exception) == 0
    assert len(llamadas_capturadas) == 3


def test_metodologia_explica_cada_parametro(monkeypatch):
    # 1 expander de historial (ya existente) + 1 de justificación por cada uno
    # de los 6 parámetros.
    _preparar(monkeypatch)
    app_test = AppTest.from_file('pages/metodologia.py')
    app_test.run()

    assert len(app_test.exception) == 0
    assert len(app_test.expander) == 7
    assert sum(1 for expander in app_test.expander if expander.label == 'Ver justificación') == 6


def test_metodologia_boton_deshabilitado_sin_checkbox(monkeypatch):
    _preparar(monkeypatch)
    app_test = AppTest.from_file('pages/metodologia.py')
    app_test.run()
    boton_guardar = next(boton for boton in app_test.button if boton.label == 'Guardar y recalcular')
    assert boton_guardar.disabled is True


def test_metodologia_guarda_al_confirmar_checkbox_y_boton(monkeypatch):
    _preparar(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'crear_configuracion',
        lambda **kwargs: {'configuracion': {'id_configuracion': 2}, 'id_lote': 'lote-1', 'total_campanas': 19},
    )
    app_test = AppTest.from_file('pages/metodologia.py')
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
    app_test = AppTest.from_file('pages/metodologia.py')
    app_test.run()
    assert len(app_test.error) == 1
