from datetime import datetime

from sqlalchemy import text

from src.services.campanas import dar_de_alta
from src.services.configuracion import crear_y_marcar_vigente, get_vigente, list_configuraciones

COLUMNAS_CONFIGURACION = (
    'nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, '
    'hueco_entregas_dias, desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en'
)


def _insertar_configuracion(engine, nombre, es_vigente, creado_en):
    with engine.begin() as connection:
        connection.execute(
            text(
                f'INSERT INTO dtdcfdab_configuracion ({COLUMNAS_CONFIGURACION}) VALUES '
                '(:nombre, 0.99, 0.01, 0.05, 10, 0.622, 0.95, :es_vigente, :creado_en)'
            ),
            {'nombre': nombre, 'es_vigente': 1 if es_vigente else 0, 'creado_en': creado_en},
        )


def test_get_vigente_ninguna_regresa_none(engine):
    assert get_vigente(engine) is None


def test_get_vigente_regresa_la_marcada(engine):
    _insertar_configuracion(engine, 'vieja', False, '2026-01-01')
    _insertar_configuracion(engine, 'Politica D v1', True, '2026-02-01')

    resultado = get_vigente(engine)

    assert resultado['nombre'] == 'Politica D v1'
    assert resultado['es_vigente'] is True


def test_list_configuraciones_ordenado_mas_reciente_primero(engine):
    _insertar_configuracion(engine, 'vieja', False, '2026-01-01')
    _insertar_configuracion(engine, 'nueva', True, '2026-02-01')

    resultado = list_configuraciones(engine)

    assert [configuracion['nombre'] for configuracion in resultado] == ['nueva', 'vieja']


def test_crear_y_marcar_vigente_desmarca_la_anterior(engine):
    _insertar_configuracion(engine, 'vieja', True, '2026-01-01')

    resultado = crear_y_marcar_vigente(
        engine, nombre='nueva', porcentaje_fin=0.99, porcentaje_inicio=0.01, porcentaje_bloque_minimo=0.05,
        hueco_entregas_dias=10, desfase_rescate_dias=0.622, cobertura_aviso=0.95,
    )

    assert resultado['configuracion']['es_vigente'] is True
    with engine.connect() as connection:
        numero_de_configuraciones_vigentes = connection.execute(
            text('SELECT COUNT(*) FROM dtdcfdab_configuracion WHERE es_vigente = 1')
        ).scalar_one()
    assert numero_de_configuraciones_vigentes == 1


def test_crear_y_marcar_vigente_encola_un_job_por_campana(engine):
    _insertar_configuracion(engine, 'vieja', True, '2026-01-01')
    dar_de_alta(engine, id_claw=1, cliente='FDA', nombre='A', inicio_campana=datetime(2026, 1, 1), milestones=[])
    dar_de_alta(engine, id_claw=2, cliente='FDA', nombre='B', inicio_campana=datetime(2026, 1, 2), milestones=[])

    resultado = crear_y_marcar_vigente(
        engine, nombre='nueva', porcentaje_fin=0.99, porcentaje_inicio=0.01, porcentaje_bloque_minimo=0.05,
        hueco_entregas_dias=10, desfase_rescate_dias=0.622, cobertura_aviso=0.95,
    )

    assert len(resultado['jobs']) == 2
    assert all(job['tipo'] == 'recalculo' for job in resultado['jobs'])
    assert len({job['id_lote'] for job in resultado['jobs']}) == 1


def test_crear_y_marcar_vigente_sin_campanas_no_crea_jobs(engine):
    resultado = crear_y_marcar_vigente(
        engine, nombre='nueva', porcentaje_fin=0.99, porcentaje_inicio=0.01, porcentaje_bloque_minimo=0.05,
        hueco_entregas_dias=10, desfase_rescate_dias=0.622, cobertura_aviso=0.95,
    )

    assert resultado['jobs'] == []
