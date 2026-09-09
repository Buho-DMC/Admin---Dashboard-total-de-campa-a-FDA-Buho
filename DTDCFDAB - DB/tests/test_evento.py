"""Tests de la tabla dtdcfdab_evento."""

import pytest
from sqlalchemy.exc import IntegrityError

from dtdcfdab_db.models import Evento


def test_catalogo_evento_tiene_7_hitos_fda(db_session):
    eventos = db_session.query(Evento).order_by(Evento.orden).all()
    assert len(eventos) == 7
    assert eventos[0].codigo == 'entrega_promociones_ac'
    assert eventos[-1].codigo == 'liberacion_folleto'
    assert all(evento.rol == 'hito' for evento in eventos)
    assert all(evento.origen == 'manual' for evento in eventos)


def test_codigo_evento_es_unico(db_session):
    evento_duplicado = Evento(codigo='entrega_promociones_ac', nombre='Duplicado de prueba', orden=99)
    db_session.add(evento_duplicado)
    with pytest.raises(IntegrityError):
        db_session.flush()
