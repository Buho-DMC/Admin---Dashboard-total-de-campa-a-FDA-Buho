"""Autenticación de la API interna: un solo API key estático por header."""

import secrets

from fastapi import Header, HTTPException, status

from src import config


def require_api_key(x_api_key: str = Header(...)) -> None:
    """Dependency de FastAPI que exige el header `X-API-Key` correcto.

    Args:
        x_api_key: valor del header `X-API-Key`, inyectado por FastAPI.

    Returns:
        None. No retorna nada cuando la autenticación es válida.

    Raises:
        HTTPException: 401 si no hay secreto configurado en `config.API_KEY_DTDC_FDA_BUHO`,
            o si `x_api_key` no coincide (comparación en tiempo constante).
    """
    if not config.API_KEY_DTDC_FDA_BUHO:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')
    if not secrets.compare_digest(x_api_key.encode('utf-8'), config.API_KEY_DTDC_FDA_BUHO.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')
