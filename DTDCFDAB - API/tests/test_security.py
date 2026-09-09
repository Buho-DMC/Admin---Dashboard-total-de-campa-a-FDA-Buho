import pytest
from fastapi import HTTPException

from src import config
from src.security import require_api_key


def test_require_api_key_pasa_con_key_correcto(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto-valido')
    require_api_key(x_api_key='secreto-valido')


def test_require_api_key_rechaza_key_incorrecto(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', 'secreto-valido')
    with pytest.raises(HTTPException) as excepcion_capturada:
        require_api_key(x_api_key='otro-valor')
    assert excepcion_capturada.value.status_code == 401


def test_require_api_key_rechaza_si_no_hay_secreto_configurado(monkeypatch):
    monkeypatch.setattr(config, 'API_KEY_DTDC_FDA_BUHO', '')
    with pytest.raises(HTTPException) as excepcion_capturada:
        require_api_key(x_api_key='cualquier-cosa')
    assert excepcion_capturada.value.status_code == 401
