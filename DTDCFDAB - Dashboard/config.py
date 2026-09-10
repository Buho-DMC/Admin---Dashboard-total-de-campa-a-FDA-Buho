"""Accesores de configuración del Dashboard sobre st.secrets."""

import streamlit as st


def obtener_url_base_api() -> str:
    """URL base de DTDCFDAB - API, sin slash final.

    Returns:
        El valor de `api_base_url` en `st.secrets`.
    """
    return st.secrets['api_base_url']


def obtener_llave_de_api() -> str:
    """Llave de autenticación interna (`X-API-Key`) hacia DTDCFDAB - API.

    Returns:
        El valor de `api_key` en `st.secrets`.
    """
    return st.secrets['api_key']


def obtener_contrasena_de_acceso() -> str:
    """Contraseña del gate de acceso a la UI del Dashboard.

    Returns:
        El valor de `app_password` en `st.secrets`.
    """
    return st.secrets['app_password']
