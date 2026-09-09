"""Tests de la tabla dtdcfdab_campana."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from dtdcfdab_db.models import Campana


def test_crear_campana(db_session):
    campana = Campana(
        id_claw=252, cliente='FDA', nombre='FDA OCT26', inicio_campana=datetime(2026, 9, 4, 23, 19, 59)
    )
    db_session.add(campana)
    db_session.flush()
    assert campana.id_campana is not None
    assert campana.cliente == 'FDA'


def test_id_claw_es_unico(db_session):
    db_session.add(Campana(id_claw=999, nombre='Campana A', inicio_campana=datetime(2026, 1, 1)))
    db_session.flush()
    db_session.add(Campana(id_claw=999, nombre='Campana B', inicio_campana=datetime(2026, 1, 2)))
    with pytest.raises(IntegrityError):
        db_session.flush()
