"""Tests de pages/campanas.py."""

from streamlit.testing.v1 import AppTest

import api_client


def test_campanas_muestra_error_si_la_api_falla(monkeypatch):
    def _lanza_error():
        raise RuntimeError('boom')

    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', _lanza_error)

    app_test = AppTest.from_file('pages/campanas.py')
    app_test.run()

    assert len(app_test.error) == 1
    assert len(app_test.exception) == 1
    assert 'boom' in app_test.exception[0].value


def test_campanas_muestra_mensaje_si_no_hay_snapshots(monkeypatch):
    monkeypatch.setattr(api_client, 'list_snapshots_vigentes', lambda: [])

    app_test = AppTest.from_file('pages/campanas.py')
    app_test.run()

    assert len(app_test.info) == 1


def test_campanas_muestra_tabla_y_boton_de_alta(monkeypatch):
    monkeypatch.setattr(
        api_client,
        'list_snapshots_vigentes',
        lambda: [
            {
                'id_campana': 1,
                'numero_envios': 100,
                'porcentaje_alcanzado_entregas': 0.87,
                'ultima_entrega': '2026-09-01T00:00:00',
                'calculado_en': '2026-09-02T00:00:00',
            }
        ],
    )

    app_test = AppTest.from_file('pages/campanas.py')
    app_test.run()

    assert len(app_test.dataframe) == 1
    etiquetas_de_botones = [boton.label for boton in app_test.button]
    assert 'Dar de alta una campaña nueva' in etiquetas_de_botones
    assert 'Ver detalle — campaña 1' in etiquetas_de_botones
