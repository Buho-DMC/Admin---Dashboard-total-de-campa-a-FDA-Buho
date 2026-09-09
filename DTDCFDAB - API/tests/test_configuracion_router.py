from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}


def test_get_configuracion_vigente_404_si_no_hay(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.configuracion.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.configuracion.configuracion.get_vigente', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/configuracion/vigente', headers=HEADERS)
    assert response.status_code == 404


def test_get_configuracion_historial(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    configuracion_de_ejemplo = {
        'id_configuracion': 1, 'nombre': 'Politica D v1', 'porcentaje_fin': 0.99, 'porcentaje_inicio': 0.01,
        'porcentaje_bloque_minimo': 0.05, 'hueco_entregas_dias': 10, 'desfase_rescate_dias': 0.622,
        'cobertura_aviso': 0.95, 'es_vigente': True, 'creado_en': '2026-01-01T00:00:00',
    }
    with patch('src.routers.configuracion.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.configuracion.configuracion.list_configuraciones', return_value=[configuracion_de_ejemplo]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/configuracion', headers=HEADERS)
    assert response.status_code == 200
    assert response.json()[0]['nombre'] == 'Politica D v1'


def test_post_configuracion_crea_y_encola(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    configuracion_de_ejemplo = {
        'id_configuracion': 2, 'nombre': 'nueva', 'porcentaje_fin': 0.99, 'porcentaje_inicio': 0.01,
        'porcentaje_bloque_minimo': 0.05, 'hueco_entregas_dias': 10, 'desfase_rescate_dias': 0.622,
        'cobertura_aviso': 0.95, 'es_vigente': True, 'creado_en': '2026-02-01T00:00:00',
    }
    resultado_creacion = {
        'configuracion': configuracion_de_ejemplo, 'id_lote': 'lote-1',
        'jobs': [{'id_job_ejecucion': 1, 'id_campana': 1, 'id_lote': 'lote-1', 'id_configuracion': 2,
                   'tipo': 'recalculo', 'estado': 'pendiente', 'iniciado_en': None, 'terminado_en': None, 'error': None}],
    }
    with patch('src.routers.configuracion.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.configuracion.clients.get_tasks_client') as mock_get_tasks_client, \
         patch('src.routers.configuracion.configuracion.crear_y_marcar_vigente', return_value=resultado_creacion), \
         patch('src.routers.configuracion.jobs.encolar_job') as mock_encolar_job:
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.post(
            '/configuracion', headers=HEADERS,
            json={'nombre': 'nueva', 'porcentaje_fin': 0.99, 'porcentaje_inicio': 0.01, 'porcentaje_bloque_minimo': 0.05,
                  'hueco_entregas_dias': 10, 'desfase_rescate_dias': 0.622, 'cobertura_aviso': 0.95},
        )
    assert response.status_code == 200
    assert response.json()['id_lote'] == 'lote-1'
    assert response.json()['total_campanas'] == 1
    mock_encolar_job.assert_called_once_with(mock_get_tasks_client.return_value, 1)
