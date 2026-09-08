"""Catálogo de eventos (hitos FDA)."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def list_eventos(engine: Engine) -> list[dict]:
    """Lista el catálogo completo de hitos FDA, ordenado cronológicamente.

    Args:
        engine: engine de SQLAlchemy.

    Returns:
        Lista de dicts con `id_evento`, `codigo`, `nombre`, `origen`, `rol`, `orden`.
    """
    with engine.connect() as connection:
        result_rows = connection.execute(
            text('SELECT id_evento, codigo, nombre, origen, rol, orden FROM dtdcfdab_evento ORDER BY orden')
        )
        return [dict(row._mapping) for row in result_rows]


def create_evento(engine: Engine, codigo: str, nombre: str, orden: int) -> dict:
    """Agrega un milestone nuevo al catálogo de eventos.

    Args:
        engine: engine de SQLAlchemy.
        codigo: slug único y estable del evento, ej. `entrega_promociones_ac`.
        nombre: nombre mostrado en la UI.
        orden: posición cronológica para Gantt/timeline/Metodología.

    Returns:
        Dict con la fila insertada, incluyendo el `id_evento` generado.
    """
    with engine.begin() as connection:
        insert_result = connection.execute(
            text(
                "INSERT INTO dtdcfdab_evento (codigo, nombre, origen, rol, orden) "
                "VALUES (:codigo, :nombre, 'manual', 'hito', :orden)"
            ),
            {'codigo': codigo, 'nombre': nombre, 'orden': orden},
        )
        nuevo_id_evento = insert_result.lastrowid
        inserted_row = connection.execute(
            text('SELECT id_evento, codigo, nombre, origen, rol, orden FROM dtdcfdab_evento WHERE id_evento = :id_evento'),
            {'id_evento': nuevo_id_evento},
        ).mappings().one()
        return dict(inserted_row)
