import httpx
from sqlalchemy import create_engine

from src.services.health import check_claw, check_database


def test_check_database_ok_con_engine_valido():
    engine = create_engine('sqlite:///:memory:')
    assert check_database(engine) == 'ok'


def test_check_claw_sin_configurar_regresa_no_configurado():
    client = httpx.Client(base_url='')
    assert check_claw(client) == 'no configurado'
    client.close()


def test_check_claw_alcanzable():
    def responder(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    client = httpx.Client(base_url='https://claw.example.com', transport=httpx.MockTransport(responder))
    assert check_claw(client) == 'reachable'
    client.close()


def test_check_claw_no_disponible():
    def responder(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError('no disponible', request=request)

    client = httpx.Client(base_url='https://claw.example.com', transport=httpx.MockTransport(responder))
    assert check_claw(client) == 'no disponible'
    client.close()
