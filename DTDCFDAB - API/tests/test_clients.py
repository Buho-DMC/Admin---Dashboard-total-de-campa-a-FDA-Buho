from unittest.mock import MagicMock, patch

from src import clients, config


def test_get_db_engine_arma_url_con_los_datos_de_config(monkeypatch):
    monkeypatch.setattr(config, 'MYSQL_USER', 'user1')
    monkeypatch.setattr(config, 'MYSQL_PASSWORD', 'pass1')
    monkeypatch.setattr(config, 'MYSQL_HOST', 'host1')
    monkeypatch.setattr(config, 'MYSQL_PORT', 25060)
    monkeypatch.setattr(config, 'MYSQL_DB', 'db1')

    engine = clients.get_db_engine()

    assert engine.url.username == 'user1'
    assert engine.url.host == 'host1'
    assert engine.url.port == 25060
    assert engine.url.database == 'db1'


def test_get_claw_client_manda_header_api_key(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_CLAW', 'claw-key')
    monkeypatch.setattr(config, 'API_BASE_URL_CLAW', 'https://claw.example.com')

    client = clients.get_claw_client()

    assert client.headers['api-key'] == 'claw-key'
    assert str(client.base_url) == 'https://claw.example.com'
    client.close()


def test_get_retool_client_manda_header_workflow_api_key(monkeypatch):
    monkeypatch.setattr(config, 'RETOOL_CAMPANAS_API_KEY', 'retool-key')

    client = clients.get_retool_client()

    assert client.headers['x-workflow-api-key'] == 'retool-key'
    client.close()


def test_get_tasks_client_regresa_cliente_de_cloud_tasks():
    with patch('src.clients.tasks_v2.CloudTasksClient') as mock_cloud_tasks_client_class:
        mock_cloud_tasks_client_class.return_value = MagicMock()
        resultado = clients.get_tasks_client()
        mock_cloud_tasks_client_class.assert_called_once()
        assert resultado is mock_cloud_tasks_client_class.return_value
