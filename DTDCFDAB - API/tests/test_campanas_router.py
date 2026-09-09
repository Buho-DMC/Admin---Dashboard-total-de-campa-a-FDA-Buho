from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}


def test_get_campanas_retool(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
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
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_retool_client') as mock_get_retool_client, \
         patch('src.routers.campanas.campanas.listar_campanas_fda_retool', side_effect=RuntimeError('boom')):
        mock_get_retool_client.return_value.close = lambda: None
        response = client.get('/campanas/retool', headers=HEADERS)
    assert response.status_code == 502


def test_post_campanas_alta_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    resultado_alta = {
        'campana': {'id_campana': 1, 'id_claw': 229, 'cliente': 'FDA', 'nombre': 'X',
                     'inicio_campana': '2026-07-24T00:00:00', 'fecha_alta': '2026-08-01T00:00:00'},
        'job': {'id_job_ejecucion': 1, 'id_campana': 1, 'id_lote': None, 'id_configuracion': 1, 'tipo': 'alta',
                 'estado': 'pendiente', 'iniciado_en': None, 'terminado_en': None, 'error': None},
    }
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.clients.get_tasks_client') as mock_get_tasks_client, \
         patch('src.routers.campanas.campanas.dar_de_alta', return_value=resultado_alta), \
         patch('src.routers.campanas.jobs.encolar_job') as mock_encolar_job:
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post(
            '/campanas', headers=HEADERS,
            json={'id_claw': 229, 'cliente': 'FDA', 'nombre': 'X', 'inicio_campana': '2026-07-24T00:00:00', 'milestones': []},
        )
    assert response.status_code == 200
    assert response.json()['campana']['id_claw'] == 229
    mock_encolar_job.assert_called_once()


def test_post_campanas_alta_duplicada_409(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.campanas.dar_de_alta', side_effect=ValueError('ya existe')):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post(
            '/campanas', headers=HEADERS,
            json={'id_claw': 229, 'cliente': 'FDA', 'nombre': 'X', 'inicio_campana': '2026-07-24T00:00:00', 'milestones': []},
        )
    assert response.status_code == 409


def test_get_campanas_lista(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.campanas.list_campanas', return_value=[]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas', headers=HEADERS)
    assert response.status_code == 200


def test_get_campana_detalle_404(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.campanas.get_campana', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/999', headers=HEADERS)
    assert response.status_code == 404


def test_get_campanas_eventos(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.campanas.list_eventos_de_campana', return_value=[]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/1/eventos', headers=HEADERS)
    assert response.status_code == 200


def test_put_campanas_evento_desconocido_400(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.campanas.upsert_evento_de_campana', side_effect=ValueError('no existe')):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.put(
            '/campanas/1/eventos/no_existe', headers=HEADERS, json={'fecha': '2026-02-01T00:00:00'}
        )
    assert response.status_code == 400


def test_get_campana_job_404(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.jobs.get_ultimo_job_de_campana', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/1/job', headers=HEADERS)
    assert response.status_code == 404


def test_get_campana_job_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    job_de_ejemplo = {
        'id_job_ejecucion': 1, 'id_campana': 1, 'id_lote': None, 'id_configuracion': 1, 'tipo': 'alta',
        'estado': 'corriendo', 'iniciado_en': '2026-08-01T00:00:00', 'terminado_en': None, 'error': None,
    }
    with patch('src.routers.campanas.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.campanas.jobs.get_ultimo_job_de_campana', return_value=job_de_ejemplo):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/1/job', headers=HEADERS)
    assert response.status_code == 200
    assert response.json()['estado'] == 'corriendo'
