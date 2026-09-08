"""Modelos Pydantic del catálogo de eventos."""

from pydantic import BaseModel


class EventoOut(BaseModel):
    """Un hito del catálogo de eventos FDA."""

    id_evento: int
    codigo: str
    nombre: str
    origen: str
    rol: str
    orden: int


class EventoCreateIn(BaseModel):
    """Body para agregar un milestone nuevo al catálogo."""

    codigo: str
    nombre: str
    orden: int
