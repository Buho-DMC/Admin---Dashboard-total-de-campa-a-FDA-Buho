"""Ciclo de vida de los jobs de ETL: crear, consultar, encolar y reintentar."""

from google.cloud import tasks_v2
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src import config

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
            'url': f'{config.API_BASE_URL_DTDCFDAB}/jobs/{id_job_ejecucion}/ejecutar',
            'headers': {'X-API-Key': config.API_KEY_DTDCFDAB, 'Content-Type': 'application/json'},
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
