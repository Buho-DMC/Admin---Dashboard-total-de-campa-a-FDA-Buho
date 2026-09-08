from sqlalchemy import text

from src.services.configuracion import get_vigente, list_configuraciones

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
