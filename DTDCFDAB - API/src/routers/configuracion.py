"""Router de configuración del método (lectura — POST en la Tarea 10)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.configuracion import ConfiguracionCreateIn, ConfiguracionCreateOut, ConfiguracionOut
from src.security import require_api_key
from src.services import configuracion, jobs

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/configuracion/vigente', response_model=ConfiguracionOut)
def get_configuracion_vigente() -> dict:
    """Obtiene la configuración vigente.

    Returns:
        `ConfiguracionOut` de la combinación vigente.

    Raises:
        HTTPException: 404 si ninguna configuración está marcada vigente.
    """
    engine = clients.get_db_engine()
    try:
        configuracion_vigente = configuracion.get_vigente(engine)
    finally:
        engine.dispose()
    if configuracion_vigente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Sin configuracion vigente')
    return configuracion_vigente


@router.get('/configuracion', response_model=list[ConfiguracionOut])
def get_configuracion_historial() -> list[dict]:
    """Lista el historial de combinaciones de parámetros ya usadas.

    Returns:
        Lista de `ConfiguracionOut`, más reciente primero.
    """
    engine = clients.get_db_engine()
    try:
        return configuracion.list_configuraciones(engine)
    finally:
        engine.dispose()


@router.post('/configuracion', response_model=ConfiguracionCreateOut)
def post_configuracion(body: ConfiguracionCreateIn) -> dict:
    """Crea una combinación de parámetros nueva, la marca vigente, y encola el recálculo global.

    Args:
        body: los 6 parámetros del método más un `nombre` opcional.

    Returns:
        `ConfiguracionCreateOut` con la configuración, el `id_lote` del recálculo,
        y cuántas campañas quedaron encoladas.
    """
    engine = clients.get_db_engine()
    try:
        resultado_creacion = configuracion.crear_y_marcar_vigente(
            engine, nombre=body.nombre, porcentaje_fin=body.porcentaje_fin, porcentaje_inicio=body.porcentaje_inicio,
            porcentaje_bloque_minimo=body.porcentaje_bloque_minimo, hueco_entregas_dias=body.hueco_entregas_dias,
            desfase_rescate_dias=body.desfase_rescate_dias, cobertura_aviso=body.cobertura_aviso,
        )
    finally:
        engine.dispose()

    tasks_client = clients.get_tasks_client()
    for job_de_recalculo in resultado_creacion['jobs']:
        jobs.encolar_job(tasks_client, job_de_recalculo['id_job_ejecucion'])

    return {
        'configuracion': resultado_creacion['configuracion'],
        'id_lote': resultado_creacion['id_lote'],
        'total_campanas': len(resultado_creacion['jobs']),
    }
