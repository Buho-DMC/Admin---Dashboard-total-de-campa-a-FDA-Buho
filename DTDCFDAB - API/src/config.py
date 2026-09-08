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
API_KEY_DTDCFDAB = os.getenv('API_KEY_DTDCFDAB', '')
API_BASE_URL_DTDCFDAB = os.getenv('API_BASE_URL_DTDCFDAB', '')

# --- Retool (selector de campañas FDA) ---
RETOOL_CAMPANAS_API_KEY = os.getenv('RETOOL_CAMPANAS_API_KEY', '')
RETOOL_CAMPANAS_WEBHOOK_URL = os.getenv('RETOOL_CAMPANAS_WEBHOOK_URL', '')

# --- Claw (fuentes del ETL, pendiente de confirmar credenciales) ---
CLAW_API_KEY = os.getenv('CLAW_API_KEY', '')
CLAW_BASE_URL_PICKS = os.getenv('CLAW_BASE_URL_PICKS', '')
CLAW_BASE_URL_TRACKING = os.getenv('CLAW_BASE_URL_TRACKING', '')

# --- Cloud Tasks / GCP ---
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')
TASKS_QUEUE = os.getenv('TASKS_QUEUE', 'dtdcfdab-jobs')

# --- Servidor ---
PORT = int(os.getenv('PORT', '8080'))

REQUIRED_VARS = [
    'MYSQL_HOST_DMC_GENERAL',
    'MYSQL_USER_DMC_GENERAL',
    'MYSQL_PASSWORD_DMC_GENERAL',
    'MYSQL_DB_DMC_GENERAL',
    'API_KEY_DTDCFDAB',
    'RETOOL_CAMPANAS_API_KEY',
    'RETOOL_CAMPANAS_WEBHOOK_URL',
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
