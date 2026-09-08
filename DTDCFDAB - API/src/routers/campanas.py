"""Router de campañas: proxy Retool (Tarea 7), alta/listado (Tarea 8), hitos (Tarea 9), job (Tarea 12)."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.campanas import CampanaRetoolOut
from src.security import require_api_key
from src.services import campanas

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
