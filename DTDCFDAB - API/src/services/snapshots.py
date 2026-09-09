"""Snapshots de ETL por (campaña, configuración)."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.services.configuracion import get_vigente

COLUMNAS_SNAPSHOT = (
    'id_campana, id_configuracion, '
    'inicio_carga_artes, fin_carga_artes, inicio_carga_preproyectos, fin_carga_preproyectos, '
    'inicio_aprobaciones, fin_aprobaciones, inicio_impresion, fin_impresion, '
    'inicio_precampana, fin_precampana, inicio_pick_pack, fin_pick_pack, '
    'inicio_entregas, fin_entregas, '
    'porcentaje_alcanzado_entregas, ultima_entrega, numero_envios, envios_con_fecha, envios_sin_fecha, '
    'envios_sin_registro_entrega, numero_cajas_pick_pack, numero_folios, numero_odps, numero_actividades, '
    'respuesta_buho_dias, respuesta_fda_dias, folios_invertidos, calculado_en'
)


def get_snapshot(engine: Engine, id_campana: int, id_configuracion: int) -> dict | None:
    """Obtiene el snapshot de una campaña para una combinación de parámetros.

    Args:
        engine: engine de SQLAlchemy.
        id_campana: campaña a consultar.
        id_configuracion: combinación de parámetros con la que se calculó.

    Returns:
        Dict con las 14 fechas Búho y los 13 metadatos, o `None` si aún no se calculó.
    """
    with engine.connect() as connection:
        snapshot_row = connection.execute(
            text(
                f'SELECT {COLUMNAS_SNAPSHOT} FROM dtdcfdab_campana_snapshot '
                'WHERE id_campana = :id_campana AND id_configuracion = :id_configuracion'
            ),
            {'id_campana': id_campana, 'id_configuracion': id_configuracion},
        ).mappings().first()
        return dict(snapshot_row) if snapshot_row else None


def list_snapshots_vigentes(engine: Engine) -> list[dict]:
    """Lista todos los snapshots calculados con la configuración vigente.

    Args:
        engine: engine de SQLAlchemy.

    Returns:
        Lista de dicts — alimenta la vista global "Todas" del dashboard. Lista
        vacía si no hay ninguna configuración vigente.
    """
    configuracion_vigente = get_vigente(engine)
    if configuracion_vigente is None:
        return []
    with engine.connect() as connection:
        result_rows = connection.execute(
            text(f'SELECT {COLUMNAS_SNAPSHOT} FROM dtdcfdab_campana_snapshot WHERE id_configuracion = :id_configuracion'),
            {'id_configuracion': configuracion_vigente['id_configuracion']},
        )
        return [dict(row._mapping) for row in result_rows]
