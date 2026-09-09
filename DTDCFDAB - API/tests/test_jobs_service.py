from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from src import config
from src.services.jobs import (
    crear_job,
    ejecutar_job,
    encolar_job,
    get_job,
    get_ultimo_job_de_campana,
    list_jobs_por_lote,
    reintentar,
)


def _sembrar_campana_y_configuracion(engine) -> tuple[int, int]:
    with engine.begin() as connection:
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_campana (id_claw, nombre, inicio_campana, fecha_alta) '
                "VALUES (229, 'FDA AGO26-2', '2026-07-24', '2026-08-01')"
            )
        )
        id_campana = connection.execute(text('SELECT id_campana FROM dtdcfdab_campana')).scalar_one()
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_configuracion '
                '(nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, hueco_entregas_dias, '
                'desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en) '
                "VALUES ('v1', 0.99, 0.01, 0.05, 10, 0.622, 0.95, 1, '2026-01-01')"
            )
        )
        id_configuracion = connection.execute(text('SELECT id_configuracion FROM dtdcfdab_configuracion')).scalar_one()
    return id_campana, id_configuracion


def test_crear_job_inserta_pendiente(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)

    job_creado = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')

    assert job_creado['estado'] == 'pendiente'
    assert job_creado['tipo'] == 'alta'
    assert job_creado['id_lote'] is None
    assert job_creado['id_job_ejecucion'] > 0


def test_crear_job_con_lote(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)

    job_creado = crear_job(
        engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='recalculo', id_lote='lote-1'
    )

    assert job_creado['id_lote'] == 'lote-1'


def test_get_job_no_encontrado_regresa_none(engine):
    assert get_job(engine, 999) is None


def test_get_job_encontrado(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_creado = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')

    assert get_job(engine, job_creado['id_job_ejecucion'])['id_job_ejecucion'] == job_creado['id_job_ejecucion']


def test_list_jobs_por_lote(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='recalculo', id_lote='lote-a')
    crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='recalculo', id_lote='lote-a')
    crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='recalculo', id_lote='lote-b')

    resultado = list_jobs_por_lote(engine, 'lote-a')

    assert len(resultado) == 2


def test_get_ultimo_job_de_campana_regresa_el_mas_reciente(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    segundo_job = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='recalculo')

    resultado = get_ultimo_job_de_campana(engine, id_campana)

    assert resultado['id_job_ejecucion'] == segundo_job['id_job_ejecucion']


def test_get_ultimo_job_de_campana_sin_jobs_regresa_none(engine):
    assert get_ultimo_job_de_campana(engine, 1) is None


def test_encolar_job_crea_tarea_con_headers_correctos(monkeypatch):
    monkeypatch.setattr(config, 'GCP_PROJECT_ID', 'prod-apps-y-computo')
    monkeypatch.setattr(config, 'GCP_LOCATION', 'us-central1')
    monkeypatch.setattr(config, 'TASKS_QUEUE', 'dtdc-fda-buho-jobs')
    monkeypatch.setattr(config, 'API_BASE_URL_DTDC_FDA_BUHO', 'https://dtdcfdab-api.example.com')
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')

    tasks_client = MagicMock()
    tasks_client.queue_path.return_value = 'projects/prod-apps-y-computo/locations/us-central1/queues/dtdc-fda-buho-jobs'

    encolar_job(tasks_client, id_job_ejecucion=42)

    tasks_client.queue_path.assert_called_once_with('prod-apps-y-computo', 'us-central1', 'dtdc-fda-buho-jobs')
    _, keyword_arguments = tasks_client.create_task.call_args
    task_request = keyword_arguments['request']
    assert task_request['parent'] == 'projects/prod-apps-y-computo/locations/us-central1/queues/dtdc-fda-buho-jobs'
    http_request = task_request['task']['http_request']
    assert http_request['url'] == 'https://dtdcfdab-api.example.com/jobs/42/ejecutar'
    assert http_request['headers']['X-API-Key'] == 'secreto'


def test_reintentar_crea_nuevo_job_y_encola(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_original = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')

    tasks_client = MagicMock()
    tasks_client.queue_path.return_value = 'projects/p/locations/l/queues/q'

    job_nuevo = reintentar(engine, tasks_client, job_original['id_job_ejecucion'])

    assert job_nuevo['id_job_ejecucion'] != job_original['id_job_ejecucion']
    assert job_nuevo['id_campana'] == id_campana
    assert job_nuevo['estado'] == 'pendiente'
    tasks_client.create_task.assert_called_once()


def test_reintentar_job_inexistente_regresa_none(engine):
    tasks_client = MagicMock()
    assert reintentar(engine, tasks_client, 999) is None


def _sembrar_dependencias_de_ejecucion(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_creado = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    return job_creado['id_job_ejecucion'], id_campana, id_configuracion


def test_ejecutar_job_marca_fallido_si_politica_d_no_esta_implementada(engine):
    id_job_ejecucion, _, _ = _sembrar_dependencias_de_ejecucion(engine)

    resultado = ejecutar_job(engine, id_job_ejecucion, claw_client=None, retool_engine=None)

    assert resultado['estado'] == 'fallido'
    assert 'Politica D' in resultado['error']
    assert resultado['terminado_en'] is not None


def test_ejecutar_job_marca_exitoso_y_escribe_snapshot(engine, monkeypatch):
    import src.services.jobs as jobs_module

    id_job_ejecucion, id_campana, id_configuracion = _sembrar_dependencias_de_ejecucion(engine)
    resultado_falso_del_etl = {'numero_envios': 10, 'numero_folios': 5}
    monkeypatch.setattr(jobs_module.politica_d, 'calcular', lambda **kwargs: resultado_falso_del_etl)

    resultado = ejecutar_job(engine, id_job_ejecucion, claw_client=None, retool_engine=None)

    assert resultado['estado'] == 'exitoso'
    with engine.connect() as connection:
        fila_del_snapshot = connection.execute(
            text('SELECT numero_envios, numero_folios FROM dtdcfdab_campana_snapshot WHERE id_campana = :id_campana'),
            {'id_campana': id_campana},
        ).mappings().one()
    assert fila_del_snapshot['numero_envios'] == 10
    assert fila_del_snapshot['numero_folios'] == 5


def test_ejecutar_job_inexistente_lanza_valueerror(engine):
    with pytest.raises(ValueError):
        ejecutar_job(engine, 999, claw_client=None, retool_engine=None)
