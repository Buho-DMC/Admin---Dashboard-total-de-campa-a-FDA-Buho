"""Test de integracion end-to-end: alta de campana -> hitos -> job -> snapshot."""

import uuid
from datetime import datetime

from dtdcfdab_db.models import Campana, CampanaEvento, CampanaSnapshot, Configuracion, Evento, JobEjecucion


def test_alta_de_campana_completa(db_session):
    campana = Campana(id_claw=5001, cliente='FDA', nombre='FDA INTEGRACION26', inicio_campana=datetime(2026, 9, 1))
    db_session.add(campana)
    db_session.flush()

    eventos = db_session.query(Evento).order_by(Evento.orden).all()
    assert len(eventos) == 7
    for indice_evento, evento in enumerate(eventos):
        db_session.add(
            CampanaEvento(
                id_campana=campana.id_campana, id_evento=evento.id_evento, fecha=datetime(2026, 8, 1 + indice_evento)
            )
        )
    db_session.flush()
    assert db_session.query(CampanaEvento).filter_by(id_campana=campana.id_campana).count() == 7

    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    id_lote = str(uuid.uuid4())
    job = JobEjecucion(
        id_campana=campana.id_campana,
        id_lote=id_lote,
        id_configuracion=configuracion_vigente.id_configuracion,
        tipo='alta',
        estado='corriendo',
        iniciado_en=datetime(2026, 9, 1, 8, 0),
    )
    db_session.add(job)
    db_session.flush()

    snapshot = CampanaSnapshot(
        id_campana=campana.id_campana,
        id_configuracion=configuracion_vigente.id_configuracion,
        inicio_carga_artes=datetime(2026, 8, 5),
        fin_carga_artes=datetime(2026, 8, 10),
        fin_entregas=datetime(2026, 9, 20),
        numero_envios=1500,
        envios_con_fecha=1400,
        envios_sin_fecha=100,
        numero_folios=30,
        folios_invertidos=0,
    )
    db_session.add(snapshot)

    job.estado = 'exitoso'
    job.terminado_en = datetime(2026, 9, 1, 12, 0)
    db_session.flush()

    assert db_session.query(CampanaEvento).filter_by(id_campana=campana.id_campana).count() == 7
    snapshot_leido = (
        db_session.query(CampanaSnapshot)
        .filter_by(id_campana=campana.id_campana, id_configuracion=configuracion_vigente.id_configuracion)
        .one()
    )
    assert snapshot_leido.numero_envios == 1500
    job_leido = db_session.query(JobEjecucion).filter_by(id_campana=campana.id_campana).one()
    assert job_leido.estado == 'exitoso'
