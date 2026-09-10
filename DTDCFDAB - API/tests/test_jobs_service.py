from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from src import config
from src.services.jobs import (
    CAMPOS_DECIMAL_DE_CONFIGURACION,
    _configuracion_con_floats,
    crear_job,
    ejecutar_job,
    encolar_job,
    get_job,
    get_ultimo_job_de_campana,
    list_jobs_activos,
    list_jobs_por_lote,
    reintentar,
    reintentar_fallidos,
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


def test_configuracion_con_floats_convierte_decimales_de_mysql():
    # MySQL devuelve `decimal.Decimal` para columnas DECIMAL cuando se consulta con
    # SQL crudo -- este es el tipo real que llega desde dtdcfdab_configuracion, no
    # el `float` que usan las demás pruebas (esas corren contra SQLite/REAL, que ya
    # devuelve float y por eso nunca hubieran agarrado este bug).
    configuracion_con_decimales = {
        campo: Decimal('0.622') for campo in CAMPOS_DECIMAL_DE_CONFIGURACION
    }
    configuracion_con_decimales['nombre'] = 'v1'

    resultado = _configuracion_con_floats(configuracion_con_decimales)

    for campo in CAMPOS_DECIMAL_DE_CONFIGURACION:
        assert resultado[campo] == 0.622
        assert isinstance(resultado[campo], float)
    assert resultado['nombre'] == 'v1'


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


def test_list_jobs_activos_regresa_solo_pendiente_y_corriendo(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_pendiente = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    job_exitoso = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    job_corriendo = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE dtdcfdab_job_ejecucion SET estado = 'exitoso' WHERE id_job_ejecucion = :id_job_ejecucion"),
            {'id_job_ejecucion': job_exitoso['id_job_ejecucion']},
        )
        connection.execute(
            text("UPDATE dtdcfdab_job_ejecucion SET estado = 'corriendo' WHERE id_job_ejecucion = :id_job_ejecucion"),
            {'id_job_ejecucion': job_corriendo['id_job_ejecucion']},
        )

    resultado = list_jobs_activos(engine)

    ids_regresados = {job['id_job_ejecucion'] for job in resultado}
    assert ids_regresados == {job_pendiente['id_job_ejecucion'], job_corriendo['id_job_ejecucion']}


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


def _marcar_fallido(engine, id_job_ejecucion: int) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE dtdcfdab_job_ejecucion SET estado = 'fallido' WHERE id_job_ejecucion = :id_job_ejecucion"),
            {'id_job_ejecucion': id_job_ejecucion},
        )


def _marcar_exitoso(engine, id_job_ejecucion: int) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE dtdcfdab_job_ejecucion SET estado = 'exitoso' WHERE id_job_ejecucion = :id_job_ejecucion"),
            {'id_job_ejecucion': id_job_ejecucion},
        )


def test_reintentar_fallidos_reencola_la_campana_que_sigue_fallando(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_fallido = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    _marcar_fallido(engine, job_fallido['id_job_ejecucion'])

    tasks_client = MagicMock()
    tasks_client.queue_path.return_value = 'projects/p/locations/l/queues/q'

    total_reintentados = reintentar_fallidos(engine, tasks_client)

    assert total_reintentados == 1
    tasks_client.create_task.assert_called_once()
    assert get_ultimo_job_de_campana(engine, id_campana)['estado'] == 'pendiente'


def test_reintentar_fallidos_ignora_fallo_ya_resuelto_por_un_reintento_posterior(engine):
    # Una campana con un fallo VIEJO ya resuelto (el job mas reciente es exitoso) no debe
    # reintentarse de nuevo -- solo cuenta un fallo vigente (el ultimo job de la campana).
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_viejo_fallido = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    _marcar_fallido(engine, job_viejo_fallido['id_job_ejecucion'])
    job_reintento_exitoso = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    _marcar_exitoso(engine, job_reintento_exitoso['id_job_ejecucion'])

    tasks_client = MagicMock()

    total_reintentados = reintentar_fallidos(engine, tasks_client)

    assert total_reintentados == 0
    tasks_client.create_task.assert_not_called()


def test_reintentar_fallidos_sin_fallidos_regresa_cero(engine):
    tasks_client = MagicMock()
    assert reintentar_fallidos(engine, tasks_client) == 0
    tasks_client.create_task.assert_not_called()


def _sembrar_dependencias_de_ejecucion(engine):
    id_campana, id_configuracion = _sembrar_campana_y_configuracion(engine)
    job_creado = crear_job(engine, id_campana=id_campana, id_configuracion=id_configuracion, tipo='alta')
    return job_creado['id_job_ejecucion'], id_campana, id_configuracion


def _lanzar_error_de_claw(**kwargs):
    raise ValueError('Claw no devolvió escaneos de Pick & Pack para id_claw=229.')


def test_ejecutar_job_marca_fallido_si_snapshot_campana_lanza_error(engine, monkeypatch):
    import src.services.jobs as jobs_module

    id_job_ejecucion, _, _ = _sembrar_dependencias_de_ejecucion(engine)
    monkeypatch.setattr(jobs_module.snapshot_campana, 'calcular_snapshot_campana', _lanzar_error_de_claw)

    resultado = ejecutar_job(engine, id_job_ejecucion, claw_client=None, retool_engine=None)

    assert resultado['estado'] == 'fallido'
    assert 'Pick & Pack' in resultado['error']
    assert resultado['terminado_en'] is not None


def test_ejecutar_job_marca_exitoso_y_escribe_snapshot(engine, monkeypatch):
    import src.services.jobs as jobs_module

    id_job_ejecucion, id_campana, id_configuracion = _sembrar_dependencias_de_ejecucion(engine)
    resultado_falso_del_etl = {'numero_envios': 10, 'numero_folios': 5}
    monkeypatch.setattr(
        jobs_module.snapshot_campana, 'calcular_snapshot_campana', lambda **kwargs: resultado_falso_del_etl
    )

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
