"""Configuración de logging: Cloud Logging en producción, consola en local."""

import logging

import google.cloud.logging


def setup_logging() -> None:
    """Activa Cloud Logging si hay credenciales de GCP disponibles.

    Returns:
        None.

    Note:
        Si `google.cloud.logging.Client()` falla (sin ADC, ej. en desarrollo local),
        cae a `logging.basicConfig` en vez de tumbar el arranque de la app.
    """
    try:
        cloud_logging_client = google.cloud.logging.Client()
        cloud_logging_client.setup_logging()
    except Exception:
        logging.basicConfig(level=logging.INFO)
