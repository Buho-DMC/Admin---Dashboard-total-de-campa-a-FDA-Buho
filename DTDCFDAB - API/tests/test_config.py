import importlib

import pytest

import src.config as config


def test_puerto_default_es_8080(monkeypatch):
    monkeypatch.delenv('PORT', raising=False)
    importlib.reload(config)
    assert config.PORT == 8080


def test_puerto_toma_env_var(monkeypatch):
    monkeypatch.setenv('PORT', '9090')
    importlib.reload(config)
    assert config.PORT == 9090
    monkeypatch.delenv('PORT', raising=False)
    importlib.reload(config)


def test_validate_env_lanza_si_falta_una_var(monkeypatch):
    monkeypatch.delenv('API_KEY_DTDCFDAB', raising=False)
    importlib.reload(config)
    with pytest.raises(RuntimeError):
        config.validate_env()


def test_validate_env_pasa_si_estan_todas(monkeypatch):
    for variable_requerida in config.REQUIRED_VARS:
        monkeypatch.setenv(variable_requerida, 'x')
    importlib.reload(config)
    config.validate_env()
