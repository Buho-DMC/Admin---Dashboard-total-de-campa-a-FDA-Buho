from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}


def _configurar_api_key(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')


def test_get_eventos_sin_api_key_rechaza():
    response = client.get('/eventos')
    assert response.status_code == 422


def test_get_eventos_con_api_key(monkeypatch):
    _configurar_api_key(monkeypatch)
    with patch('src.routers.eventos.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.eventos.eventos.list_eventos', return_value=[]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/eventos', headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_post_eventos_crea(monkeypatch):
    _configurar_api_key(monkeypatch)
    evento_creado = {
        'id_evento': 8, 'codigo': 'nuevo_hito', 'nombre': 'Nuevo Hito',
        'origen': 'manual', 'rol': 'hito', 'orden': 8,
    }
    with patch('src.routers.eventos.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.eventos.eventos.create_evento', return_value=evento_creado):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post(
            '/eventos', headers=HEADERS, json={'codigo': 'nuevo_hito', 'nombre': 'Nuevo Hito', 'orden': 8}
        )
    assert response.status_code == 200
    assert response.json() == evento_creado
