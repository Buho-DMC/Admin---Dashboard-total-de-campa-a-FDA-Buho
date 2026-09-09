"""Tests de la tabla dtdcfdab_job_ejecucion."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import OperationalError

from dtdcfdab_db.models import Campana, Configuracion, JobEjecucion


def test_job_por_campana_agrupado_por_lote(db_session):
    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    id_lote = str(uuid.uuid4())

    campanas = []
    for id_claw in (3001, 3002, 3003):
        campana = Campana(id_claw=id_claw, nombre=f'Campana {id_claw}', inicio_campana=datetime(2026, 1, 1))
        db_session.add(campana)
        campanas.append(campana)
    db_session.flush()

    for campana in campanas:
        db_session.add(
            JobEjecucion(
                id_campana=campana.id_campana,
                id_lote=id_lote,
                id_configuracion=configuracion_vigente.id_configuracion,
                tipo='recalculo',
                estado='pendiente',
            )
        )
    db_session.flush()

    jobs_del_lote = db_session.query(JobEjecucion).filter_by(id_lote=id_lote).all()
    assert len(jobs_del_lote) == 3
    assert all(job.estado == 'pendiente' for job in jobs_del_lote)
    assert all(job.iniciado_en is None for job in jobs_del_lote)


def test_tipo_invalido_rechazado(db_session):
    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    campana = Campana(id_claw=3004, nombre='Campana tipo invalido', inicio_campana=datetime(2026, 1, 1))
    db_session.add(campana)
    db_session.flush()

    db_session.add(
        JobEjecucion(
            id_campana=campana.id_campana,
            id_configuracion=configuracion_vigente.id_configuracion,
            tipo='no_existe',
            estado='pendiente',
        )
    )
    with pytest.raises(OperationalError):
        db_session.flush()
