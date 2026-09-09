"""Modelos SQLAlchemy de las 6 tablas dtdcfdab_* en la base compartida dmc-general.

Los nombres de tabla/columna aquí son la fuente de verdad para el esquema físico,
pero deben coincidir exactamente con el SQL crudo que ya usa DTDCFDAB - API en
producción (ver src/services/*.py de esa carpeta) — esta API no importa este
paquete, tiene su propia conexión a MySQL, así que un nombre distinto aquí no
truena en tiempo de importación: rompe en producción la primera vez que corre
una query.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base compartida por las 6 tablas de este paquete."""


class Evento(Base):
    """Catálogo de los 7 hitos FDA (manuales, no dependen de parámetros).

    Agregar un milestone nuevo es un INSERT en esta tabla — el formulario de
    alta, el Gantt y la pestaña Metodología se generan a partir de este
    catálogo en vez de tener el nombre de cada hito hardcodeado en el código.
    """

    __tablename__ = 'dtdcfdab_evento'

    id_evento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    origen: Mapped[str] = mapped_column(String(16), nullable=False, server_default='manual')
    rol: Mapped[str] = mapped_column(String(16), nullable=False, server_default='hito')
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("origen IN ('manual')", name='ck_evento_origen'),
        CheckConstraint("rol IN ('hito')", name='ck_evento_rol'),
    )


class Campana(Base):
    """Una campaña FDA dada de alta, identificada por su id_claw único de Retool/Claw."""

    __tablename__ = 'dtdcfdab_campana'

    id_campana: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_claw: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    cliente: Mapped[str] = mapped_column(String(32), nullable=False, server_default='FDA')
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    inicio_campana: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_alta: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))


class CampanaEvento(Base):
    """Fecha vigente de un hito FDA capturado a mano para una campaña.

    Solo guarda la versión vigente (sin historial de cómo cambió) — cada
    captura hace UPSERT sobre la misma fila en vez de insertar una nueva.
    """

    __tablename__ = 'dtdcfdab_campana_evento'

    id_campana: Mapped[int] = mapped_column(ForeignKey('dtdcfdab_campana.id_campana'), primary_key=True)
    id_evento: Mapped[int] = mapped_column(ForeignKey('dtdcfdab_evento.id_evento'), primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
    )


class Configuracion(Base):
    """Combinación de los 6 parámetros de Política D — una sola fila es_vigente=True a la vez.

    `es_vigente` es global (nunca por campaña): comparar dos campañas
    calculadas con parámetros distintos no sería válido, así que solo una
    combinación está activa para todas las campañas al mismo tiempo.
    """

    __tablename__ = 'dtdcfdab_configuracion'

    id_configuracion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    porcentaje_fin: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), nullable=False)
    porcentaje_inicio: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), nullable=False)
    porcentaje_bloque_minimo: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), nullable=False)
    hueco_entregas_dias: Mapped[Decimal] = mapped_column(DECIMAL(6, 2), nullable=False)
    desfase_rescate_dias: Mapped[Decimal] = mapped_column(DECIMAL(6, 3), nullable=False)
    cobertura_aviso: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), nullable=False)
    es_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))


class CampanaSnapshot(Base):
    """Resultado completo de un ETL para (campaña, configuración) — atómico, nunca a medias.

    Un fallo del ETL nunca deja una fila parcial aquí: la API solo inserta el
    snapshot completo tras terminar las 7 etapas y los 3 KPIs de ciclo. Sin
    esta fila, el dashboard muestra la campaña como "pendiente", nunca datos
    viejos disfrazados de vigentes.
    """

    __tablename__ = 'dtdcfdab_campana_snapshot'

    id_campana: Mapped[int] = mapped_column(ForeignKey('dtdcfdab_campana.id_campana'), primary_key=True)
    id_configuracion: Mapped[int] = mapped_column(
        ForeignKey('dtdcfdab_configuracion.id_configuracion'), primary_key=True
    )

    inicio_carga_artes: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_carga_artes: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_carga_preproyectos: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_carga_preproyectos: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_aprobaciones: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_aprobaciones: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_impresion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_impresion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_precampana: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_precampana: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_pick_pack: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_pick_pack: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_entregas: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fin_entregas: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    porcentaje_alcanzado_entregas: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 6), nullable=True)
    ultima_entrega: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    numero_envios: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envios_con_fecha: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envios_sin_fecha: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envios_sin_registro_entrega: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_cajas_pick_pack: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_folios: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_odps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_actividades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respuesta_buho_dias: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 4), nullable=True)
    respuesta_fda_dias: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 4), nullable=True)
    folios_invertidos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calculado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))


class JobEjecucion(Base):
    """Una fila por campaña de un job de ETL, agrupable por id_lote para ver progreso de un lote.

    `iniciado_en` queda en NULL mientras el job está 'pendiente' — la API lo
    llena solo al pasar a 'corriendo', así que forzar NOT NULL aquí rompería
    la inserción inicial de cada job.
    """

    __tablename__ = 'dtdcfdab_job_ejecucion'

    id_job_ejecucion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_campana: Mapped[int] = mapped_column(ForeignKey('dtdcfdab_campana.id_campana'), nullable=False)
    id_lote: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    id_configuracion: Mapped[int] = mapped_column(
        ForeignKey('dtdcfdab_configuracion.id_configuracion'), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(16), nullable=False)
    estado: Mapped[str] = mapped_column(String(16), nullable=False, server_default='pendiente')
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("tipo IN ('alta','recalculo')", name='ck_job_tipo'),
        CheckConstraint("estado IN ('pendiente','corriendo','exitoso','fallido')", name='ck_job_estado'),
    )
