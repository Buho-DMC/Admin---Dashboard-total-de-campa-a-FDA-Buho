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
    # Offset de Entregas en A: 9 días (10 ene - 1 ene). En B: 14 días (15 feb - 1 feb).
    # Promedio: 11.5 -> delta de A = 9 - 11.5 = -2.5
    assert resultado['Entregas'] == (9.0, -2.5)


def test_listar_fechas_ordenadas_ordena_cronologicamente():
    resultado = analisis_de_fechas.listar_fechas_ordenadas(_SNAPSHOT_A)
    assert resultado[0] == ('Inicio Carga de artes', datetime(2023, 1, 1))
    assert resultado[-1] == ('Fin Entregas', datetime(2023, 1, 12))


def test_listar_fechas_ordenadas_ignora_fechas_ausentes():
    resultado = analisis_de_fechas.listar_fechas_ordenadas({'inicio_carga_artes': '2023-01-01T00:00:00'})
    assert resultado == [('Inicio Carga de artes', datetime(2023, 1, 1))]
