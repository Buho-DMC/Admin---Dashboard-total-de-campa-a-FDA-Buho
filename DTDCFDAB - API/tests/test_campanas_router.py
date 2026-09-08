from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}


def test_get_campanas_retool(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDCFDAB', 'secreto')
    campana_de_ejemplo = {
        'id_claw': 229, 'campana': 'FDA AGO26-2', 'cliente': 'FDA', 'cliente_clave': 'FDA', 'inicio_campana': None,
    }
    with patch('src.routers.campanas.clients.get_retool_client') as mock_get_retool_client, \
         patch('src.routers.campanas.campanas.listar_campanas_fda_retool', return_value=[campana_de_ejemplo]):
        mock_get_retool_client.return_value.close = lambda: None
        response = client.get('/campanas/retool', headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == [campana_de_ejemplo]


def test_get_campanas_retool_error_regresa_502(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDCFDAB', 'secreto')
    with patch('src.routers.campanas.clients.get_retool_client') as mock_get_retool_client, \
         patch('src.routers.campanas.campanas.listar_campanas_fda_retool', side_effect=RuntimeError('boom')):
        mock_get_retool_client.return_value.close = lambda: None
        response = client.get('/campanas/retool', headers=HEADERS)
    assert response.status_code == 502
