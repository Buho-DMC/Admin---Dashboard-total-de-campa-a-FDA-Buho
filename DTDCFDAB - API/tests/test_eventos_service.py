from sqlalchemy import text

from src.services.eventos import create_evento, list_eventos


def test_list_eventos_vacio(engine):
    assert list_eventos(engine) == []


def test_list_eventos_ordenado_por_orden(engine):
    with engine.begin() as connection:
        connection.execute(
            text('INSERT INTO dtdcfdab_evento (codigo, nombre, orden) VALUES (:codigo, :nombre, :orden)'),
            [
                {'codigo': 'cierre_comercializacion', 'nombre': 'Cierre Comercializacion Espacios', 'orden': 2},
                {'codigo': 'entrega_promociones_ac', 'nombre': 'Entrega Promociones Area Comercial', 'orden': 1},
            ],
        )

    resultado = list_eventos(engine)

    assert [evento['codigo'] for evento in resultado] == ['entrega_promociones_ac', 'cierre_comercializacion']


def test_create_evento_inserta_y_regresa_la_fila(engine):
    evento_creado = create_evento(engine, codigo='liberacion_pop', nombre='Liberacion POP', orden=7)

    assert evento_creado['codigo'] == 'liberacion_pop'
    assert evento_creado['origen'] == 'manual'
    assert evento_creado['rol'] == 'hito'
    assert evento_creado['id_evento'] > 0
