from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src import config

client = TestClient(app)
HEADERS = {'X-API-Key': 'secreto'}

CAMPOS_OPCIONALES_SNAPSHOT = [
    'inicio_carga_artes', 'fin_carga_artes', 'inicio_carga_preproyectos', 'fin_carga_preproyectos',
    'inicio_aprobaciones', 'fin_aprobaciones', 'inicio_impresion', 'fin_impresion',
    'inicio_precampana', 'fin_precampana', 'inicio_pick_pack', 'fin_pick_pack',
    'inicio_entregas', 'fin_entregas', 'porcentaje_alcanzado_entregas', 'ultima_entrega',
    'numero_envios', 'envios_con_fecha', 'envios_sin_fecha', 'envios_sin_registro_entrega',
    'numero_cajas_pick_pack', 'numero_folios', 'numero_odps', 'numero_actividades',
    'respuesta_buho_dias', 'respuesta_fda_dias', 'folios_invertidos', 'calculado_en',
]


def _construir_snapshot_de_prueba(**overrides):
    snapshot_base = {campo: None for campo in CAMPOS_OPCIONALES_SNAPSHOT}
    snapshot_base.update(id_campana=1, id_configuracion=1)
    snapshot_base.update(overrides)
    return snapshot_base


def test_get_campana_snapshot_404_si_no_existe(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.snapshots.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.snapshots.configuracion.get_vigente', return_value={'id_configuracion': 1}), \
         patch('src.routers.snapshots.snapshots.get_snapshot', return_value=None):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/1/snapshot', headers=HEADERS)
    assert response.status_code == 404


def test_get_campana_snapshot_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.snapshots.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.snapshots.configuracion.get_vigente', return_value={'id_configuracion': 1}), \
         patch('src.routers.snapshots.snapshots.get_snapshot', return_value=_construir_snapshot_de_prueba()):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/campanas/1/snapshot', headers=HEADERS)
    assert response.status_code == 200


def test_get_snapshots_vigentes_requiere_query_param(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    response = client.get('/snapshots', headers=HEADERS)
    assert response.status_code == 400


def test_get_snapshots_vigentes_ok(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto')
    with patch('src.routers.snapshots.clients.get_db_engine') as mock_get_db_engine, \
         patch('src.routers.snapshots.snapshots.list_snapshots_vigentes', return_value=[_construir_snapshot_de_prueba()]):
        mock_get_db_engine.return_value.dispose = lambda: None
        response = client.get('/snapshots?vigente=true', headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1
