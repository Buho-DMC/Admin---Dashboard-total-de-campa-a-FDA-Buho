from datetime import datetime

import pytest
from sqlalchemy import create_engine, text

from src.services.campanas import (
    dar_de_alta,
    get_campana,
    list_campanas,
    list_eventos_de_campana,
    listar_campanas_fda_retool,
    upsert_evento_de_campana,
)


@pytest.fixture
def retool_engine():
    """Engine de SQLite in-memory con `kam_campanas` sembrada a mano.

    Yields:
        Un `Engine` de SQLAlchemy con 3 filas: dos campañas FDA y una YZA, para
        probar el filtro por `cliente` y el orden por `inicio_campana`.
    """
    sqlite_engine = create_engine('sqlite:///:memory:')
    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                'CREATE TABLE kam_campanas ('
                'id_campana INTEGER PRIMARY KEY, id_claw INTEGER, nombre_claw TEXT, '
                'id_nest INTEGER, nombre_nest TEXT, cliente TEXT, inicio_campana TEXT, '
                'nombre_cliente TEXT'
                ')'
            )
        )
        connection.execute(
            text(
                'INSERT INTO kam_campanas '
                '(id_campana, id_claw, nombre_claw, cliente, inicio_campana, nombre_cliente) VALUES '
                "(1, 229, 'FDA AGO26-2', 'FDA', '2026-07-24T17:55:49', 'Farmacias del ahorro'), "
                "(2, 50, 'YZA JUN26', 'YZA', '2026-06-01T00:00:00', 'Farmacias YZA'), "
                "(3, 199, 'FDA JUN26', 'FDA', '2026-06-10T00:00:00', 'Farmacias del ahorro')"
            )
        )
    yield sqlite_engine
    sqlite_engine.dispose()


def test_listar_campanas_fda_filtra_por_clave_cliente(retool_engine):
    resultado = listar_campanas_fda_retool(retool_engine)

    assert {campana['id_claw'] for campana in resultado} == {229, 199}


def test_listar_campanas_fda_ordena_mas_reciente_primero(retool_engine):
    resultado = listar_campanas_fda_retool(retool_engine)

    assert [campana['id_claw'] for campana in resultado] == [229, 199]


def test_listar_campanas_fda_no_invierte_cliente_y_clave(retool_engine):
    resultado = listar_campanas_fda_retool(retool_engine)

    campana_229 = next(campana for campana in resultado if campana['id_claw'] == 229)
    assert campana_229['cliente'] == 'Farmacias del ahorro'
    assert campana_229['cliente_clave'] == 'FDA'


def _sembrar_catalogo_eventos(engine):
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO dtdcfdab_evento (codigo, nombre, orden) VALUES ('entrega_promociones_ac', 'X', 1)")
        )


def _sembrar_configuracion_vigente(engine):
    with engine.begin() as connection:
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_configuracion '
                '(nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, hueco_entregas_dias, '
                'desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en) '
                "VALUES ('v1', 0.99, 0.01, 0.05, 10, 0.622, 0.95, 1, '2026-01-01')"
            )
        )


def test_dar_de_alta_inserta_campana_eventos_y_job(engine):
    _sembrar_catalogo_eventos(engine)
    _sembrar_configuracion_vigente(engine)

    resultado = dar_de_alta(
        engine,
        id_claw=229,
        cliente='FDA',
        nombre='FDA AGO26-2',
        inicio_campana=datetime(2026, 7, 24),
        milestones=[{'codigo_evento': 'entrega_promociones_ac', 'fecha': datetime(2026, 7, 1)}],
    )

    assert resultado['campana']['id_claw'] == 229
    assert resultado['job']['tipo'] == 'alta'
    assert resultado['job']['estado'] == 'pendiente'

    with engine.connect() as connection:
        numero_de_eventos_capturados = connection.execute(text('SELECT COUNT(*) FROM dtdcfdab_campana_evento')).scalar_one()
    assert numero_de_eventos_capturados == 1


def test_dar_de_alta_id_claw_duplicado_lanza_valueerror(engine):
    _sembrar_catalogo_eventos(engine)
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=229, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 7, 24), milestones=[])

    with pytest.raises(ValueError):
        dar_de_alta(engine, id_claw=229, cliente='FDA', nombre='Y', inicio_campana=datetime(2026, 7, 24), milestones=[])


def test_dar_de_alta_codigo_evento_desconocido_lanza_valueerror(engine):
    _sembrar_configuracion_vigente(engine)

    with pytest.raises(ValueError):
        dar_de_alta(
            engine, id_claw=229, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 7, 24),
            milestones=[{'codigo_evento': 'no_existe', 'fecha': datetime(2026, 7, 1)}],
        )


def test_dar_de_alta_sin_configuracion_vigente_lanza_valueerror(engine):
    _sembrar_catalogo_eventos(engine)

    with pytest.raises(ValueError):
        dar_de_alta(engine, id_claw=229, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 7, 24), milestones=[])


def test_list_campanas_ordenado_por_inicio_desc(engine):
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='vieja', inicio_campana=datetime(2026, 1, 1), milestones=[])
    dar_de_alta(engine, id_claw=2, cliente='FDA', nombre='nueva', inicio_campana=datetime(2026, 6, 1), milestones=[])

    resultado = list_campanas(engine)

    assert [campana['nombre'] for campana in resultado] == ['nueva', 'vieja']


def test_get_campana_no_encontrada_regresa_none(engine):
    assert get_campana(engine, 999) is None


def test_get_campana_encontrada(engine):
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 1, 1), milestones=[])

    campana_de_prueba = list_campanas(engine)[0]

    assert get_campana(engine, campana_de_prueba['id_campana'])['id_claw'] == 1


def test_list_eventos_de_campana_incluye_no_capturados(engine):
    _sembrar_catalogo_eventos(engine)
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 1, 1), milestones=[])

    resultado = list_eventos_de_campana(engine, 1)

    assert len(resultado) == 1
    assert resultado[0]['codigo'] == 'entrega_promociones_ac'
    assert resultado[0]['fecha'] is None


def test_upsert_evento_de_campana_inserta_si_no_existe(engine):
    _sembrar_catalogo_eventos(engine)
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 1, 1), milestones=[])

    resultado = upsert_evento_de_campana(engine, 1, 'entrega_promociones_ac', datetime(2026, 2, 1))

    assert resultado['fecha'] == datetime(2026, 2, 1)
    assert resultado['codigo'] == 'entrega_promociones_ac'
    assert resultado['nombre'] == 'X'  # nombre real del evento sembrado por _sembrar_catalogo_eventos
    assert resultado['actualizado_en'] is not None


def test_upsert_evento_de_campana_actualiza_si_ya_existe(engine):
    _sembrar_catalogo_eventos(engine)
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(
        engine, id_claw=1, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 1, 1),
        milestones=[{'codigo_evento': 'entrega_promociones_ac', 'fecha': datetime(2026, 1, 15)}],
    )

    resultado = upsert_evento_de_campana(engine, 1, 'entrega_promociones_ac', datetime(2026, 2, 1))

    assert resultado['fecha'] == datetime(2026, 2, 1)
    with engine.connect() as connection:
        numero_de_filas = connection.execute(text('SELECT COUNT(*) FROM dtdcfdab_campana_evento')).scalar_one()
    assert numero_de_filas == 1


def test_upsert_evento_de_campana_codigo_desconocido_lanza_valueerror(engine):
    _sembrar_configuracion_vigente(engine)
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='X', inicio_campana=datetime(2026, 1, 1), milestones=[])

    with pytest.raises(ValueError):
        upsert_evento_de_campana(engine, 1, 'no_existe', datetime(2026, 2, 1))
