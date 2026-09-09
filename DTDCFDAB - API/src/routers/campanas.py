"""Router de campañas: proxy Retool (Tarea 7), alta/listado (Tarea 8), hitos (Tarea 9), job (Tarea 12)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.campanas import (
    CampanaAltaIn,
    CampanaAltaOut,
    CampanaEventoOut,
    CampanaEventoUpsertIn,
    CampanaOut,
    CampanaRetoolOut,
)
from src.models.jobs import JobOut
from src.security import require_api_key
from src.services import campanas, jobs

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/campanas/retool', response_model=list[CampanaRetoolOut])
def get_campanas_retool() -> list[dict]:
    """Lista las campañas FDA disponibles en Retool, para el selector de alta.

    Returns:
        Lista de `CampanaRetoolOut`.

    Raises:
        HTTPException: 502 si Retool no responde o responde con error.
    """
    retool_client = clients.get_retool_client()
    try:
        return campanas.listar_campanas_fda_retool(retool_client)
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    finally:
        retool_client.close()


@router.post('/campanas', response_model=CampanaAltaOut)
def post_campanas(body: CampanaAltaIn) -> dict:
    """Da de alta una campaña nueva y encola el job de ETL correspondiente.

    Args:
        body: `id_claw`, `cliente`, `nombre`, `inicio_campana` y los `milestones` capturados.

    Returns:
        `CampanaAltaOut` con la campaña insertada y el job encolado.

    Raises:
        HTTPException: 409 si la campaña ya fue dada de alta, si un `codigo_evento`
            no existe en el catálogo, o si no hay configuración vigente.
    """
    engine = clients.get_db_engine()
    try:
        resultado_alta = campanas.dar_de_alta(
            engine,
            id_claw=body.id_claw,
            cliente=body.cliente,
            nombre=body.nombre,
            inicio_campana=body.inicio_campana,
            milestones=[milestone.model_dump() for milestone in body.milestones],
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    finally:
        engine.dispose()

    tasks_client = clients.get_tasks_client()
    jobs.encolar_job(tasks_client, resultado_alta['job']['id_job_ejecucion'])
    return resultado_alta


@router.get('/campanas', response_model=list[CampanaOut])
def get_campanas() -> list[dict]:
    """Lista las campañas ya dadas de alta.

    Returns:
        Lista de `CampanaOut`, ordenada por `inicio_campana` descendente.
    """
    engine = clients.get_db_engine()
    try:
        return campanas.list_campanas(engine)
    finally:
        engine.dispose()


@router.get('/campanas/{id_campana}', response_model=CampanaOut)
def get_campana_detalle(id_campana: int) -> dict:
    """Obtiene el detalle de una campaña dada de alta.

    Args:
        id_campana: id interno de la campaña.

    Returns:
        `CampanaOut`.

    Raises:
        HTTPException: 404 si la campaña no existe.
    """
    engine = clients.get_db_engine()
    try:
        campana_encontrada = campanas.get_campana(engine, id_campana)
    finally:
        engine.dispose()
    if campana_encontrada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Campana no encontrada')
    return campana_encontrada


@router.get('/campanas/{id_campana}/eventos', response_model=list[CampanaEventoOut])
def get_campana_eventos(id_campana: int) -> list[dict]:
    """Lista el catálogo de hitos FDA con la fecha capturada (o pendiente) de una campaña.

    Args:
        id_campana: id de la campaña.

    Returns:
        Lista de `CampanaEventoOut`.
    """
    engine = clients.get_db_engine()
    try:
        return campanas.list_eventos_de_campana(engine, id_campana)
    finally:
        engine.dispose()


@router.put('/campanas/{id_campana}/eventos/{codigo_evento}', response_model=CampanaEventoOut)
def put_campana_evento(id_campana: int, codigo_evento: str, body: CampanaEventoUpsertIn) -> dict:
    """Captura o corrige la fecha de un hito FDA para una campaña.

    Args:
        id_campana: id de la campaña.
        codigo_evento: slug del evento en el catálogo.
        body: la `fecha` a capturar.

    Returns:
        `CampanaEventoOut` con el hito actualizado.

    Raises:
        HTTPException: 400 si `codigo_evento` no existe en el catálogo.
    """
    engine = clients.get_db_engine()
    try:
        return campanas.upsert_evento_de_campana(engine, id_campana, codigo_evento, body.fecha)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    finally:
        engine.dispose()


@router.get('/campanas/{id_campana}/job', response_model=JobOut)
def get_campana_job(id_campana: int) -> dict:
    """Obtiene el job más reciente de una campaña (para bloquear la UI mientras corre).

    Args:
        id_campana: id de la campaña.

    Returns:
        `JobOut` del job más reciente.

    Raises:
        HTTPException: 404 si la campaña nunca tuvo un job.
    """
    engine = clients.get_db_engine()
    try:
        job_encontrado = jobs.get_ultimo_job_de_campana(engine, id_campana)
    finally:
        engine.dispose()
    if job_encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Sin jobs para esta campana')
    return job_encontrado
