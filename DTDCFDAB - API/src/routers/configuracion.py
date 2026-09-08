"""Router de configuración del método (lectura — POST en la Tarea 10)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.configuracion import ConfiguracionOut
from src.security import require_api_key
from src.services import configuracion

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
