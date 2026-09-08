"""Router del catálogo de eventos."""

from fastapi import APIRouter, Depends

from src import clients
from src.models.eventos import EventoCreateIn, EventoOut
from src.security import require_api_key
from src.services import eventos

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/eventos', response_model=list[EventoOut])
def get_eventos() -> list[dict]:
    """Lista el catálogo completo de hitos FDA.

    Returns:
        Lista de `EventoOut`, ordenada cronológicamente.
    """
    engine = clients.get_db_engine()
    try:
        return eventos.list_eventos(engine)
    finally:
        engine.dispose()


@router.post('/eventos', response_model=EventoOut)
def post_eventos(body: EventoCreateIn) -> dict:
    """Agrega un milestone nuevo al catálogo.

    Args:
        body: `codigo`, `nombre` y `orden` del nuevo evento.

    Returns:
        El `EventoOut` recién creado.
    """
    engine = clients.get_db_engine()
    try:
        return eventos.create_evento(engine, codigo=body.codigo, nombre=body.nombre, orden=body.orden)
    finally:
        engine.dispose()
