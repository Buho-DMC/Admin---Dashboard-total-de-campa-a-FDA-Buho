"""Configuración de parámetros del método (Política D)."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

COLUMNAS_CONFIGURACION = (
    'id_configuracion, nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, '
    'hueco_entregas_dias, desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en'
)


def _normalizar_fila_configuracion(row: dict) -> dict:
    """Convierte `es_vigente` de entero (SQLite) a booleano real.

    Args:
        row: fila cruda leída de la base de datos.

    Returns:
        Copia del dict con `es_vigente` como `bool`.
    """
    normalized_row = dict(row)
    normalized_row['es_vigente'] = bool(normalized_row['es_vigente'])
    return normalized_row


def get_vigente(engine: Engine) -> dict | None:
    """Obtiene la combinación de parámetros vigente.

    Args:
        engine: engine de SQLAlchemy.

    Returns:
        Dict con la configuración vigente, o `None` si ninguna está marcada
        (no debería pasar en producción: hay una semilla `es_vigente=1`).
    """
    with engine.connect() as connection:
        vigente_row = connection.execute(
            text(f'SELECT {COLUMNAS_CONFIGURACION} FROM dtdcfdab_configuracion WHERE es_vigente = 1')
        ).mappings().first()
        return _normalizar_fila_configuracion(vigente_row) if vigente_row else None


def list_configuraciones(engine: Engine) -> list[dict]:
    """Lista el historial de combinaciones de parámetros ya usadas.

    Args:
        engine: engine de SQLAlchemy.

    Returns:
        Lista de dicts, ordenada por `creado_en` descendente (más reciente primero).
    """
    with engine.connect() as connection:
        result_rows = connection.execute(
            text(f'SELECT {COLUMNAS_CONFIGURACION} FROM dtdcfdab_configuracion ORDER BY creado_en DESC')
        )
        return [_normalizar_fila_configuracion(row._mapping) for row in result_rows]
