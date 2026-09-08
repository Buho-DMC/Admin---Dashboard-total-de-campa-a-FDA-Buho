import httpx
import pytest

from src import config
from src.services.campanas import listar_campanas_fda_retool

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
