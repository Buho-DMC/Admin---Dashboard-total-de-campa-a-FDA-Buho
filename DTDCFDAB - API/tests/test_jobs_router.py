from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}

JOB_DE_EJEMPLO = {
    'id_job_ejecucion': 1, 'id_campana': 1, 'id_lote': None, 'id_configuracion': 1, 'tipo': 'alta',
    'estado': 'pendiente', 'iniciado_en': None, 'terminado_en': None, 'error': None,
}


def test_get_job_404(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.jobs.get_job', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/jobs/999', headers=HEADERS)
    assert response.status_code == 404


def test_get_job_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.jobs.get_job', return_value=JOB_DE_EJEMPLO):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/jobs/1', headers=HEADERS)
    assert response.status_code == 200


def test_get_jobs_por_lote_requiere_query_param(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    response = client.get('/jobs', headers=HEADERS)
    assert response.status_code == 400


def test_get_jobs_por_lote_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.jobs.list_jobs_por_lote', return_value=[JOB_DE_EJEMPLO]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/jobs?id_lote=lote-1', headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_post_job_reintentar_404(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.clients.get_tasks_client'), \
         patch('src.routers.jobs.jobs.reintentar', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post('/jobs/999/reintentar', headers=HEADERS)
    assert response.status_code == 404


def test_post_job_reintentar_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    job_reintentado = {**JOB_DE_EJEMPLO, 'id_job_ejecucion': 2}
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.clients.get_tasks_client'), \
         patch('src.routers.jobs.jobs.reintentar', return_value=job_reintentado):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post('/jobs/1/reintentar', headers=HEADERS)
    assert response.status_code == 200
    assert response.json()['id_job_ejecucion'] == 2


def test_post_job_ejecutar(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    job_final = {**JOB_DE_EJEMPLO, 'estado': 'fallido', 'error': 'Politica D pendiente'}
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.clients.get_claw_client'), \
         patch('src.routers.jobs.clients.get_retool_engine') as mock_get_retool_engine, \
         patch('src.routers.jobs.jobs.ejecutar_job', return_value=job_final):
        mock_get_db_engine.return_value.dispose = lambda: None
        mock_get_retool_engine.return_value.dispose = lambda: None
        response = client.post('/jobs/1/ejecutar', headers=HEADERS)
    assert response.status_code == 200
    assert response.json()['estado'] == 'fallido'


def test_post_job_ejecutar_job_inexistente_404(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.jobs.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.jobs.clients.get_claw_client'), \
         patch('src.routers.jobs.clients.get_retool_engine') as mock_get_retool_engine, \
         patch('src.routers.jobs.jobs.ejecutar_job', side_effect=ValueError('no existe')):
        mock_get_db_engine.return_value.dispose = lambda: None
        mock_get_retool_engine.return_value.dispose = lambda: None
        response = client.post('/jobs/999/ejecutar', headers=HEADERS)
    assert response.status_code == 404
