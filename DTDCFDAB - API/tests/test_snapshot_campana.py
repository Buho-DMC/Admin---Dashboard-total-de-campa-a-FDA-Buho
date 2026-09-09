import math

import httpx
import pandas as pd
import pytest

import src.services.snapshot_campana as snapshot_campana_module
from src.services.snapshot_campana import (
    calcular_snapshot_campana,
    RUTA_CLAW_PICKS,
    RUTA_CLAW_TRACKING,
    _calcular_extremo,
    _configuracion_del_extremo,
    _construir_configuracion_etapas,
    bloques_de_actividad,
    calcular_etapa,
    calcular_etapas,
    calcular_kpis_ciclo_folio,
    inicio_por_bloque,
    obtener_datos_claw,
    obtener_datos_retool_digital,
    obtener_datos_retool_precampana,
    punto_de_avance,
    regla_ciclo_folio_valido,
    regla_folios_validos,
    regla_odps_validas,
    regla_precampana_dia_sin_operacion,
    regla_rescate_entregas,
)

CONFIGURACION_DE_EJEMPLO = {
    'porcentaje_fin': 0.99, 'porcentaje_inicio': 0.01, 'porcentaje_bloque_minimo': 0.05,
    'hueco_entregas_dias': 10, 'desfase_rescate_dias': 0.622, 'cobertura_aviso': 0.95,
}


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


def test_configuracion_del_extremo_combina_lo_base_con_lo_propio_del_extremo():
    configuracion_etapa = {
        'unidad': 'folio', 'evento': ['fecha_arte'],
        'inicio': {'metodo': 'primero'}, 'fin': {'metodo': 'ultimo'},
    }

    resultado = _configuracion_del_extremo(configuracion_etapa, 'inicio')

    assert resultado == {'unidad': 'folio', 'evento': ['fecha_arte'], 'metodo': 'primero'}


def test_calcular_extremo_metodo_primero_sobre_pool_de_evento():
    datos = pd.DataFrame({'fecha_arte': pd.to_datetime(['2026-01-02', '2026-01-01'])})
    configuracion_extremo = {'evento': ['fecha_arte'], 'metodo': 'primero'}

    resultado = _calcular_extremo(datos, configuracion_extremo)

    assert resultado['valor'] == pd.Timestamp('2026-01-01')
    assert resultado['numero_unidades_total'] == 2
    assert resultado['numero_unidades_con_dato'] == 2


def test_calcular_extremo_metodo_avance():
    datos = pd.DataFrame({'fecha_final': pd.to_datetime(['2026-01-01', '2026-01-02', '2026-01-03'])})
    configuracion_extremo = {'evento_por_unidad': (None, 'fecha_final', None), 'metodo': 'avance', 'porcentaje': 0.5}

    resultado = _calcular_extremo(datos, configuracion_extremo)

    assert resultado['valor'] == pd.Timestamp('2026-01-02')


def test_calcular_extremo_metodo_bloque():
    datos = pd.DataFrame({'time': pd.to_datetime(['2026-01-01', '2026-01-01', '2026-01-10'])})
    configuracion_extremo = {
        'evento': ['time'], 'metodo': 'bloque', 'porcentaje_minimo': 0.5, 'dias_de_hueco': 3,
    }

    resultado = _calcular_extremo(datos, configuracion_extremo)

    assert resultado['valor'] == pd.Timestamp('2026-01-01')
    assert resultado['extras']['numero_bloques'] == 2


def test_calcular_extremo_desde_inicio_filtra_filas_previas_al_inicio():
    datos = pd.DataFrame({
        'box_id': [1, 1, 2],
        'time': pd.to_datetime(['2026-01-01', '2026-01-05', '2026-01-06']),
    })
    configuracion_extremo = {
        'unidad': 'caja', 'metodo': 'avance', 'porcentaje': 1.0,
        'evento_por_unidad': ('box_id', 'time', 'max'), 'desde': 'inicio',
    }

    resultado = _calcular_extremo(datos, configuracion_extremo, inicio=pd.Timestamp('2026-01-02'))

    assert resultado['valor'] == pd.Timestamp('2026-01-06')
    assert resultado['numero_unidades_total'] == 2


def test_calcular_extremo_metodo_bloque_final():
    datos = pd.DataFrame({'fecha_final': pd.to_datetime(['2026-01-01', '2026-01-02', '2026-01-20'])})
    configuracion_extremo = {
        'evento_por_unidad': (None, 'fecha_final', None), 'metodo': 'bloque_final', 'dias_de_hueco': 5,
    }

    resultado = _calcular_extremo(datos, configuracion_extremo)

    assert resultado['valor'] == pd.Timestamp('2026-01-02')


def test_calcular_extremo_metodo_desconocido_lanza_valueerror():
    datos = pd.DataFrame({'fecha_arte': pd.to_datetime(['2026-01-01'])})
    configuracion_extremo = {'evento': ['fecha_arte'], 'metodo': 'inventado'}

    with pytest.raises(ValueError):
        _calcular_extremo(datos, configuracion_extremo)


def test_calcular_etapa_aplica_regla_y_calcula_inicio_y_fin():
    datos_fuente = pd.DataFrame({
        'id_claw': [229, 229],
        'folio': ['A1', 'A2'],
        'fecha_arte': pd.to_datetime(['2026-01-02', '2026-01-01']),
        'fecha_preproyecto': pd.to_datetime([None, None]),
        'fecha_aprobacion_arte': pd.to_datetime([None, None]),
        'fecha_aprobacion_odt': pd.to_datetime([None, None]),
    })
    configuracion_etapa = {
        'evento': ['fecha_arte'], 'deduplicar_por': ['id_claw', 'folio'], 'reglas': ['folios_validos'],
        'inicio': {'metodo': 'primero'}, 'fin': {'metodo': 'ultimo'},
    }

    resultado_etapa, metadatos = calcular_etapa('artes', configuracion_etapa, datos_fuente)

    assert resultado_etapa['inicio'] == pd.Timestamp('2026-01-01')
    assert resultado_etapa['fin'] == pd.Timestamp('2026-01-02')
    assert resultado_etapa['numero_unidades_total'] == 2
    assert metadatos['folios_validos']['folios_validos'] == 2


def test_calcular_etapa_regla_desconocida_lanza_keyerror():
    datos_fuente = pd.DataFrame({'fecha_arte': pd.to_datetime(['2026-01-01'])})
    configuracion_etapa = {
        'evento': ['fecha_arte'], 'reglas': ['regla_inexistente'],
        'inicio': {'metodo': 'primero'}, 'fin': {'metodo': 'ultimo'},
    }

    with pytest.raises(KeyError):
        calcular_etapa('artes', configuracion_etapa, datos_fuente)


def test_construir_configuracion_etapas_sustituye_los_parametros_configurables():
    configuracion_etapas = _construir_configuracion_etapas(CONFIGURACION_DE_EJEMPLO)

    assert set(configuracion_etapas.keys()) == {
        'artes', 'preproyectos', 'aprobaciones', 'impresion', 'precampana', 'pick_pack', 'entregas',
    }
    assert configuracion_etapas['pick_pack']['inicio']['porcentaje_minimo'] == 0.05
    assert configuracion_etapas['pick_pack']['fin']['porcentaje'] == 0.99
    assert configuracion_etapas['entregas']['inicio']['porcentaje'] == 0.01
    assert configuracion_etapas['entregas']['fin']['dias_de_hueco'] == 10


def _fuentes_de_campana_de_ejemplo():
    retool_digital = pd.DataFrame({
        'id_claw': [229, 229],
        'folio': ['A1', 'A2'],
        'fecha_arte': pd.to_datetime(['2026-01-01', '2026-01-02']),
        'fecha_preproyecto': pd.to_datetime(['2026-01-02', '2026-01-03']),
        'fecha_aprobacion_arte': pd.to_datetime(['2026-01-03', '2026-01-05']),
        'fecha_aprobacion_odt': pd.to_datetime(['2026-01-04', '2026-01-04']),
        'inicio_produccion': pd.to_datetime(['2026-01-05 08:00', '2026-01-06 08:00']),
        'fin_produccion': pd.to_datetime(['2026-01-05 08:10', '2026-01-06 08:05']),
    })
    retool_precampana = pd.DataFrame({
        'id_claw': [229, 229],
        'hora_inicio': pd.to_datetime(['2026-01-01 08:00', '2026-01-02 10:00']),
        'hora_fin': pd.to_datetime(['2026-01-01 09:00', '2026-01-02 11:00']),
    })
    claw_picks = pd.DataFrame({
        'box_id': [1, 1, 1, 2, 2],
        'time': pd.to_datetime([
            '2026-01-10 08:00', '2026-01-10 08:10', '2026-01-10 08:20',
            '2026-01-10 09:00', '2026-01-10 09:15',
        ]),
    })
    claw_tracking = pd.DataFrame({
        'Fecha Entrega': [pd.Timestamp('2026-01-15'), pd.NaT, pd.NaT],
        'Fecha Última Actualización': [pd.NaT, pd.Timestamp('2026-01-16'), pd.NaT],
        'Estatus': ['Entregado', 'Entregado', 'En transito'],
    })
    return {
        'retool_digital': retool_digital, 'retool_precampana': retool_precampana,
        'claw_picks': claw_picks, 'claw_tracking': claw_tracking,
    }


def test_calcular_etapas_pasa_el_fin_de_pick_pack_a_impresion_para_descartar_reenvios():
    fuentes = _fuentes_de_campana_de_ejemplo()
    configuracion_etapas = _construir_configuracion_etapas(CONFIGURACION_DE_EJEMPLO)
    contexto_inicial = {'desfase_rescate_dias': CONFIGURACION_DE_EJEMPLO['desfase_rescate_dias']}

    resultados, metadatos = calcular_etapas(fuentes, configuracion_etapas, contexto_inicial)

    assert resultados['pick_pack']['fin'] == pd.Timestamp('2026-01-10 09:15')
    assert resultados['impresion']['numero_unidades_total'] == 2
    assert resultados['artes']['inicio'] == pd.Timestamp('2026-01-01')
    assert resultados['artes']['fin'] == pd.Timestamp('2026-01-02')


def test_calcular_kpis_ciclo_folio_calcula_medianas_de_respuesta_buho_y_fda():
    folios_digitales = pd.DataFrame({
        'id_claw': [229, 229],
        'folio': ['A1', 'A2'],
        'fecha_arte': pd.to_datetime(['2026-01-01', '2026-01-02']),
        'fecha_preproyecto': pd.to_datetime(['2026-01-02', '2026-01-03']),
        'fecha_aprobacion_arte': pd.to_datetime(['2026-01-03', '2026-01-05']),
        'fecha_aprobacion_odt': pd.to_datetime(['2026-01-04', '2026-01-04']),
    })

    kpis = calcular_kpis_ciclo_folio(folios_digitales)

    assert kpis['respuesta_buho_mediana_dias'] == pytest.approx(1.0)
    assert kpis['respuesta_fda_mediana_dias'] == pytest.approx(2.0)
    assert kpis['folios_invertidos'] == 0


def test_obtener_datos_retool_digital_filtra_por_id_claw_y_convierte_tipos(monkeypatch):
    llamadas_capturadas = []

    def read_sql_query_falso(consulta, motor, params):
        llamadas_capturadas.append({'consulta': str(consulta), 'params': params})
        return pd.DataFrame({
            'id_claw': ['229'], 'campana': ['FDA AGO26-2'], 'folio': ['A1'],
            'fecha_arte': ['2026-01-01 08:00:00'], 'fecha_preproyecto': [None],
            'fecha_aprobacion_arte': [None], 'fecha_aprobacion_odt': [None],
            'inicio_produccion': [None], 'fin_produccion': [None],
        })

    monkeypatch.setattr('src.services.snapshot_campana.pd.read_sql_query', read_sql_query_falso)

    resultado = obtener_datos_retool_digital(retool_engine=None, id_claw=229)

    assert llamadas_capturadas[0]['params'] == {'id_claw': 229}
    assert 'kam_preproyectos' in llamadas_capturadas[0]['consulta']
    assert resultado.iloc[0]['id_claw'] == 229
    assert resultado.iloc[0]['fecha_arte'] == pd.Timestamp('2026-01-01 08:00:00')


def test_obtener_datos_retool_digital_sin_folios_lanza_valueerror(monkeypatch):
    monkeypatch.setattr(
        'src.services.snapshot_campana.pd.read_sql_query',
        lambda consulta, motor, params: pd.DataFrame(),
    )

    with pytest.raises(ValueError):
        obtener_datos_retool_digital(retool_engine=None, id_claw=229)


def test_obtener_datos_retool_precampana_puede_venir_vacia_sin_error(monkeypatch):
    monkeypatch.setattr(
        'src.services.snapshot_campana.pd.read_sql_query',
        lambda consulta, motor, params: pd.DataFrame(columns=[
            'id_campana', 'id_claw', 'nombre_claw', 'nombre_nest',
            'id_actividad', 'actividad', 'hora_inicio', 'hora_fin',
        ]),
    )

    resultado = obtener_datos_retool_precampana(retool_engine=None, id_claw=229)

    assert resultado.empty


def _cliente_claw_de_prueba(handler):
    return httpx.Client(base_url='https://claw.example.com', transport=httpx.MockTransport(handler))


def test_obtener_datos_claw_acepta_lista_directa():
    def handler(request):
        assert request.url.path == '/distribution/tracking/229'
        return httpx.Response(200, json=[{'Fecha Entrega': '2026-01-15'}])

    resultado = obtener_datos_claw(_cliente_claw_de_prueba(handler), RUTA_CLAW_TRACKING, 229)

    assert len(resultado) == 1


def test_obtener_datos_claw_acepta_objeto_con_result():
    def handler(request):
        assert request.url.path == '/campaign/picks/229'
        return httpx.Response(200, json={'result': [{'box_id': 1, 'time': '2026-01-10 08:00:00'}]})

    resultado = obtener_datos_claw(_cliente_claw_de_prueba(handler), RUTA_CLAW_PICKS, 229)

    assert len(resultado) == 1
    assert resultado.iloc[0]['box_id'] == 1


def test_obtener_datos_claw_sin_registros_regresa_none():
    def handler(request):
        return httpx.Response(200, json={'result': []})

    resultado = obtener_datos_claw(_cliente_claw_de_prueba(handler), RUTA_CLAW_PICKS, 229)

    assert resultado is None


def test_calcular_snapshot_campana_produce_las_14_fechas_y_13_metadatos(monkeypatch):
    fuentes = _fuentes_de_campana_de_ejemplo()
    monkeypatch.setattr(
        snapshot_campana_module, 'obtener_datos_retool_digital',
        lambda retool_engine, id_claw: fuentes['retool_digital'],
    )
    monkeypatch.setattr(
        snapshot_campana_module, 'obtener_datos_retool_precampana',
        lambda retool_engine, id_claw: fuentes['retool_precampana'],
    )

    def claw_falso(claw_client, ruta_base, id_claw):
        if ruta_base == snapshot_campana_module.RUTA_CLAW_PICKS:
            return fuentes['claw_picks']
        return fuentes['claw_tracking']

    monkeypatch.setattr(snapshot_campana_module, 'obtener_datos_claw', claw_falso)

    snapshot = calcular_snapshot_campana(
        id_claw=229, configuracion=CONFIGURACION_DE_EJEMPLO, claw_client=None, retool_engine=None
    )

    # env2 se rescata con Fecha Última Actualización + desfase_rescate_dias (0.622 en
    # CONFIGURACION_DE_EJEMPLO) — se calcula aquí, no se hardcodea, para no depender de
    # redondeo de punto flotante en un timestamp con precisión de microsegundos.
    fecha_entrega_rescatada_de_env2 = pd.Timestamp('2026-01-16') + pd.Timedelta(
        days=CONFIGURACION_DE_EJEMPLO['desfase_rescate_dias']
    )

    # las 14 fechas
    assert snapshot['inicio_carga_artes'] == pd.Timestamp('2026-01-01')
    assert snapshot['fin_carga_artes'] == pd.Timestamp('2026-01-02')
    assert snapshot['inicio_carga_preproyectos'] == pd.Timestamp('2026-01-02')
    assert snapshot['fin_carga_preproyectos'] == pd.Timestamp('2026-01-03')
    assert snapshot['inicio_aprobaciones'] == pd.Timestamp('2026-01-03')
    assert snapshot['fin_aprobaciones'] == pd.Timestamp('2026-01-05')
    assert snapshot['inicio_impresion'] == pd.Timestamp('2026-01-05 08:00:00')
    assert snapshot['fin_impresion'] == pd.Timestamp('2026-01-06 08:05:00')
    assert snapshot['inicio_precampana'] == pd.Timestamp('2026-01-01 08:00:00')
    assert snapshot['fin_precampana'] == pd.Timestamp('2026-01-02 11:00:00')
    assert snapshot['inicio_pick_pack'] == pd.Timestamp('2026-01-10 08:00:00')
    assert snapshot['fin_pick_pack'] == pd.Timestamp('2026-01-10 09:15:00')
    assert snapshot['inicio_entregas'] == pd.Timestamp('2026-01-15')
    # fin_entregas: bloque_final con hueco=10 días — env1 (01-15) y env2 (rescatado, ~01-16)
    # caen en un solo bloque (gap < 10 días), así que el fin es el máximo de las dos.
    assert snapshot['fin_entregas'] == fecha_entrega_rescatada_de_env2

    # los 13 metadatos
    assert snapshot['porcentaje_alcanzado_entregas'] == pytest.approx(2 / 3)
    assert snapshot['ultima_entrega'] == fecha_entrega_rescatada_de_env2
    assert snapshot['numero_envios'] == 3
    assert snapshot['envios_con_fecha'] == 2
    assert snapshot['envios_sin_fecha'] == 0
    assert snapshot['envios_sin_registro_entrega'] == 1
    assert snapshot['numero_cajas_pick_pack'] == 2
    assert snapshot['numero_folios'] == 2
    assert snapshot['numero_odps'] == 2
    assert snapshot['numero_actividades'] == 2
    assert snapshot['respuesta_buho_dias'] == pytest.approx(1.0)
    assert snapshot['respuesta_fda_dias'] == pytest.approx(2.0)
    assert snapshot['folios_invertidos'] == 0


def test_calcular_snapshot_campana_sin_picks_de_claw_lanza_valueerror(monkeypatch):
    fuentes = _fuentes_de_campana_de_ejemplo()
    monkeypatch.setattr(
        snapshot_campana_module, 'obtener_datos_retool_digital',
        lambda retool_engine, id_claw: fuentes['retool_digital'],
    )
    monkeypatch.setattr(
        snapshot_campana_module, 'obtener_datos_retool_precampana',
        lambda retool_engine, id_claw: fuentes['retool_precampana'],
    )
    monkeypatch.setattr(snapshot_campana_module, 'obtener_datos_claw', lambda claw_client, ruta_base, id_claw: None)

    with pytest.raises(ValueError):
        calcular_snapshot_campana(id_claw=229, configuracion=CONFIGURACION_DE_EJEMPLO, claw_client=None, retool_engine=None)
