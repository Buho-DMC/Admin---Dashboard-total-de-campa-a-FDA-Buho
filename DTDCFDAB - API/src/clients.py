"""Fábricas de clientes externos: MySQL, Claw, Retool y Cloud Tasks."""

import ssl

import httpx
from google.cloud import tasks_v2
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src import config


def _build_mysql_ssl_context() -> ssl.SSLContext:
    """Construye el contexto SSL para la conexión a MySQL en Digital Ocean.

    Returns:
        Un `ssl.SSLContext` con verificación de certificado deshabilitada (el
        servidor gestionado de Digital Ocean no expone un CA público verificable
        desde este cliente).
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


def get_db_engine() -> Engine:
    """Crea un engine de SQLAlchemy hacia la base `dmc-general`.

    Returns:
        Un `Engine` de SQLAlchemy con `pool_pre_ping` activo y un timeout de
        conexión de 60s (necesario en Cloud Run: la primera conexión tras un
        cold start puede tardar).
    """
    connection_url = (
        f'mysql+pymysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}'
        f'@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DB}'
    )
    return create_engine(
        connection_url,
        pool_pre_ping=True,
        connect_args={'ssl': _build_mysql_ssl_context(), 'connect_timeout': 60},
    )


def get_claw_picks_client() -> httpx.Client:
    """Crea un cliente HTTP para el endpoint de Pick & Pack de Claw.

    Returns:
        Un `httpx.Client` con el header `api-key` ya configurado y un timeout
        de 300s (el volumen de filas por campaña es grande, ver spec).
    """
    return httpx.Client(
        base_url=config.CLAW_BASE_URL_PICKS,
        headers={'api-key': config.CLAW_API_KEY, 'Content-Type': 'application/json'},
        timeout=300.0,
    )


def get_claw_tracking_client() -> httpx.Client:
    """Crea un cliente HTTP para el endpoint de Entregas de Claw.

    Returns:
        Un `httpx.Client` con el header `api-key` ya configurado y un timeout
        de 300s.
    """
    return httpx.Client(
        base_url=config.CLAW_BASE_URL_TRACKING,
        headers={'api-key': config.CLAW_API_KEY, 'Content-Type': 'application/json'},
        timeout=300.0,
    )


def get_retool_client() -> httpx.Client:
    """Crea un cliente HTTP para el workflow de Retool que lista campañas.

    Returns:
        Un `httpx.Client` con el header `X-Workflow-Api-Key` ya configurado.
    """
    return httpx.Client(
        headers={'X-Workflow-Api-Key': config.RETOOL_CAMPANAS_API_KEY, 'Content-Type': 'application/json'},
        timeout=15.0,
    )


def get_tasks_client() -> tasks_v2.CloudTasksClient:
    """Crea el cliente de Cloud Tasks usado para encolar jobs.

    Returns:
        Un `tasks_v2.CloudTasksClient` autenticado vía Application Default
        Credentials (el service account de Cloud Run).
    """
    return tasks_v2.CloudTasksClient()
