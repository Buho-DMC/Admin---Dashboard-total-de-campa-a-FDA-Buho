"""Campañas: proxy a Retool (Tarea 7), alta y listado (Tarea 8), fechas de hitos (Tarea 9)."""

from datetime import datetime, timezone

import httpx
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src import config
from src.services import eventos as eventos_service
from src.services import jobs as jobs_service
from src.services.configuracion import get_vigente

COLUMNAS_CAMPANA = 'id_campana, id_claw, cliente, nombre, inicio_campana, fecha_alta'


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


def list_campanas(engine: Engine) -> list[dict]:
    """Lista las campañas ya dadas de alta.

    Args:
        engine: engine de SQLAlchemy.

    Returns:
        Lista de dicts, ordenada por `inicio_campana` descendente.
    """
    with engine.connect() as connection:
        result_rows = connection.execute(
            text(f'SELECT {COLUMNAS_CAMPANA} FROM dtdcfdab_campana ORDER BY inicio_campana DESC')
        )
        return [dict(row._mapping) for row in result_rows]


def get_campana(engine: Engine, id_campana: int) -> dict | None:
    """Obtiene el detalle de una campaña dada de alta.

    Args:
        engine: engine de SQLAlchemy.
        id_campana: id interno de la campaña.

    Returns:
        Dict con la fila, o `None` si no existe.
    """
    with engine.connect() as connection:
        campana_row = connection.execute(
            text(f'SELECT {COLUMNAS_CAMPANA} FROM dtdcfdab_campana WHERE id_campana = :id_campana'),
            {'id_campana': id_campana},
        ).mappings().first()
        return dict(campana_row) if campana_row else None


def dar_de_alta(
    engine: Engine, id_claw: int, cliente: str, nombre: str, inicio_campana: datetime, milestones: list[dict]
) -> dict:
    """Da de alta una campaña: inserta la campaña, sus hitos FDA manuales y encola el ETL.

    Args:
        engine: engine de SQLAlchemy.
        id_claw: id de la campaña en Claw/Retool — único, no se repite entre filas.
        cliente: clave del cliente, ej. `'FDA'`.
        nombre: nombre de la campaña.
        inicio_campana: fecha de inicio informativa (viene de Retool).
        milestones: lista de `{'codigo_evento': str, 'fecha': datetime}` — los hitos
            FDA capturados a mano en el formulario de alta.

    Returns:
        Dict `{'campana': dict, 'job': dict}` — la campaña insertada y el job de
        ETL `'alta'` recién creado, en estado `'pendiente'` (todavía sin encolar en
        Cloud Tasks — eso lo hace el router, que sí tiene el cliente de Cloud Tasks).

    Raises:
        ValueError: si `id_claw` ya fue dado de alta, si algún `codigo_evento` no
            existe en el catálogo, o si no hay ninguna configuración vigente.
    """
    with engine.connect() as connection:
        campana_ya_existe = connection.execute(
            text('SELECT 1 FROM dtdcfdab_campana WHERE id_claw = :id_claw'), {'id_claw': id_claw}
        ).first()
    if campana_ya_existe:
        raise ValueError(f'La campana con id_claw={id_claw} ya fue dada de alta')

    catalogo_eventos = {evento['codigo']: evento['id_evento'] for evento in eventos_service.list_eventos(engine)}
    for milestone in milestones:
        if milestone['codigo_evento'] not in catalogo_eventos:
            raise ValueError(f"codigo_evento desconocido: {milestone['codigo_evento']}")

    configuracion_vigente = get_vigente(engine)
    if configuracion_vigente is None:
        raise ValueError('No hay configuracion vigente — no se puede encolar el ETL de alta')

    ahora = datetime.now(timezone.utc)
    with engine.begin() as connection:
        insert_result = connection.execute(
            text(
                'INSERT INTO dtdcfdab_campana (id_claw, cliente, nombre, inicio_campana, fecha_alta) '
                'VALUES (:id_claw, :cliente, :nombre, :inicio_campana, :fecha_alta)'
            ),
            {'id_claw': id_claw, 'cliente': cliente, 'nombre': nombre, 'inicio_campana': inicio_campana, 'fecha_alta': ahora},
        )
        id_campana = insert_result.lastrowid

        for milestone in milestones:
            connection.execute(
                text(
                    'INSERT INTO dtdcfdab_campana_evento (id_campana, id_evento, fecha, actualizado_en) '
                    'VALUES (:id_campana, :id_evento, :fecha, :actualizado_en)'
                ),
                {
                    'id_campana': id_campana,
                    'id_evento': catalogo_eventos[milestone['codigo_evento']],
                    'fecha': milestone['fecha'],
                    'actualizado_en': ahora,
                },
            )

    job_de_alta = jobs_service.crear_job(engine, id_campana=id_campana, id_configuracion=configuracion_vigente['id_configuracion'], tipo='alta')
    campana_insertada = get_campana(engine, id_campana)
    return {'campana': campana_insertada, 'job': job_de_alta}
