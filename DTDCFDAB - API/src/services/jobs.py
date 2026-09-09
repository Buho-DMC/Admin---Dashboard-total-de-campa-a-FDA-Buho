"""Ciclo de vida de los jobs de ETL: crear, consultar, encolar y reintentar."""

from datetime import datetime, timezone

from google.cloud import tasks_v2
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src import config
from src.services import snapshot_campana

COLUMNAS_JOB = (
    'id_job_ejecucion, id_campana, id_lote, id_configuracion, tipo, estado, '
    'iniciado_en, terminado_en, error'
)


def crear_job(
    engine: Engine, id_campana: int, id_configuracion: int, tipo: str, id_lote: str | None = None
) -> dict:
    """Inserta una fila `job_ejecucion` en estado `pendiente`.

    Args:
        engine: engine de SQLAlchemy.
        id_campana: campaña a la que pertenece el job.
        id_configuracion: combinación de parámetros con la que va a correr el ETL.
        tipo: `'alta'` o `'recalculo'`.
        id_lote: UUID que agrupa un recálculo global; `None` para una alta individual.

    Returns:
        Dict con la fila insertada.
    """
    with engine.begin() as connection:
        insert_result = connection.execute(
            text(
                'INSERT INTO dtdcfdab_job_ejecucion (id_campana, id_lote, id_configuracion, tipo, estado) '
                "VALUES (:id_campana, :id_lote, :id_configuracion, :tipo, 'pendiente')"
            ),
            {'id_campana': id_campana, 'id_lote': id_lote, 'id_configuracion': id_configuracion, 'tipo': tipo},
        )
        nuevo_id_job_ejecucion = insert_result.lastrowid
        inserted_row = connection.execute(
            text(f'SELECT {COLUMNAS_JOB} FROM dtdcfdab_job_ejecucion WHERE id_job_ejecucion = :id_job_ejecucion'),
            {'id_job_ejecucion': nuevo_id_job_ejecucion},
        ).mappings().one()
        return dict(inserted_row)


def get_job(engine: Engine, id_job_ejecucion: int) -> dict | None:
    """Obtiene un job por su id.

    Args:
        engine: engine de SQLAlchemy.
        id_job_ejecucion: id del job.

    Returns:
        Dict con la fila, o `None` si no existe.
    """
    with engine.connect() as connection:
        job_row = connection.execute(
            text(f'SELECT {COLUMNAS_JOB} FROM dtdcfdab_job_ejecucion WHERE id_job_ejecucion = :id_job_ejecucion'),
            {'id_job_ejecucion': id_job_ejecucion},
        ).mappings().first()
        return dict(job_row) if job_row else None


def list_jobs_por_lote(engine: Engine, id_lote: str) -> list[dict]:
    """Lista todos los jobs de un lote de recálculo global.

    Args:
        engine: engine de SQLAlchemy.
        id_lote: UUID del lote.

    Returns:
        Lista de dicts, ordenada por `id_job_ejecucion` — sirve para mostrar
        progreso tipo "3 de 19 listas".
    """
    with engine.connect() as connection:
        result_rows = connection.execute(
            text(f'SELECT {COLUMNAS_JOB} FROM dtdcfdab_job_ejecucion WHERE id_lote = :id_lote ORDER BY id_job_ejecucion'),
            {'id_lote': id_lote},
        )
        return [dict(row._mapping) for row in result_rows]


def get_ultimo_job_de_campana(engine: Engine, id_campana: int) -> dict | None:
    """Obtiene el job más reciente de una campaña (para bloquear la UI mientras corre).

    Args:
        engine: engine de SQLAlchemy.
        id_campana: campaña a consultar.

    Returns:
        Dict con el job más reciente, o `None` si la campaña nunca tuvo uno.
    """
    with engine.connect() as connection:
        job_row = connection.execute(
            text(
                f'SELECT {COLUMNAS_JOB} FROM dtdcfdab_job_ejecucion WHERE id_campana = :id_campana '
                'ORDER BY id_job_ejecucion DESC LIMIT 1'
            ),
            {'id_campana': id_campana},
        ).mappings().first()
        return dict(job_row) if job_row else None


def encolar_job(tasks_client: tasks_v2.CloudTasksClient, id_job_ejecucion: int) -> None:
    """Encola una tarea de Cloud Tasks que llama de vuelta a `/jobs/{id}/ejecutar`.

    Args:
        tasks_client: cliente de Cloud Tasks (ver `clients.get_tasks_client`).
        id_job_ejecucion: id del job a ejecutar.

    Returns:
        None.
    """
    queue_path = tasks_client.queue_path(config.GCP_PROJECT_ID, config.GCP_LOCATION, config.TASKS_QUEUE)
    task_definition = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': f'{config.API_BASE_URL_DTDC_FDA_BUHO}/jobs/{id_job_ejecucion}/ejecutar',
            'headers': {'X-API-Key': config.API_KEY_DTDC_FDA_BUHO, 'Content-Type': 'application/json'},
            'body': b'{}',
        }
    }
    tasks_client.create_task(request={'parent': queue_path, 'task': task_definition})


def reintentar(engine: Engine, tasks_client: tasks_v2.CloudTasksClient, id_job_ejecucion: int) -> dict | None:
    """Reencola manualmente un job fallido: crea una fila nueva y la encola.

    Args:
        engine: engine de SQLAlchemy.
        tasks_client: cliente de Cloud Tasks.
        id_job_ejecucion: id del job original a reintentar.

    Returns:
        Dict con el job nuevo, o `None` si `id_job_ejecucion` no existe.
    """
    job_original = get_job(engine, id_job_ejecucion)
    if job_original is None:
        return None
    job_nuevo = crear_job(
        engine,
        id_campana=job_original['id_campana'],
        id_configuracion=job_original['id_configuracion'],
        tipo=job_original['tipo'],
        id_lote=job_original['id_lote'],
    )
    encolar_job(tasks_client, job_nuevo['id_job_ejecucion'])
    return job_nuevo


def ejecutar_job(engine: Engine, id_job_ejecucion: int, claw_client, retool_engine) -> dict:
    """Ejecuta el ETL real de un job: descarga fuentes, corre Política D, guarda el snapshot.

    Args:
        engine: engine de SQLAlchemy.
        id_job_ejecucion: id del job a ejecutar.
        claw_client: cliente HTTP hacia Claw (ver `clients.get_claw_client`).
        retool_engine: engine hacia Retool DB.

    Returns:
        Dict con el job en su estado final (`'exitoso'` o `'fallido'`).

    Raises:
        ValueError: si `id_job_ejecucion` no existe.

    Note:
        Un fallo de `snapshot_campana.calcular_snapshot_campana` se captura y
        marca el job `'fallido'` con el mensaje de error — nunca se propaga
        como excepción, para que Cloud Tasks no reintente solo (el reintento
        es manual, ver spec §3).
    """
    job_a_ejecutar = get_job(engine, id_job_ejecucion)
    if job_a_ejecutar is None:
        raise ValueError(f'Job no encontrado: {id_job_ejecucion}')

    ahora = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE dtdcfdab_job_ejecucion SET estado = 'corriendo', iniciado_en = :ahora "
                'WHERE id_job_ejecucion = :id_job_ejecucion'
            ),
            {'ahora': ahora, 'id_job_ejecucion': id_job_ejecucion},
        )
        id_claw = connection.execute(
            text('SELECT id_claw FROM dtdcfdab_campana WHERE id_campana = :id_campana'),
            {'id_campana': job_a_ejecutar['id_campana']},
        ).scalar_one()
        fila_configuracion = connection.execute(
            text(
                'SELECT porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, hueco_entregas_dias, '
                'desfase_rescate_dias, cobertura_aviso FROM dtdcfdab_configuracion WHERE id_configuracion = :id_configuracion'
            ),
            {'id_configuracion': job_a_ejecutar['id_configuracion']},
        ).mappings().one()

    try:
        resultado_del_etl = snapshot_campana.calcular_snapshot_campana(
            id_claw=id_claw,
            configuracion=dict(fila_configuracion),
            claw_client=claw_client,
            retool_engine=retool_engine,
        )
    except Exception as error:
        terminado_en = datetime.now(timezone.utc)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE dtdcfdab_job_ejecucion SET estado = 'fallido', terminado_en = :terminado_en, "
                    'error = :error WHERE id_job_ejecucion = :id_job_ejecucion'
                ),
                {'terminado_en': terminado_en, 'error': str(error), 'id_job_ejecucion': id_job_ejecucion},
            )
        return get_job(engine, id_job_ejecucion)

    terminado_en = datetime.now(timezone.utc)
    columnas_del_resultado = ', '.join(resultado_del_etl.keys())
    placeholders_del_resultado = ', '.join(f':{nombre_columna}' for nombre_columna in resultado_del_etl.keys())
    with engine.begin() as connection:
        connection.execute(
            text(
                f'INSERT INTO dtdcfdab_campana_snapshot (id_campana, id_configuracion, {columnas_del_resultado}, calculado_en) '
                f'VALUES (:id_campana, :id_configuracion, {placeholders_del_resultado}, :calculado_en)'
            ),
            {
                'id_campana': job_a_ejecutar['id_campana'], 'id_configuracion': job_a_ejecutar['id_configuracion'],
                'calculado_en': terminado_en, **resultado_del_etl,
            },
        )
        connection.execute(
            text(
                "UPDATE dtdcfdab_job_ejecucion SET estado = 'exitoso', terminado_en = :terminado_en "
                'WHERE id_job_ejecucion = :id_job_ejecucion'
            ),
            {'terminado_en': terminado_en, 'id_job_ejecucion': id_job_ejecucion},
        )
    return get_job(engine, id_job_ejecucion)
