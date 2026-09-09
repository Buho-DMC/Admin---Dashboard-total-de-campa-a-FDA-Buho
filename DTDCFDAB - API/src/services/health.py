"""Chequeos de salud: DB y Claw alcanzables."""

import httpx
from sqlalchemy import text
from sqlalchemy.engine import Engine


def check_database(engine: Engine) -> str:
    """Verifica que la base de datos responda con un `SELECT 1`.

    Args:
        engine: engine de SQLAlchemy ya configurado.

    Returns:
        `'ok'` si la query se ejecuta sin error.
    """
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return 'ok'


def check_claw(claw_client: httpx.Client) -> str:
    """Verifica si el endpoint base de Claw responde.

    Args:
        claw_client: cliente HTTP de Claw (ver `clients.get_claw_client`).

    Returns:
        `'no configurado'` si el cliente no tiene `base_url`; `'reachable'` si
        responde con un status menor a 500; `'degraded'` si responde con 5xx;
        `'no disponible'` si la conexión falla por completo.
    """
    if not str(claw_client.base_url):
        return 'no configurado'
    try:
        response = claw_client.get('/', timeout=5.0)
    except httpx.HTTPError:
        return 'no disponible'
    return 'reachable' if response.status_code < 500 else 'degraded'
