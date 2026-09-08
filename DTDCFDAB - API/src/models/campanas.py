"""Modelos Pydantic de campañas (proxy Retool en la Tarea 7, alta/listado en la 8, hitos en la 9)."""

from datetime import datetime

from pydantic import BaseModel


class CampanaRetoolOut(BaseModel):
    """Una campaña FDA tal como la reporta el workflow de Retool (sin dar de alta todavía)."""

    id_claw: int
    campana: str
    cliente: str
    cliente_clave: str | None
    inicio_campana: datetime | None
