"""Configuración de parámetros del método (Política D)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.services import jobs as jobs_service

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


def crear_y_marcar_vigente(
    engine: Engine, nombre: str | None, porcentaje_fin: float, porcentaje_inicio: float,
    porcentaje_bloque_minimo: float, hueco_entregas_dias: float, desfase_rescate_dias: float,
    cobertura_aviso: float,
) -> dict:
    """Crea una combinación de parámetros nueva, la marca vigente, y encola el recálculo global.

    Args:
        engine: engine de SQLAlchemy.
        nombre: etiqueta opcional para la combinación, ej. `'Politica D v1'`.
        porcentaje_fin: `PCT_FIN` de `etl.ipynb`.
        porcentaje_inicio: `PCT_INICIO` de `etl.ipynb`.
        porcentaje_bloque_minimo: `PCT_BLOQUE_MIN` de `etl.ipynb`.
        hueco_entregas_dias: `HUECO_ENTREGAS_D` de `etl.ipynb`.
        desfase_rescate_dias: `DESFASE_RESCATE_D` de `etl.ipynb`.
        cobertura_aviso: `COBERTURA_AVISO` de `etl.ipynb`.

    Returns:
        Dict `{'configuracion': dict, 'id_lote': str, 'jobs': list[dict]}` — la
        configuración recién creada, el UUID del lote de recálculo, y un job
        `'recalculo'` por cada campaña ya dada de alta (vacío si aún no hay ninguna).
    """
    from src.services import campanas as campanas_service  # import diferido: rompe el ciclo campanas <-> configuracion

    ahora = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(text('UPDATE dtdcfdab_configuracion SET es_vigente = 0 WHERE es_vigente = 1'))
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_configuracion '
                '(nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, hueco_entregas_dias, '
                'desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en) '
                'VALUES (:nombre, :porcentaje_fin, :porcentaje_inicio, :porcentaje_bloque_minimo, '
                ':hueco_entregas_dias, :desfase_rescate_dias, :cobertura_aviso, 1, :creado_en)'
            ),
            {
                'nombre': nombre, 'porcentaje_fin': porcentaje_fin, 'porcentaje_inicio': porcentaje_inicio,
                'porcentaje_bloque_minimo': porcentaje_bloque_minimo, 'hueco_entregas_dias': hueco_entregas_dias,
                'desfase_rescate_dias': desfase_rescate_dias, 'cobertura_aviso': cobertura_aviso, 'creado_en': ahora,
            },
        )

    configuracion_nueva = get_vigente(engine)

    id_lote = str(uuid.uuid4())
    todas_las_campanas = campanas_service.list_campanas(engine)
    jobs_de_recalculo = [
        jobs_service.crear_job(
            engine, id_campana=campana['id_campana'], id_configuracion=configuracion_nueva['id_configuracion'],
            tipo='recalculo', id_lote=id_lote,
        )
        for campana in todas_las_campanas
    ]

    return {'configuracion': configuracion_nueva, 'id_lote': id_lote, 'jobs': jobs_de_recalculo}
