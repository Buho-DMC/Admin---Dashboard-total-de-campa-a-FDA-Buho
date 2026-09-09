"""Punto de entrada de la API: crea la app de FastAPI y monta los routers."""

from fastapi import FastAPI

from src import config, logging_utils
from src.routers.campanas import router as campanas_router
from src.routers.configuracion import router as configuracion_router
from src.routers.eventos import router as eventos_router
from src.routers.health import router as health_router
from src.routers.jobs import router as jobs_router
from src.routers.snapshots import router as snapshots_router

app = FastAPI(title='DTDCFDAB API', docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(health_router)
app.include_router(eventos_router)
app.include_router(configuracion_router)
app.include_router(campanas_router)
app.include_router(snapshots_router)
app.include_router(jobs_router)


@app.on_event('startup')
def startup() -> None:
    """Configura logging y valida el entorno antes de aceptar tráfico.

    Returns:
        None.

    Raises:
        RuntimeError: si falta una variable de entorno requerida (ver `config.validate_env`).
    """
    logging_utils.setup_logging()
    config.validate_env()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=config.PORT)
