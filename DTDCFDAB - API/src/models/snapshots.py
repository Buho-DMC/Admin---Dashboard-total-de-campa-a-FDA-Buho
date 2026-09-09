"""Modelos Pydantic de snapshots de ETL."""

from datetime import datetime

from pydantic import BaseModel


class SnapshotOut(BaseModel):
    """Un resultado de ETL completo para (campaña, configuración): 14 fechas Búho + 13 metadatos."""

    id_campana: int
    id_configuracion: int
    inicio_carga_artes: datetime | None
    fin_carga_artes: datetime | None
    inicio_carga_preproyectos: datetime | None
    fin_carga_preproyectos: datetime | None
    inicio_aprobaciones: datetime | None
    fin_aprobaciones: datetime | None
    inicio_impresion: datetime | None
    fin_impresion: datetime | None
    inicio_precampana: datetime | None
    fin_precampana: datetime | None
    inicio_pick_pack: datetime | None
    fin_pick_pack: datetime | None
    inicio_entregas: datetime | None
    fin_entregas: datetime | None
    porcentaje_alcanzado_entregas: float | None
    ultima_entrega: datetime | None
    numero_envios: int | None
    envios_con_fecha: int | None
    envios_sin_fecha: int | None
    envios_sin_registro_entrega: int | None
    numero_cajas_pick_pack: int | None
    numero_folios: int | None
    numero_odps: int | None
    numero_actividades: int | None
    respuesta_buho_dias: float | None
    respuesta_fda_dias: float | None
    folios_invertidos: int | None
    calculado_en: datetime | None
