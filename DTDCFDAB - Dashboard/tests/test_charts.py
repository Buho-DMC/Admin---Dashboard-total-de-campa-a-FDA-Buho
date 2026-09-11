"""Tests de charts.py — validan la lógica de la gráfica ilustrativa de percentil, no el render."""

import pytest

import charts


def test_construir_grafica_de_percentil_lanza_valueerror_fuera_de_rango():
    with pytest.raises(ValueError):
        charts.construir_grafica_de_percentil(0, 'Prueba')
    with pytest.raises(ValueError):
        charts.construir_grafica_de_percentil(1, 'Prueba')


def test_construir_grafica_de_percentil_sombrea_aproximadamente_la_proporcion_pedida():
    figura = charts.construir_grafica_de_percentil(0.5, 'Prueba')
    traza_sombreada = figura.data[1]
    # Para el percentil 50 de una normal estándar, el corte z es 0.
    assert max(traza_sombreada.x) == pytest.approx(0, abs=0.1)


def test_construir_grafica_de_percentil_usa_el_titulo_recibido():
    figura = charts.construir_grafica_de_percentil(0.95, 'Cobertura de aviso (0.95)')
    assert figura.layout.title.text == 'Cobertura de aviso (0.95)'


def test_construir_grafica_de_linea_de_tiempo_con_todas_las_etapas():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00',
        'inicio_carga_preproyectos': '2023-01-03T00:00:00', 'fin_carga_preproyectos': '2023-01-04T00:00:00',
        'inicio_aprobaciones': '2023-01-05T00:00:00', 'fin_aprobaciones': '2023-01-06T00:00:00',
        'inicio_impresion': '2023-01-07T00:00:00', 'fin_impresion': '2023-01-08T00:00:00',
        'inicio_precampana': '2023-01-09T00:00:00', 'fin_precampana': '2023-01-10T00:00:00',
        'inicio_pick_pack': '2023-01-11T00:00:00', 'fin_pick_pack': '2023-01-12T00:00:00',
        'inicio_entregas': '2023-01-13T00:00:00', 'fin_entregas': '2023-01-14T00:00:00',
    }
    figura = charts.construir_grafica_de_linea_de_tiempo(snapshot)
    assert figura is not None
    # Each stage might be graphed, we check the length of the data trace or number of bars
    assert len(figura.data) > 0


def test_construir_grafica_de_linea_de_tiempo_omite_incompletas():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00',
        'inicio_carga_preproyectos': '2023-01-03T00:00:00', 'fin_carga_preproyectos': None, # Incomplete
    }
    figura = charts.construir_grafica_de_linea_de_tiempo(snapshot)
    assert figura is not None


def test_construir_grafica_de_linea_de_tiempo_vacio_retorna_none():
    snapshot_vacio = {}
    assert charts.construir_grafica_de_linea_de_tiempo(snapshot_vacio) is None
    
    snapshot_incompleto = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': None,
    }
    assert charts.construir_grafica_de_linea_de_tiempo(snapshot_incompleto) is None
