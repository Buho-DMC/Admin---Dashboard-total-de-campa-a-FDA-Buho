"""Tests de analisis_de_fechas.py — cálculo puro, sin Streamlit."""

from datetime import datetime

import analisis_de_fechas

_SNAPSHOT_A = {
    'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-03T00:00:00',
    'inicio_entregas': '2023-01-10T00:00:00', 'fin_entregas': '2023-01-12T00:00:00',
}
_SNAPSHOT_B = {
    'inicio_carga_artes': '2023-02-01T00:00:00', 'fin_carga_artes': '2023-02-06T00:00:00',
    'inicio_entregas': '2023-02-15T00:00:00', 'fin_entregas': '2023-02-19T00:00:00',
}


def test_calcular_duracion_vs_promedio_calcula_delta_correcto():
    resultado = analisis_de_fechas.calcular_duracion_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    # Carga de artes: A dura 2 días, B dura 5 días -> promedio 3.5 -> delta de A = 2 - 3.5 = -1.5
    assert resultado['Carga de artes'] == (2.0, -1.5)


def test_calcular_duracion_vs_promedio_etapa_sin_datos_es_none():
    resultado = analisis_de_fechas.calcular_duracion_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    assert resultado['Aprobaciones'] is None


def test_calcular_offset_vs_promedio_usa_inicio_carga_artes_como_base():
    resultado = analisis_de_fechas.calcular_offset_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    # Offset de Inicio Entregas en A: 9 días (10 ene - 1 ene). En B: 14 días (15 feb - 1 feb).
    # Promedio: 11.5 -> delta de A = 9 - 11.5 = -2.5
    assert resultado['Inicio Entregas'] == (9.0, -2.5)
    # El offset del primer hito (Inicio Carga de artes) es siempre 0 respecto a sí mismo.
    assert resultado['Inicio Carga de artes'] == (0.0, 0.0)


def test_calcular_offset_vs_promedio_incluye_offset_de_fin_de_etapa():
    resultado = analisis_de_fechas.calcular_offset_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    # Offset de Fin Entregas en A: 11 días (12 ene - 1 ene). En B: 18 días (19 feb - 1 feb).
    # Promedio: 14.5 -> delta de A = 11 - 14.5 = -3.5
    assert resultado['Fin Entregas'] == (11.0, -3.5)


def test_listar_fechas_ordenadas_ordena_cronologicamente():
    resultado = analisis_de_fechas.listar_fechas_ordenadas(_SNAPSHOT_A)
    assert resultado[0] == ('Inicio Carga de artes', datetime(2023, 1, 1))
    assert resultado[-1] == ('Fin Entregas', datetime(2023, 1, 12))


def test_listar_fechas_ordenadas_ignora_fechas_ausentes():
    resultado = analisis_de_fechas.listar_fechas_ordenadas({'inicio_carga_artes': '2023-01-01T00:00:00'})
    assert resultado == [('Inicio Carga de artes', datetime(2023, 1, 1))]


def test_calcular_dia_del_mes_vs_promedio_calcula_delta_correcto():
    resultado = analisis_de_fechas.calcular_dia_del_mes_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    # Fin Carga de artes: A cae día 3, B día 6 -> promedio 4.5 -> delta de A = 3 - 4.5 = -1.5
    assert resultado['Fin Carga de artes'] == (3.0, -1.5)
    # Fin Entregas: A cae día 12, B día 19 -> promedio 15.5 -> delta de A = 12 - 15.5 = -3.5
    assert resultado['Fin Entregas'] == (12.0, -3.5)


def test_calcular_dia_del_mes_vs_promedio_respeta_el_orden_cronologico():
    resultado = analisis_de_fechas.calcular_dia_del_mes_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    assert list(resultado.keys()) == ['Inicio Carga de artes', 'Fin Carga de artes', 'Inicio Entregas', 'Fin Entregas']


def test_calcular_dia_del_mes_vs_promedio_solo_incluye_fechas_de_la_campana_seleccionada():
    resultado = analisis_de_fechas.calcular_dia_del_mes_vs_promedio(_SNAPSHOT_A, [_SNAPSHOT_A, _SNAPSHOT_B])
    assert 'Inicio Aprobaciones' not in resultado


def test_calcular_dia_del_mes_vs_promedio_sin_campanas_para_promediar_es_none():
    resultado = analisis_de_fechas.calcular_dia_del_mes_vs_promedio(_SNAPSHOT_A, [])
    assert resultado['Inicio Carga de artes'] is None


def test_aplicar_percentiles_a_snapshot_actualiza_fechas_segun_rejilla():
    snapshot = {
        'id_campana': 1,
        'inicio_pick_pack': '2026-01-05T08:00:00',
        'fin_pick_pack': '2026-01-20T18:00:00',
        'distribucion_percentiles': {
            'pick_pack': {
                'inicio': {'0.5': '2026-01-05T09:00:00', '1.0': '2026-01-05T10:00:00'},
                'fin': {'95.0': '2026-01-19T17:00:00', '99.0': '2026-01-20T18:00:00'},
            }
        },
    }
    resultado = analisis_de_fechas.aplicar_percentiles_a_snapshot(
        snapshot,
        percentiles_inicio={'pick_pack': 0.5},
        percentiles_fin={'pick_pack': 95.0},
    )
    assert resultado['inicio_pick_pack'] == '2026-01-05T09:00:00'
    assert resultado['fin_pick_pack'] == '2026-01-19T17:00:00'


def test_aplicar_percentiles_a_snapshot_sin_distribucion_retorna_copia_sin_cambios():
    snapshot = {'id_campana': 1, 'inicio_pick_pack': '2026-01-05T08:00:00'}
    resultado = analisis_de_fechas.aplicar_percentiles_a_snapshot(
        snapshot,
        percentiles_inicio={'pick_pack': 0.5},
        percentiles_fin={'pick_pack': 95.0},
    )
    assert resultado == snapshot


def test_calcular_offset_cronologico_toma_hito_minimo_como_dia_cero():
    snapshot = {
        'inicio_carga_artes': '2026-01-08T00:00:00',
        'fin_carga_artes': '2026-01-10T00:00:00',
    }
    eventos = [
        {'nombre': 'Kickoff FDA', 'fecha': '2026-01-05T00:00:00'},
        {'nombre': 'Lanzamiento', 'fecha': '2026-01-12T00:00:00'},
    ]
    resultado = analisis_de_fechas.calcular_offset_cronologico(snapshot, eventos)

    # El orden cronológico debe ser:
    # 1. Kickoff FDA (Día 0)
    # 2. Inicio Carga de artes (+3 días)
    # 3. Fin Carga de artes (+5 días)
    # 4. Lanzamiento (+7 días)
    claves = list(resultado.keys())
    assert claves == ['Kickoff FDA', 'Inicio Carga de artes', 'Fin Carga de artes', 'Lanzamiento']
    assert resultado['Kickoff FDA'] == (0.0, None)
    assert resultado['Inicio Carga de artes'] == (3.0, None)
    assert resultado['Fin Carga de artes'] == (5.0, None)
    assert resultado['Lanzamiento'] == (7.0, None)

