"""Modelos Pydantic compartidos entre routers."""

from pydantic import BaseModel


class HealthOut(BaseModel):
    """Respuesta del liveness check simple."""

    status: str


class HealthDeepOut(BaseModel):
    """Respuesta del chequeo profundo: DB y Claw."""

    status: str
    database: str
    claw: str
