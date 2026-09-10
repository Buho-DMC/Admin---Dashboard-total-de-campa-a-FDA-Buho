"""Tests de pages/jobs.py."""

import streamlit
from streamlit.testing.v1 import AppTest

import api_client


def _sin_autorefresh(monkeypatch):
    monkeypatch.setattr('streamlit_autorefresh.st_autorefresh', lambda **kwargs: 0)


def _capturar_texto_de_progreso(monkeypatch):
    # AppTest (streamlit 1.58) no modela st.progress como elemento
    # introspeccionable — element_tree.py no lo registra en absoluto, a
    # diferencia de otros widgets. Se intercepta la llamada real para
    # capturar su parametro `text` sin tocar el codigo de produccion.
    llamadas_de_progreso = []
    monkeypatch.setattr(streamlit, 'progress', lambda valor, text=None: llamadas_de_progreso.append(text))
    return llamadas_de_progreso


def test_jobs_muestra_info_sin_id_de_lote(monkeypatch):
    _sin_autorefresh(monkeypatch)
    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    assert len(app_test.info) == 1


def test_jobs_muestra_activos_sin_pedir_id_ni_lote(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'list_jobs_activos',
        lambda: [
            {'id_job_ejecucion': 1, 'id_campana': 1, 'tipo': 'alta', 'estado': 'pendiente'},
            {'id_job_ejecucion': 2, 'id_campana': 2, 'tipo': 'recalculo', 'estado': 'corriendo'},
        ],
    )
    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    app_test.radio[0].set_value('Activos ahora').run()
    assert len(app_test.exception) == 0
    assert len(app_test.dataframe) == 1


def test_jobs_muestra_progreso_por_lote(monkeypatch):
    _sin_autorefresh(monkeypatch)
    llamadas_de_progreso = _capturar_texto_de_progreso(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'list_jobs_de_lote',
        lambda id_lote: [
            {'id_job_ejecucion': 1, 'id_campana': 1, 'estado': 'exitoso'},
            {'id_job_ejecucion': 2, 'id_campana': 2, 'estado': 'corriendo'},
        ],
    )
    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    app_test.text_input[0].set_value('lote-1').run()
    assert len(llamadas_de_progreso) == 1
    assert '1 de 2' in llamadas_de_progreso[0]


def test_jobs_muestra_progreso_por_job_individual(monkeypatch):
    _sin_autorefresh(monkeypatch)
    llamadas_de_progreso = _capturar_texto_de_progreso(monkeypatch)
    monkeypatch.setattr(
        api_client, 'get_job', lambda id_job: {'id_job_ejecucion': 9, 'id_campana': 3, 'estado': 'exitoso'}
    )
    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    app_test.radio[0].set_value('Job individual (alta de campaña)').run()
    assert len(llamadas_de_progreso) == 1
    assert '1 de 1' in llamadas_de_progreso[0]


def test_jobs_muestra_boton_de_reintentar_solo_para_fallidos(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'list_jobs_de_lote',
        lambda id_lote: [
            {'id_job_ejecucion': 1, 'id_campana': 1, 'estado': 'fallido'},
            {'id_job_ejecucion': 2, 'id_campana': 2, 'estado': 'exitoso'},
        ],
    )
    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    app_test.text_input[0].set_value('lote-1').run()
    etiquetas_de_botones = [boton.label for boton in app_test.button]
    assert etiquetas_de_botones.count('Reintentar') == 1


def test_jobs_reintenta_al_hacer_click(monkeypatch):
    _sin_autorefresh(monkeypatch)
    monkeypatch.setattr(
        api_client,
        'list_jobs_de_lote',
        lambda id_lote: [{'id_job_ejecucion': 1, 'id_campana': 1, 'estado': 'fallido'}],
    )
    llamadas_a_reintentar = []
    monkeypatch.setattr(api_client, 'reintentar_job', lambda id_job: llamadas_a_reintentar.append(id_job))

    app_test = AppTest.from_file('pages/jobs.py')
    app_test.run()
    app_test.text_input[0].set_value('lote-1').run()
    boton_reintentar = next(boton for boton in app_test.button if boton.label == 'Reintentar')
    boton_reintentar.click().run()

    assert llamadas_a_reintentar == [1]
    assert len(app_test.success) == 1
