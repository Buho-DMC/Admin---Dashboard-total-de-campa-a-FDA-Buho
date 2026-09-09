import math

import pandas as pd
import pytest

from src.services.snapshot_campana import bloques_de_actividad, inicio_por_bloque, punto_de_avance


def test_punto_de_avance_devuelve_el_evento_en_la_posicion_exacta():
    eventos = pd.to_datetime(['2026-01-01', '2026-01-03', '2026-01-02'])

    resultado = punto_de_avance(eventos, porcentaje=0.5)

    assert resultado == pd.Timestamp('2026-01-02')


def test_punto_de_avance_sin_eventos_regresa_nat():
    eventos_vacios = pd.Series([], dtype='datetime64[ns]')

    resultado = punto_de_avance(eventos_vacios, porcentaje=0.5)

    assert pd.isna(resultado)


def test_punto_de_avance_con_denominador_explicito_puede_no_alcanzar_el_porcentaje():
    eventos = pd.to_datetime(['2026-01-01', '2026-01-02'])

    resultado = punto_de_avance(eventos, porcentaje=0.5, numero_denominador=10)

    assert pd.isna(resultado)


def test_bloques_de_actividad_separa_por_hueco():
    fechas = pd.to_datetime(['2026-01-01', '2026-01-02', '2026-01-10'])

    _, resumen_de_bloques = bloques_de_actividad(fechas, dias_de_hueco=3)

    assert len(resumen_de_bloques) == 2
    assert resumen_de_bloques.iloc[0]['n'] == 2
    assert resumen_de_bloques.iloc[1]['n'] == 1
    assert resumen_de_bloques.iloc[0]['peso'] == pytest.approx(2 / 3)


def test_bloques_de_actividad_sin_fechas_regresa_resumen_vacio():
    fechas_vacias = pd.Series([], dtype='datetime64[ns]')

    identificador_de_bloque, resumen_de_bloques = bloques_de_actividad(fechas_vacias, dias_de_hueco=3)

    assert identificador_de_bloque.empty
    assert resumen_de_bloques.empty


def test_inicio_por_bloque_descarta_bloque_chico_al_inicio():
    fechas = pd.to_datetime(['2026-01-01', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08'])

    resultado, _ = inicio_por_bloque(fechas, porcentaje_minimo=0.5, dias_de_hueco=3)

    assert resultado == pd.Timestamp('2026-01-05')


def test_inicio_por_bloque_si_ningun_bloque_alcanza_el_minimo_usa_la_fecha_mas_temprana():
    fechas = pd.to_datetime(['2026-01-01', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08'])

    resultado, _ = inicio_por_bloque(fechas, porcentaje_minimo=0.99, dias_de_hueco=3)

    assert resultado == pd.Timestamp('2026-01-01')
