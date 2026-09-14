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


def test_construir_grafica_por_actividad_con_todas_las_etapas():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00',
        'inicio_carga_preproyectos': '2023-01-03T00:00:00', 'fin_carga_preproyectos': '2023-01-04T00:00:00',
        'inicio_aprobaciones': '2023-01-05T00:00:00', 'fin_aprobaciones': '2023-01-06T00:00:00',
        'inicio_impresion': '2023-01-07T00:00:00', 'fin_impresion': '2023-01-08T00:00:00',
        'inicio_precampana': '2023-01-09T00:00:00', 'fin_precampana': '2023-01-10T00:00:00',
        'inicio_pick_pack': '2023-01-11T00:00:00', 'fin_pick_pack': '2023-01-12T00:00:00',
        'inicio_entregas': '2023-01-13T00:00:00', 'fin_entregas': '2023-01-14T00:00:00',
    }
    figura = charts.construir_grafica_por_actividad(snapshot, [])
    assert figura is not None
    assert len(figura.data) > 0


def test_construir_grafica_por_actividad_omite_incompletas():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00',
        'inicio_carga_preproyectos': '2023-01-03T00:00:00', 'fin_carga_preproyectos': None,
    }
    figura = charts.construir_grafica_por_actividad(snapshot, [])
    assert figura is not None


def test_construir_grafica_por_actividad_vacio_retorna_none():
    assert charts.construir_grafica_por_actividad({}, []) is None
    snapshot_incompleto = {'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': None}
    assert charts.construir_grafica_por_actividad(snapshot_incompleto, []) is None


def test_construir_grafica_por_actividad_incluye_marcador_por_hito_con_fecha():
    snapshot = {'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00'}
    eventos = [
        {'id_evento': 6, 'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'fecha': '2023-01-05T00:00:00', 'actualizado_en': None},
    ]
    figura = charts.construir_grafica_por_actividad(snapshot, eventos)
    nombres_de_trazo = [traza.name for traza in figura.data]
    assert 'Liberación POP' in nombres_de_trazo


def test_construir_grafica_por_actividad_ignora_hitos_sin_fecha():
    snapshot = {'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_carga_artes': '2023-01-02T00:00:00'}
    eventos = [
        {'id_evento': 6, 'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'fecha': None, 'actualizado_en': None},
    ]
    figura = charts.construir_grafica_por_actividad(snapshot, eventos)
    nombres_de_trazo = [traza.name for traza in figura.data]
    assert 'Liberación POP' not in nombres_de_trazo


def test_construir_grafica_por_actividad_solo_con_hitos_no_retorna_none():
    eventos = [
        {'id_evento': 6, 'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'fecha': '2023-01-05T00:00:00', 'actualizado_en': None},
    ]
    figura = charts.construir_grafica_por_actividad({}, eventos)
    assert figura is not None
    assert len(figura.data) == 1


def test_construir_grafica_por_actividad_usa_el_simbolo_del_hito():
    eventos = [
        {'id_evento': 6, 'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'fecha': '2023-01-05T00:00:00', 'actualizado_en': None},
    ]
    figura = charts.construir_grafica_por_actividad({}, eventos)
    assert figura.data[0].marker.symbol == 'star'


def test_construir_grafica_por_actividad_sin_etapas_ni_hitos_retorna_none():
    assert charts.construir_grafica_por_actividad({}, []) is None


def test_construir_grafica_por_responsable_con_los_3_bloques_completos():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_aprobaciones': '2023-01-05T00:00:00',
        'inicio_carga_preproyectos': '2023-01-02T00:00:00', 'fin_carga_preproyectos': '2023-01-03T00:00:00',
        'inicio_impresion': '2023-01-06T00:00:00', 'fin_pick_pack': '2023-01-10T00:00:00',
        'inicio_entregas': '2023-01-11T00:00:00', 'fin_entregas': '2023-01-15T00:00:00',
    }
    figura = charts.construir_grafica_por_responsable(snapshot)
    assert figura is not None
    assert len(figura.data) > 0


def test_construir_grafica_por_responsable_agrega_tiempo_muerto_si_hay_hueco():
    snapshot = {
        'inicio_carga_artes': '2023-01-01T00:00:00', 'fin_aprobaciones': '2023-01-05T00:00:00',
        'inicio_impresion': '2023-01-10T00:00:00', 'fin_pick_pack': '2023-01-15T00:00:00',
    }
    figura = charts.construir_grafica_por_responsable(snapshot)
    nombres_de_trazo = [traza.name for traza in figura.data]
    assert 'Tiempo muerto' in nombres_de_trazo


def test_construir_grafica_por_responsable_vacio_retorna_none():
    assert charts.construir_grafica_por_responsable({}) is None


def test_construir_grafica_de_percentiles_combinada_dibuja_una_linea_por_corte():
    figura = charts.construir_grafica_de_percentiles_combinada(
        {'Porcentaje inicio': 0.01, 'Porcentaje fin': 0.99, 'Cobertura de aviso': 0.95}
    )
    lineas_verticales = figura.layout.shapes
    assert len(lineas_verticales) == 3


def test_construir_grafica_de_percentiles_combinada_incluye_la_curva_base():
    figura = charts.construir_grafica_de_percentiles_combinada({'Porcentaje fin': 0.99})
    assert figura.data[0].name == 'Distribución ilustrativa'
    assert len(figura.data[0].x) > 0
