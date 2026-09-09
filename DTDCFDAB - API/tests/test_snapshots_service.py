from sqlalchemy import text

from src.services.snapshots import get_snapshot, list_snapshots_vigentes


def _insertar_snapshot(engine, id_campana, id_configuracion, calculado_en):
    with engine.begin() as connection:
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_campana_snapshot (id_campana, id_configuracion, calculado_en) '
                'VALUES (:id_campana, :id_configuracion, :calculado_en)'
            ),
            {'id_campana': id_campana, 'id_configuracion': id_configuracion, 'calculado_en': calculado_en},
        )


def _insertar_configuracion_vigente(engine, id_configuracion):
    with engine.begin() as connection:
        connection.execute(
            text(
                'INSERT INTO dtdcfdab_configuracion '
                '(id_configuracion, nombre, porcentaje_fin, porcentaje_inicio, porcentaje_bloque_minimo, '
                'hueco_entregas_dias, desfase_rescate_dias, cobertura_aviso, es_vigente, creado_en) '
                "VALUES (:id_configuracion, 'v1', 0.99, 0.01, 0.05, 10, 0.622, 0.95, 1, '2026-01-01')"
            ),
            {'id_configuracion': id_configuracion},
        )


def test_get_snapshot_no_encontrado_regresa_none(engine):
    assert get_snapshot(engine, id_campana=1, id_configuracion=1) is None


def test_get_snapshot_encontrado(engine):
    _insertar_snapshot(engine, 1, 1, '2026-08-01')

    resultado = get_snapshot(engine, id_campana=1, id_configuracion=1)

    assert resultado['id_campana'] == 1


def test_list_snapshots_vigentes_filtra_por_configuracion_vigente(engine):
    _insertar_configuracion_vigente(engine, 2)
    _insertar_snapshot(engine, 1, 1, '2026-07-01')  # de una config vieja, no vigente
    _insertar_snapshot(engine, 1, 2, '2026-08-01')
    _insertar_snapshot(engine, 2, 2, '2026-08-02')

    resultado = list_snapshots_vigentes(engine)

    assert {snapshot['id_campana'] for snapshot in resultado} == {1, 2}


def test_list_snapshots_vigentes_sin_configuracion_vigente_regresa_vacio(engine):
    assert list_snapshots_vigentes(engine) == []
