"""Tests de config.py — accesores sobre st.secrets."""

import config


def test_obtener_url_base_api_lee_de_secrets(monkeypatch):
    monkeypatch.setattr(config.st, 'secrets', {'api_base_url': 'https://ejemplo.test'})
    assert config.obtener_url_base_api() == 'https://ejemplo.test'


def test_obtener_llave_de_api_lee_de_secrets(monkeypatch):
    monkeypatch.setattr(config.st, 'secrets', {'api_key': 'llave-de-prueba'})
    assert config.obtener_llave_de_api() == 'llave-de-prueba'


def test_obtener_contrasena_de_acceso_lee_de_secrets(monkeypatch):
    monkeypatch.setattr(config.st, 'secrets', {'app_password': 'clave-de-prueba'})
    assert config.obtener_contrasena_de_acceso() == 'clave-de-prueba'
