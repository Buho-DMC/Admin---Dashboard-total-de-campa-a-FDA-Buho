from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_no_requiere_api_key():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_health_deep_requiere_api_key():
    response = client.get('/health/deep')
    assert response.status_code == 422  # falta el header requerido


def test_health_deep_con_api_key_valido(monkeypatch):
    from src import config

    monkeypatch.setattr(config, 'API_KEY_DTDCFDAB', 'secreto')

    with patch('src.routers.health.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.health.clients.get_claw_picks_client') as mock_get_claw_picks_client:
        mock_get_db_engine.return_value = MagicMock()
        mock_get_claw_picks_client.return_value = MagicMock()
        with patch('src.routers.health.health.check_database', return_value='ok'), \
             patch('src.routers.health.health.check_claw', return_value='reachable'):
            response = client.get('/health/deep', headers={'X-API-Key': 'secreto'})

    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'database': 'ok', 'claw': 'reachable'}
