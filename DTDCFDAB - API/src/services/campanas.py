"""Campañas: proxy a Retool (Tarea 7), alta y listado (Tarea 8), fechas de hitos (Tarea 9)."""

from datetime import datetime

import httpx

from src import config


def _normalizar_campana_retool(raw_campana: dict) -> dict:
    """Convierte una fila cruda del workflow de Retool al shape interno.

    Args:
        raw_campana: dict tal como lo entrega el workflow de Retool.

    Returns:
        Dict con `id_claw`, `campana`, `cliente`, `cliente_clave`, `inicio_campana`
        (como `datetime` o `None`).
    """
    fecha_inicio_cruda = raw_campana.get('inicio_campana')
    fecha_inicio = datetime.fromisoformat(fecha_inicio_cruda.replace('Z', '+00:00')) if fecha_inicio_cruda else None
    return {
        'id_claw': raw_campana['id_claw'],
        'campana': raw_campana['campana'],
        'cliente': raw_campana['cliente'],
        'cliente_clave': raw_campana.get('clave_cliente'),
        'inicio_campana': fecha_inicio,
    }


def listar_campanas_fda_retool(retool_client: httpx.Client) -> list[dict]:
    """Consulta el workflow de Retool y filtra las campañas del cliente FDA.

    Args:
        retool_client: cliente HTTP configurado con el header de Retool (ver
            `clients.get_retool_client`).

    Returns:
        Lista de campañas FDA, normalizadas y ordenadas por `inicio_campana`
        descendente (más reciente primero).

    Raises:
        RuntimeError: si la llamada HTTP falla, o si el workflow responde `ok: false`.
    """
    try:
        retool_response = retool_client.post(config.RETOOL_CAMPANAS_WEBHOOK_URL)
        retool_response.raise_for_status()
    except httpx.HTTPError as error:
        raise RuntimeError(f'No se pudo consultar Retool: {error}') from error

    response_data = retool_response.json()
    if not response_data.get('ok'):
        raise RuntimeError('El workflow de Retool respondio ok=false')

    campanas_fda = [
        _normalizar_campana_retool(raw_campana)
        for raw_campana in response_data.get('campanas', [])
        if raw_campana.get('clave_cliente') == 'FDA'
    ]
    return sorted(campanas_fda, key=lambda campana: campana['inicio_campana'] or datetime.min.replace(tzinfo=None), reverse=True)
