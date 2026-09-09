"""Campañas: proxy a Retool (Tarea 7), alta y listado (Tarea 8), fechas de hitos (Tarea 9)."""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.services import eventos as eventos_service
from src.services import jobs as jobs_service
from src.services.configuracion import get_vigente

COLUMNAS_CAMPANA = 'id_campana, id_claw, cliente, nombre, inicio_campana, fecha_alta'


def listar_campanas_fda_retool(retool_engine: Engine) -> list[dict]:
    """Consulta `kam_campanas` en Retool DB y filtra las campañas del cliente FDA.

    Args:
        retool_engine: engine de SQLAlchemy hacia Retool DB (ver
            `clients.get_retool_engine`).

    Returns:
        Lista de campañas FDA (`id_claw`, `campana`, `cliente`, `cliente_clave`,
        `inicio_campana`), ordenadas por `inicio_campana` descendente (más
        reciente primero).
    """
    with retool_engine.connect() as connection:
        result_rows = connection.execute(
            text(
                'SELECT id_claw, nombre_claw AS campana, nombre_cliente AS cliente, '
                'cliente AS cliente_clave, inicio_campana '
                "FROM kam_campanas WHERE cliente = 'FDA' ORDER BY inicio_campana DESC"
            )
        )
        return [dict(row._mapping) for row in result_rows]


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


def list_eventos_de_campana(engine: Engine, id_campana: int) -> list[dict]:
    """Lista el catálogo completo de hitos FDA con la fecha capturada para una campaña (si existe).

    Args:
        engine: engine de SQLAlchemy.
        id_campana: campaña a consultar.

    Returns:
        Lista de dicts con `id_evento`, `codigo`, `nombre`, `fecha` (`None` si no se
        ha capturado) y `actualizado_en` — incluye los hitos aún no capturados, para
        que el formulario muestre cuáles faltan.
    """
    with engine.connect() as connection:
        result_rows = connection.execute(
            text(
                'SELECT ev.id_evento AS id_evento, ev.codigo, ev.nombre, ce.fecha, ce.actualizado_en '
                'FROM dtdcfdab_evento ev '
                'LEFT JOIN dtdcfdab_campana_evento ce '
                '  ON ce.id_evento = ev.id_evento AND ce.id_campana = :id_campana '
                'ORDER BY ev.orden'
            ),
            {'id_campana': id_campana},
        )
        return [dict(row._mapping) for row in result_rows]


def upsert_evento_de_campana(engine: Engine, id_campana: int, codigo_evento: str, fecha: datetime) -> dict:
    """Captura o corrige la fecha de un hito FDA para una campaña.

    Args:
        engine: engine de SQLAlchemy.
        id_campana: campaña a la que pertenece el hito.
        codigo_evento: slug del evento en el catálogo (ver `dtdcfdab_evento.codigo`).
        fecha: fecha capturada para ese hito.

    Returns:
        Dict con `id_evento`, `codigo`, `nombre`, `fecha` y `actualizado_en` (el
        timestamp real del upsert, no la `fecha` capturada).

    Raises:
        ValueError: si `codigo_evento` no existe en el catálogo.
    """
    catalogo_eventos = {evento['codigo']: evento for evento in eventos_service.list_eventos(engine)}
    if codigo_evento not in catalogo_eventos:
        raise ValueError(f'codigo_evento desconocido: {codigo_evento}')
    evento_del_catalogo = catalogo_eventos[codigo_evento]
    id_evento = evento_del_catalogo['id_evento']

    with engine.begin() as connection:
        fila_ya_existe = connection.execute(
            text('SELECT 1 FROM dtdcfdab_campana_evento WHERE id_campana = :id_campana AND id_evento = :id_evento'),
            {'id_campana': id_campana, 'id_evento': id_evento},
        ).first()

        ahora = datetime.now(timezone.utc)
        if fila_ya_existe:
            connection.execute(
                text(
                    'UPDATE dtdcfdab_campana_evento SET fecha = :fecha, actualizado_en = :ahora '
                    'WHERE id_campana = :id_campana AND id_evento = :id_evento'
                ),
                {'fecha': fecha, 'ahora': ahora, 'id_campana': id_campana, 'id_evento': id_evento},
            )
        else:
            connection.execute(
                text(
                    'INSERT INTO dtdcfdab_campana_evento (id_campana, id_evento, fecha, actualizado_en) '
                    'VALUES (:id_campana, :id_evento, :fecha, :ahora)'
                ),
                {'id_campana': id_campana, 'id_evento': id_evento, 'fecha': fecha, 'ahora': ahora},
            )

    return {
        'id_evento': id_evento,
        'codigo': codigo_evento,
        'nombre': evento_del_catalogo['nombre'],
        'fecha': fecha,
        'actualizado_en': ahora,
    }
