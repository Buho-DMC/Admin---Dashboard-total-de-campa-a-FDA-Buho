"""Modelos Pydantic de campañas (proxy Retool en la Tarea 7, alta/listado en la 8, hitos en la 9)."""

from datetime import datetime

from pydantic import BaseModel

from src.models.jobs import JobOut


class CampanaRetoolOut(BaseModel):
    """Una campaña FDA tal como la reporta el workflow de Retool (sin dar de alta todavía)."""

    id_claw: int
    campana: str
    cliente: str
    cliente_clave: str | None
    inicio_campana: datetime | None


class MilestoneIn(BaseModel):
    """Un hito FDA capturado a mano en el formulario de alta."""

    codigo_evento: str
    fecha: datetime


class CampanaOut(BaseModel):
    """Una campaña ya dada de alta."""

    id_campana: int
    id_claw: int
    cliente: str
    nombre: str
    inicio_campana: datetime
    fecha_alta: datetime


class CampanaAltaIn(BaseModel):
    """Body para dar de alta una campaña nueva."""

    id_claw: int
    cliente: str
    nombre: str
    inicio_campana: datetime
    milestones: list[MilestoneIn] = []


class CampanaAltaOut(BaseModel):
    """Resultado de dar de alta una campaña: la campaña y el job de ETL creado."""

    campana: CampanaOut
    job: JobOut


class CampanaEventoOut(BaseModel):
    """La fecha capturada (o pendiente) de un hito FDA para una campaña."""

    id_evento: int
    codigo: str
    nombre: str
    fecha: datetime | None
    actualizado_en: datetime | None


class CampanaEventoUpsertIn(BaseModel):
    """Body para capturar o corregir la fecha de un hito FDA."""

    fecha: datetime
