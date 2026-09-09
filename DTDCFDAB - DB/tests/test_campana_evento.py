"""Tests de la tabla dtdcfdab_campana_evento."""

from datetime import datetime

from dtdcfdab_db.models import Campana, CampanaEvento, Evento


def test_upsert_hito_reemplaza_fecha_vigente(db_session):
    campana = Campana(id_claw=1001, nombre='Campana de prueba', inicio_campana=datetime(2026, 1, 1))
    evento = db_session.query(Evento).filter_by(codigo='liberacion_pop').one()
    db_session.add(campana)
    db_session.flush()

    campana_evento = CampanaEvento(
        id_campana=campana.id_campana, id_evento=evento.id_evento, fecha=datetime(2026, 3, 1)
    )
    db_session.add(campana_evento)
    db_session.flush()

    campana_evento.fecha = datetime(2026, 3, 5)
    db_session.flush()

    fila = (
        db_session.query(CampanaEvento)
        .filter_by(id_campana=campana.id_campana, id_evento=evento.id_evento)
        .one()
    )
    assert fila.fecha == datetime(2026, 3, 5)
    assert (
        db_session.query(CampanaEvento)
        .filter_by(id_campana=campana.id_campana, id_evento=evento.id_evento)
        .count()
        == 1
    )
