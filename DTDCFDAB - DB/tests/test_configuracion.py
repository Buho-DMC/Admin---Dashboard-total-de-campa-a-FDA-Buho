"""Tests de la tabla dtdcfdab_configuracion."""

import pytest
from sqlalchemy.exc import IntegrityError

from dtdcfdab_db.models import Configuracion

PARAMETROS_DE_PRUEBA = dict(
    porcentaje_fin='0.9900',
    porcentaje_inicio='0.0100',
    porcentaje_bloque_minimo='0.0500',
    hueco_entregas_dias='10.00',
    desfase_rescate_dias='0.622',
    cobertura_aviso='0.9500',
)


def test_semilla_politica_d_es_vigente(db_session):
    configuracion_vigente = db_session.query(Configuracion).filter_by(es_vigente=True).one()
    assert str(configuracion_vigente.porcentaje_fin) == '0.9900'
    assert str(configuracion_vigente.hueco_entregas_dias) == '10.00'


def test_solo_una_configuracion_vigente_a_la_vez(db_session):
    configuracion_nueva = Configuracion(nombre='prueba', es_vigente=True, **PARAMETROS_DE_PRUEBA)
    db_session.add(configuracion_nueva)
    with pytest.raises(IntegrityError):
        db_session.flush()
