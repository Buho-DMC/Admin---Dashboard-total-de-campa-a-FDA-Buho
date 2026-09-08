"""Fixtures compartidas: esquema completo en SQLite in-memory."""

import pytest
from sqlalchemy import create_engine, text

ESQUEMA_STATEMENTS = [
    """
    CREATE TABLE dtdcfdab_evento (
        id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        origen TEXT NOT NULL DEFAULT 'manual',
        rol TEXT NOT NULL DEFAULT 'hito',
        orden INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE dtdcfdab_campana (
        id_campana INTEGER PRIMARY KEY AUTOINCREMENT,
        id_claw INTEGER UNIQUE NOT NULL,
        cliente TEXT NOT NULL DEFAULT 'FDA',
        nombre TEXT NOT NULL,
        inicio_campana TEXT NOT NULL,
        fecha_alta TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE dtdcfdab_campana_evento (
        id_campana INTEGER NOT NULL,
        id_evento INTEGER NOT NULL,
        fecha TEXT,
        actualizado_en TEXT,
        PRIMARY KEY (id_campana, id_evento)
    )
    """,
    """
    CREATE TABLE dtdcfdab_configuracion (
        id_configuracion INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        porcentaje_fin REAL NOT NULL,
        porcentaje_inicio REAL NOT NULL,
        porcentaje_bloque_minimo REAL NOT NULL,
        hueco_entregas_dias REAL NOT NULL,
        desfase_rescate_dias REAL NOT NULL,
        cobertura_aviso REAL NOT NULL,
        es_vigente INTEGER NOT NULL DEFAULT 0,
        creado_en TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE dtdcfdab_campana_snapshot (
        id_campana INTEGER NOT NULL,
        id_configuracion INTEGER NOT NULL,
        inicio_carga_artes TEXT, fin_carga_artes TEXT,
        inicio_carga_preproyectos TEXT, fin_carga_preproyectos TEXT,
        inicio_aprobaciones TEXT, fin_aprobaciones TEXT,
        inicio_impresion TEXT, fin_impresion TEXT,
        inicio_precampana TEXT, fin_precampana TEXT,
        inicio_pick_pack TEXT, fin_pick_pack TEXT,
        inicio_entregas TEXT, fin_entregas TEXT,
        porcentaje_alcanzado_entregas REAL,
        ultima_entrega TEXT,
        numero_envios INTEGER,
        envios_con_fecha INTEGER,
        envios_sin_fecha INTEGER,
        envios_sin_registro_entrega INTEGER,
        numero_cajas_pick_pack INTEGER,
        numero_folios INTEGER,
        numero_odps INTEGER,
        numero_actividades INTEGER,
        respuesta_buho_dias REAL,
        respuesta_fda_dias REAL,
        folios_invertidos INTEGER,
        calculado_en TEXT,
        PRIMARY KEY (id_campana, id_configuracion)
    )
    """,
    """
    CREATE TABLE dtdcfdab_job_ejecucion (
        id_job_ejecucion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_campana INTEGER NOT NULL,
        id_lote TEXT,
        id_configuracion INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        iniciado_en TEXT,
        terminado_en TEXT,
        error TEXT
    )
    """,
]


@pytest.fixture
def engine():
    """Engine de SQLite in-memory con las 6 tablas de DTDCFDAB ya creadas.

    Yields:
        Un `Engine` de SQLAlchemy listo para usarse en tests de servicios.
    """
    sqlite_engine = create_engine('sqlite:///:memory:')
    with sqlite_engine.begin() as connection:
        for create_table_statement in ESQUEMA_STATEMENTS:
            connection.execute(text(create_table_statement))
    yield sqlite_engine
    sqlite_engine.dispose()
