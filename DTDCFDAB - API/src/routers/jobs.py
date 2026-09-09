"""Router de jobs: consulta de estado y reintento manual (ejecución en la Tarea 13)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.jobs import JobOut
from src.security import require_api_key
from src.services import jobs

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/jobs/{id_job_ejecucion}', response_model=JobOut)
def get_job(id_job_ejecucion: int) -> dict:
    """Obtiene el estado de un job.

    Args:
        id_job_ejecucion: id del job.

    Returns:
        `JobOut`.

    Raises:
        HTTPException: 404 si el job no existe.
    """
    engine = clients.get_db_engine()
    try:
        job_encontrado = jobs.get_job(engine, id_job_ejecucion)
    finally:
        engine.dispose()
    if job_encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job no encontrado')
    return job_encontrado


@router.get('/jobs', response_model=list[JobOut])
def get_jobs(id_lote: str | None = None) -> list[dict]:
    """Lista todos los jobs de un lote de recálculo global.

    Args:
        id_lote: UUID del lote — obligatorio, es el único filtro soportado.

    Returns:
        Lista de `JobOut` del lote — progreso tipo "3 de 19 listas".

    Raises:
        HTTPException: 400 si no se manda `id_lote`.
    """
    if not id_lote:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Falta ?id_lote=')
    engine = clients.get_db_engine()
    try:
        return jobs.list_jobs_por_lote(engine, id_lote)
    finally:
        engine.dispose()


@router.post('/jobs/{id_job_ejecucion}/reintentar', response_model=JobOut)
def post_job_reintentar(id_job_ejecucion: int) -> dict:
    """Reencola manualmente un job fallido.

    Args:
        id_job_ejecucion: id del job original a reintentar.

    Returns:
        `JobOut` del job nuevo, en estado `'pendiente'`.

    Raises:
        HTTPException: 404 si `id_job_ejecucion` no existe.
    """
    engine = clients.get_db_engine()
    tasks_client = clients.get_tasks_client()
    try:
        job_reintentado = jobs.reintentar(engine, tasks_client, id_job_ejecucion)
    finally:
        engine.dispose()
    if job_reintentado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job no encontrado')
    return job_reintentado


@router.post('/jobs/{id_job_ejecucion}/ejecutar', response_model=JobOut)
def post_job_ejecutar(id_job_ejecucion: int) -> dict:
    """Ejecuta el ETL real de un job. Endpoint interno — solo lo invoca Cloud Tasks.

    Args:
        id_job_ejecucion: id del job a ejecutar.

    Returns:
        `JobOut` en su estado final (`'exitoso'` o `'fallido'`).

    Raises:
        HTTPException: 404 si `id_job_ejecucion` no existe.
    """
    engine = clients.get_db_engine()
    claw_picks_client = clients.get_claw_picks_client()
    claw_tracking_client = clients.get_claw_tracking_client()
    try:
        return jobs.ejecutar_job(
            engine, id_job_ejecucion,
            claw_picks_client=claw_picks_client, claw_tracking_client=claw_tracking_client, retool_engine=None,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    finally:
        engine.dispose()
        claw_picks_client.close()
        claw_tracking_client.close()
