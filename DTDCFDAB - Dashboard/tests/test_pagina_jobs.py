"""Tests de views/jobs.py."""

import streamlit
from streamlit.testing.v1 import AppTest

import api_client


def _sin_autorefresh(monkeypatch):
    monkeypatch.setattr('streamlit_autorefresh.st_autorefresh', lambda **kwargs: 0)


def test_jobs_muestra_info_y_botones(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(api_client, 'get_resumen_jobs', lambda: [])
    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    assert len(app_test.info) == 1
    etiquetas_botones = [boton.label for boton in app_test.button]
    assert 'Actualizar estado' in etiquetas_botones
    assert 'Reintentar fallidos' in etiquetas_botones


def test_jobs_muestra_resumen_en_tabla_fija(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'get_resumen_jobs',
        lambda: [
            {'id_job_ejecucion': 1, 'id_campana': 1, 'tipo': 'alta', 'estado': 'pendiente'},
            {'id_job_ejecucion': 2, 'id_campana': 2, 'tipo': 'recalculo', 'estado': 'corriendo'},
        ],
    )
    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    assert len(app_test.exception) == 0
    assert len(app_test.dataframe) == 1
    # st.dataframe no expone los datos crudos en AppTest de la misma forma que table,
    # pero nos aseguramos que se renderice sin errores.


def test_jobs_reintenta_todos_los_fallidos(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(api_client, 'get_resumen_jobs', lambda: [])
    llamadas_a_reintentar_fallidos = []
    monkeypatch.setattr(
        api_client,
        'reintentar_fallidos',
        lambda: llamadas_a_reintentar_fallidos.append(1) or {'total_reintentados': 2},
    )
    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    boton_reintentar_fallidos = next(boton for boton in app_test.button if boton.label == 'Reintentar fallidos')
    boton_reintentar_fallidos.click().run()
    assert len(llamadas_a_reintentar_fallidos) == 1
    assert len(app_test.success) == 1


def test_jobs_actualiza_estado(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(api_client, 'get_resumen_jobs', lambda: [])
    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    boton_actualizar = next(boton for boton in app_test.button if boton.label == 'Actualizar estado')
    boton_actualizar.click().run()
    assert len(app_test.exception) == 0


def test_jobs_muestra_boton_de_reintentar_solo_para_fallidos(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'get_resumen_jobs',
        lambda: [
            {'id_job_ejecucion': 1, 'id_campana': 1, 'estado': 'fallido'},
            {'id_job_ejecucion': 2, 'id_campana': 2, 'estado': 'exitoso'},
        ],
    )
    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    etiquetas_de_botones = [boton.label for boton in app_test.button]
    # 'Actualizar estado', 'Reintentar fallidos', y un 'Reintentar' por fila fallida
    assert etiquetas_de_botones.count('Reintentar') == 1


def test_jobs_reintenta_al_hacer_click_en_reintentar_individual(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'get_resumen_jobs',
        lambda: [{'id_job_ejecucion': 1, 'id_campana': 1, 'estado': 'fallido'}],
    )
    llamadas_a_reintentar = []
    monkeypatch.setattr(api_client, 'reintentar_job', lambda id_job: llamadas_a_reintentar.append(id_job))

    app_test = AppTest.from_file('views/jobs.py')
    app_test.run()
    boton_reintentar = next(boton for boton in app_test.button if boton.label == 'Reintentar')
    boton_reintentar.click().run()

    assert llamadas_a_reintentar == [1]
    assert len(app_test.success) == 1
