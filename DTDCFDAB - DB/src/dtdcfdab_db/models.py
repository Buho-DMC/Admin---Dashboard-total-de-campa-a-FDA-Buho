"""Modelos SQLAlchemy de las 6 tablas dtdcfdab_* en la base compartida dmc-general.

Los nombres de tabla/columna aquí son la fuente de verdad para el esquema físico,
pero deben coincidir exactamente con el SQL crudo que ya usa DTDCFDAB - API en
producción (ver src/services/*.py de esa carpeta) — esta API no importa este
paquete, tiene su propia conexión a MySQL, así que un nombre distinto aquí no
truena en tiempo de importación: rompe en producción la primera vez que corre
una query.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, text
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
