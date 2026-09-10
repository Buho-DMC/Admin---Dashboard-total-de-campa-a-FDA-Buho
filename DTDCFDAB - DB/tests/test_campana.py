"""Tests de la tabla dtdcfdab_campana."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from dtdcfdab_db.models import Campana, CampanaEvento, CampanaSnapshot, Configuracion, Evento, JobEjecucion


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


def test_borrar_campana_hace_cascada_en_hitos_snapshot_y_jobs(db_session):
    campana = Campana(id_claw=4001, nombre='Campana a borrar', inicio_campana=datetime(2026, 1, 1))
    evento = db_session.query(Evento).filter_by(codigo='liberacion_pop').one()
    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    db_session.add(campana)
    db_session.flush()
    id_campana = campana.id_campana

    db_session.add(CampanaEvento(id_campana=id_campana, id_evento=evento.id_evento, fecha=datetime(2026, 3, 1)))
    db_session.add(
        CampanaSnapshot(id_campana=id_campana, id_configuracion=configuracion_vigente.id_configuracion, numero_envios=1)
    )
    db_session.add(
        JobEjecucion(
            id_campana=id_campana, id_configuracion=configuracion_vigente.id_configuracion, tipo='alta', estado='pendiente'
        )
    )
    db_session.flush()

    db_session.delete(campana)
    db_session.flush()

    assert db_session.query(CampanaEvento).filter_by(id_campana=id_campana).count() == 0
    assert db_session.query(CampanaSnapshot).filter_by(id_campana=id_campana).count() == 0
    assert db_session.query(JobEjecucion).filter_by(id_campana=id_campana).count() == 0
