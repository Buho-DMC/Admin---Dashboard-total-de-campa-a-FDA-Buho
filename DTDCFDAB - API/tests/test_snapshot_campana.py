import math

import pandas as pd
import pytest

from src.services.snapshot_campana import (
    bloques_de_actividad,
    inicio_por_bloque,
    punto_de_avance,
    regla_ciclo_folio_valido,
    regla_folios_validos,
    regla_odps_validas,
    regla_precampana_dia_sin_operacion,
    regla_rescate_entregas,
)


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


def test_regla_folios_validos_descarta_folio_cero_y_sin_fecha():
    folios = pd.DataFrame({
        'folio': ['A1', '0', 'A2'],
        'fecha_arte': pd.to_datetime(['2026-01-01', '2026-01-01', None]),
        'fecha_preproyecto': pd.to_datetime([None, None, None]),
        'fecha_aprobacion_arte': pd.to_datetime([None, None, None]),
        'fecha_aprobacion_odt': pd.to_datetime([None, None, None]),
    })

    folios_validos, metadatos = regla_folios_validos(folios)

    assert list(folios_validos['folio']) == ['A1']
    assert metadatos == {
        'folios_entrada': 3, 'folios_folio_cero': 1, 'folios_sin_fecha': 1,
        'folios_descartados': 2, 'folios_validos': 1,
    }


def test_regla_odps_validas_descarta_instantaneas_y_reenvios():
    odps = pd.DataFrame({
        'id_claw': [229, 229, 229],
        'inicio_produccion': pd.to_datetime(['2026-01-05 08:00:00', '2026-01-05 08:00:00', '2026-01-11 08:00:00']),
        'fin_produccion': pd.to_datetime(['2026-01-05 08:00:30', '2026-01-05 08:10:00', '2026-01-11 08:05:00']),
    })
    contexto = {'fin_pick_pack': pd.Timestamp('2026-01-10 09:15')}

    odps_validas, metadatos = regla_odps_validas(odps, contexto)

    assert len(odps_validas) == 1
    assert metadatos['odps_instantaneas'] == 1
    assert metadatos['odps_reenvio'] == 1
    assert metadatos['odps_validas'] == 1


def test_regla_odps_validas_sin_fin_pick_pack_en_contexto_lanza_valueerror():
    odps = pd.DataFrame({'inicio_produccion': pd.to_datetime([]), 'fin_produccion': pd.to_datetime([])})

    with pytest.raises(ValueError):
        regla_odps_validas(odps, {})


def test_regla_precampana_dia_sin_operacion_marca_registro_que_cruza_dia_sin_actividad():
    registros = pd.DataFrame({
        'hora_inicio': pd.to_datetime(['2026-01-01 08:00', '2026-01-05 08:00']),
        'hora_fin': pd.to_datetime(['2026-01-01 09:00', '2026-01-08 08:00']),
    })

    resultado, metadatos = regla_precampana_dia_sin_operacion(registros)

    assert list(resultado['abierto']) == [False, True]
    assert resultado.iloc[0]['hora_fin_valida'] == pd.Timestamp('2026-01-01 09:00')
    assert pd.isna(resultado.iloc[1]['hora_fin_valida'])
    assert metadatos == {'registros_entrada': 2, 'registros': 2, 'registros_abiertos': 1}


def test_regla_rescate_entregas_rellena_solo_lo_que_falta_y_conserva_todas_las_filas():
    envios = pd.DataFrame({
        'Fecha Entrega': [pd.Timestamp('2026-01-15'), pd.NaT, pd.NaT],
        'Fecha Última Actualización': [pd.NaT, pd.Timestamp('2026-01-16'), pd.NaT],
        'Estatus': ['Entregado', 'Entregado', 'En transito'],
    })
    contexto = {'desfase_rescate_dias': 0.5}

    resultado, metadatos = regla_rescate_entregas(envios, contexto)

    assert resultado.iloc[0]['fecha_final'] == pd.Timestamp('2026-01-15')
    assert resultado.iloc[1]['fecha_final'] == pd.Timestamp('2026-01-16 12:00:00')
    assert pd.isna(resultado.iloc[2]['fecha_final'])
    assert metadatos['rescatados'] == 1
    assert metadatos['sin_fecha_entregado'] == 0
    assert metadatos['sin_registro_entrega'] == 1


def test_regla_rescate_entregas_sin_columnas_esperadas_lanza_valueerror():
    envios_sin_columnas = pd.DataFrame({'Fecha Entrega': [pd.NaT]})

    with pytest.raises(ValueError):
        regla_rescate_entregas(envios_sin_columnas, {'desfase_rescate_dias': 0})


def test_regla_ciclo_folio_valido_descarta_folio_con_tramo_negativo():
    folios = pd.DataFrame({
        'fecha_arte': pd.to_datetime(['2026-01-01', '2026-01-05']),
        'fecha_preproyecto': pd.to_datetime(['2026-01-02', '2026-01-03']),
        'fecha_aprobacion_arte': pd.to_datetime(['2026-01-04', '2026-01-06']),
        'fecha_aprobacion_odt': pd.to_datetime(['2026-01-04', '2026-01-06']),
    })

    folios_validos, metadatos = regla_ciclo_folio_valido(folios)

    assert len(folios_validos) == 1
    assert metadatos['folios_invertidos'] == 1
