from datetime import datetime

import httpx
import pytest
from sqlalchemy import text

from src import config
from src.services.campanas import dar_de_alta, get_campana, list_campanas, listar_campanas_fda_retool

PAYLOAD_RETOOL = {
    'ok': True,
    'campanas': [
        {'clave_cliente': 'FDA', 'cliente': 'Farmacias del ahorro', 'campana': 'FDA AGO26-2',
         'id_claw': 229, 'id_nest': 332, 'inicio_campana': '2026-07-24T17:55:49.000Z'},
        {'clave_cliente': 'YZA', 'cliente': 'Farmacias YZA', 'campana': 'YZA JUN26',
         'id_claw': 50, 'id_nest': 51, 'inicio_campana': '2026-06-01T00:00:00.000Z'},
        {'clave_cliente': 'FDA', 'cliente': 'Farmacias del ahorro', 'campana': 'FDA JUN26',
         'id_claw': 199, 'id_nest': 300, 'inicio_campana': '2026-06-10T00:00:00.000Z'},
    ],
}


def _crear_cliente_con_respuesta(responder):
    return httpx.Client(transport=httpx.MockTransport(responder))


def test_listar_campanas_fda_filtra_por_clave_cliente(monkeypatch):
    monkeypatch.setattr(config, 'RETOOL_CAMPANAS_WEBHOOK_URL', 'https://retool.example.com/webhook')

    def responder(request):
        return httpx.Response(200, json=PAYLOAD_RETOOL)

    resultado = listar_campanas_fda_retool(_crear_cliente_con_respuesta(responder))

    assert {campana['id_claw'] for campana in resultado} == {229, 199}


def test_listar_campanas_fda_ordena_mas_reciente_primero(monkeypatch):
    monkeypatch.setattr(config, 'RETOOL_CAMPANAS_WEBHOOK_URL', 'https://retool.example.com/webhook')

    def responder(request):
        return httpx.Response(200, json=PAYLOAD_RETOOL)

    resultado = listar_campanas_fda_retool(_crear_cliente_con_respuesta(responder))

    assert [campana['id_claw'] for campana in resultado] == [229, 199]


def test_listar_campanas_fda_ok_false_lanza_runtimeerror(monkeypatch):
    monkeypatch.setattr(config, 'RETOOL_CAMPANAS_WEBHOOK_URL', 'https://retool.example.com/webhook')

    def responder(request):
        return httpx.Response(200, json={'ok': False})

    with pytest.raises(RuntimeError):
        listar_campanas_fda_retool(_crear_cliente_con_respuesta(responder))


def test_listar_campanas_fda_error_http_lanza_runtimeerror(monkeypatch):
    monkeypatch.setattr(config, 'RETOOL_CAMPANAS_WEBHOOK_URL', 'https://retool.example.com/webhook')

    def responder(request):
        return httpx.Response(503)

    with pytest.raises(RuntimeError):
        listar_campanas_fda_retool(_crear_cliente_con_respuesta(responder))


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
