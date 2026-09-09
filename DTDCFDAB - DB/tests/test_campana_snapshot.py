"""Tests de la tabla dtdcfdab_campana_snapshot."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from dtdcfdab_db.models import Campana, CampanaSnapshot, Configuracion


def test_un_snapshot_por_campana_y_configuracion(db_session):
    campana = Campana(id_claw=2001, nombre='Campana snapshot', inicio_campana=datetime(2026, 1, 1))
    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    db_session.add(campana)
    db_session.flush()

    snapshot = CampanaSnapshot(
        id_campana=campana.id_campana,
        id_configuracion=configuracion_vigente.id_configuracion,
        fin_entregas=datetime(2026, 6, 1),
        numero_envios=1908,
        folios_invertidos=1,
    )
    db_session.add(snapshot)
    db_session.flush()
    assert snapshot.calculado_en is not None

    snapshot_duplicado = CampanaSnapshot(
        id_campana=campana.id_campana, id_configuracion=configuracion_vigente.id_configuracion, numero_envios=1
    )
    db_session.add(snapshot_duplicado)
    with pytest.raises(IntegrityError):
        db_session.flush()
