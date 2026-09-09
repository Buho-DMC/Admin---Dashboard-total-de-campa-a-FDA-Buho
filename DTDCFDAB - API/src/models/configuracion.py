"""Modelos Pydantic de configuración del método."""

from datetime import datetime

from pydantic import BaseModel


class ConfiguracionOut(BaseModel):
    """Una combinación de parámetros del método (Política D)."""

    id_configuracion: int
    nombre: str | None
    porcentaje_fin: float
    porcentaje_inicio: float
    porcentaje_bloque_minimo: float
    hueco_entregas_dias: float
    desfase_rescate_dias: float
    cobertura_aviso: float
    es_vigente: bool
    creado_en: datetime


class ConfiguracionCreateIn(BaseModel):
    """Body para crear una combinación de parámetros nueva y marcarla vigente."""

    nombre: str | None = None
    porcentaje_fin: float
    porcentaje_inicio: float
    porcentaje_bloque_minimo: float
    hueco_entregas_dias: float
    desfase_rescate_dias: float
    cobertura_aviso: float


class ConfiguracionCreateOut(BaseModel):
    """Resultado de crear una configuración: la configuración y el recálculo encolado."""

    configuracion: ConfiguracionOut
    id_lote: str
    total_campanas: int
