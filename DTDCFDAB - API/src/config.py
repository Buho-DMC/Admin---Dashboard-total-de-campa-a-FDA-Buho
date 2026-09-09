"""Configuración central de la API: variables de entorno y validación de arranque."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# --- MySQL (dmc-general, compartida con otros proyectos chicos) ---
MYSQL_HOST = os.getenv('MYSQL_HOST_DMC_GENERAL', '')
MYSQL_PORT = int(os.getenv('MYSQL_PORT_DMC_GENERAL', '25060'))
MYSQL_USER = os.getenv('MYSQL_USER_DMC_GENERAL', '')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD_DMC_GENERAL', '')
MYSQL_DB = os.getenv('MYSQL_DB_DMC_GENERAL', '')

# --- Autenticación interna (Dashboard y Cloud Tasks -> esta API) ---
API_KEY_DTDC_FDA_BUHO = os.getenv('API_KEY_DTDC_FDA_BUHO', '')
API_BASE_URL_DTDC_FDA_BUHO = os.getenv('API_BASE_URL_DTDC_FDA_BUHO', '')

# --- Retool (selector de campañas FDA) ---
RETOOL_CAMPANAS_API_KEY = os.getenv('RETOOL_CAMPANAS_API_KEY', '')
RETOOL_CAMPANAS_WEBHOOK_URL = os.getenv('RETOOL_CAMPANAS_WEBHOOK_URL', '')

# --- Retool DB (fuente del ETL: artes, preproyectos, aprobaciones, precampana) ---
RETOOL_DB_HOST = os.getenv('RETOOL_DB_HOST', '')
RETOOL_DB_PORT = int(os.getenv('RETOOL_DB_PORT', '5432'))
RETOOL_DB_USER = os.getenv('RETOOL_DB_USER', '')
RETOOL_DB_PASSWORD = os.getenv('RETOOL_DB_PASSWORD', '')
RETOOL_DB_NAME = os.getenv('RETOOL_DB_NAME', '')

# --- Claw (fuentes del ETL, secrets compartidos con otros proyectos del equipo) ---
API_KEY_CLAW = os.getenv('API_KEY_CLAW', '')
API_BASE_URL_CLAW = os.getenv('API_BASE_URL_CLAW', '')

# --- Cloud Tasks / GCP ---
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')
TASKS_QUEUE = os.getenv('TASKS_QUEUE', 'dtdc-fda-buho-jobs')

# --- Servidor ---
PORT = int(os.getenv('PORT', '8080'))

REQUIRED_VARS = [
    'MYSQL_HOST_DMC_GENERAL',
    'MYSQL_USER_DMC_GENERAL',
    'MYSQL_PASSWORD_DMC_GENERAL',
    'MYSQL_DB_DMC_GENERAL',
    'API_KEY_DTDC_FDA_BUHO',
    'RETOOL_CAMPANAS_API_KEY',
    'RETOOL_CAMPANAS_WEBHOOK_URL',
    'RETOOL_DB_HOST',
    'RETOOL_DB_USER',
    'RETOOL_DB_PASSWORD',
    'RETOOL_DB_NAME',
    'GCP_PROJECT_ID',
]


def validate_env() -> None:
    """Verifica que todas las variables de entorno requeridas estén presentes.

    Returns:
        None. No retorna nada si la validación pasa.

    Raises:
        RuntimeError: si falta una o más variables de `REQUIRED_VARS`, con la lista
            completa de nombres faltantes en el mensaje.
    """
    missing_variables = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing_variables:
        raise RuntimeError(f'Missing required environment variables: {", ".join(missing_variables)}')
