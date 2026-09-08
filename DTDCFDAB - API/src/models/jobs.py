"""Modelos Pydantic de jobs de ejecución."""

from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    """Estado de un job de ETL (alta o recálculo)."""

    id_job_ejecucion: int
    id_campana: int
    id_lote: str | None
    id_configuracion: int
    tipo: str
    estado: str
    iniciado_en: datetime | None
    terminado_en: datetime | None
    error: str | None
