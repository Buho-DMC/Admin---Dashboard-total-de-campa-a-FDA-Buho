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
