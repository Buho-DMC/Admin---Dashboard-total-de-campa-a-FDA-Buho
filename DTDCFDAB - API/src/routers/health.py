"""Router de salud: liveness simple y chequeo profundo."""

from fastapi import APIRouter, Depends

from src import clients
from src.models.common import HealthDeepOut, HealthOut
from src.security import require_api_key
from src.services import health

router = APIRouter()


@router.get('/health', response_model=HealthOut)
def get_health() -> HealthOut:
    """Liveness check simple, sin autenticación.

    Returns:
        `HealthOut(status='ok')` siempre que el proceso esté vivo.
    """
    return HealthOut(status='ok')


@router.get('/health/deep', response_model=HealthDeepOut, dependencies=[Depends(require_api_key)])
def get_health_deep() -> HealthDeepOut:
    """Chequeo profundo: prueba la DB y Claw.

    Returns:
        `HealthDeepOut` con el estado de cada dependencia externa.
    """
    engine = clients.get_db_engine()
    claw_client = clients.get_claw_picks_client()
    try:
        database_status = health.check_database(engine)
        claw_status = health.check_claw(claw_client)
    finally:
        engine.dispose()
        claw_client.close()
    return HealthDeepOut(status='ok', database=database_status, claw=claw_status)
