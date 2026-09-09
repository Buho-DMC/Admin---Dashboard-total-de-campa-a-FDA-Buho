"""Cálculo del snapshot de una campaña: 14 fechas y 13 metadatos por etapa.

Método conocido como "Política D" en la auditoría original — ver
AUDITORIA_ETL.txt §8-19 (repo "[Direccion] Reporte proceso total de campaña")
para la justificación de negocio completa detrás de cada regla y parámetro.
Este módulo es un port fiel de etl.ipynb, adaptado de "todas las campañas en
un lote" a "una campaña por llamada".
"""

import math

import pandas as pd


def punto_de_avance(eventos: pd.Series, porcentaje: float, numero_denominador: int | None = None) -> pd.Timestamp:
    """Fecha en que se alcanzó `porcentaje` de las unidades con fecha.

    Responde preguntas como "¿cuándo se entregó el 90% de los envíos?" sin
    interpolar entre dos fechas: el hito de un porcentaje siempre es un
    evento real que de verdad ocurrió, nunca un promedio inventado entre el
    envío 89 y el 90.

    Args:
        eventos: fechas, una por unidad con registro.
        porcentaje: 0-1.
        numero_denominador: por defecto, el número de unidades con fecha (el
            método vigente). Parámetro abierto solo para diagnóstico.

    Returns:
        La fecha del evento que alcanza `porcentaje`, o `pd.NaT` si no hay
        eventos o si `porcentaje` nunca se alcanza. Usa `math.ceil(porcentaje
        * n)` como posición — el punto en que se alcanza el X% es un evento
        real, no un valor interpolado entre dos.
    """
    eventos_ordenados = pd.Series(eventos).dropna().sort_values()
    if eventos_ordenados.empty:
        return pd.NaT
    numero_unidades = len(eventos_ordenados) if numero_denominador is None else numero_denominador
    if numero_unidades <= 0:
        return pd.NaT
    posicion = math.ceil(porcentaje * numero_unidades)
    if posicion <= 0 or posicion > len(eventos_ordenados):
        return pd.NaT
    return eventos_ordenados.iloc[posicion - 1]


def bloques_de_actividad(fechas: pd.Series, dias_de_hueco: int) -> tuple[pd.Series, pd.DataFrame]:
    """Agrupa eventos en bloques separados por huecos sin actividad.

    Sirve para distinguir una racha real de trabajo de un evento aislado. Por
    ejemplo, en Carga de Artes alguien puede subir un arte de prueba el día 1
    y no volver a tocar la campaña hasta el día 10, cuando empieza la carga
    real de 40 artes: sin esta función, el rango completo (día 1 al último
    arte) infla la duración de la etapa con 9 días de hueco que no fueron
    trabajo. Esta función detecta ese hueco y separa los eventos en bloques
    (racha 1: 1 evento del día 1; racha 2: 40 eventos desde el día 10), para
    que otras funciones (como `inicio_por_bloque`) decidan cuál racha es la
    real.

    Args:
        fechas: eventos crudos, con o sin duplicados.
        dias_de_hueco: días sin actividad que separan un bloque del siguiente.

    Returns:
        (identificador_de_bloque: el bloque de cada evento,
         resumen_de_bloques: DataFrame con columnas inicio, fin, n y peso —
         una fila por bloque).
    """
    eventos_ordenados = pd.Series(fechas).dropna().sort_values()
    if eventos_ordenados.empty:
        return pd.Series(dtype='int64'), pd.DataFrame(columns=['inicio', 'fin', 'n', 'peso'])

    dia_de_cada_evento = eventos_ordenados.dt.normalize()
    dias_con_actividad = pd.Series(sorted(set(dia_de_cada_evento)))
    identificador_de_bloque_por_dia = (dias_con_actividad.diff().dt.days >= dias_de_hueco).cumsum()
    identificador_de_bloque = dia_de_cada_evento.map(dict(zip(dias_con_actividad, identificador_de_bloque_por_dia)))

    resumen_de_bloques = (
        pd.DataFrame({'bloque': identificador_de_bloque.values, 'fecha': eventos_ordenados.values})
        .groupby('bloque')['fecha']
        .agg(inicio='min', fin='max', n='size')
    )
    resumen_de_bloques['peso'] = resumen_de_bloques['n'] / len(eventos_ordenados)
    return identificador_de_bloque, resumen_de_bloques


def inicio_por_bloque(fechas: pd.Series, porcentaje_minimo: float, dias_de_hueco: int) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Primer evento del primer bloque que pesa >= `porcentaje_minimo` del volumen total.

    Es el método que usa el cálculo de una etapa para fijar su fecha de
    INICIO cuando la actividad no es continua. Usa `bloques_de_actividad`
    para separar rachas y descarta las que son demasiado chicas para contar
    como el arranque real (por ejemplo, un solo arte de prueba subido días
    antes de que el equipo empiece a trabajar la campaña de verdad). Solo se
    aplica al INICIO: al final de una etapa, un bloque chico sí es real (la
    cola de cierre, gente terminando lo último), así que ahí no se descarta
    nada.

    Args:
        fechas: eventos crudos.
        porcentaje_minimo: peso mínimo, 0-1, para que un bloque cuente.
        dias_de_hueco: días sin actividad que separan un bloque del siguiente.

    Returns:
        (Timestamp de inicio, DataFrame de bloques con la columna 'cuenta').
        Si ningún bloque alcanza `porcentaje_minimo`, regresa la fecha más
        temprana de todos los eventos.
    """
    _, resumen_de_bloques = bloques_de_actividad(fechas, dias_de_hueco)
    if resumen_de_bloques.empty:
        return pd.NaT, resumen_de_bloques

    resumen_de_bloques = resumen_de_bloques.copy()
    resumen_de_bloques['cuenta'] = resumen_de_bloques['peso'] >= porcentaje_minimo
    bloques_validos = resumen_de_bloques[resumen_de_bloques['cuenta']]
    if bloques_validos.empty:
        return pd.Series(fechas).dropna().min(), resumen_de_bloques
    return bloques_validos['inicio'].iloc[0], resumen_de_bloques


COLUMNAS_DIGITALES = ['fecha_arte', 'fecha_preproyecto', 'fecha_aprobacion_arte', 'fecha_aprobacion_odt']


def regla_folios_validos(folios: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Descarta el folio '0' y los folios sin ninguna fecha digital.

    Claw usa el folio '0' como marcador de "sin folio asignado" — no es una
    campaña real y contaminaría cualquier fecha de inicio/fin si se cuenta.
    Un folio sin ninguna fecha digital tampoco aporta nada: es un registro
    vacío que solo existe en la base, no un evento que haya ocurrido.

    Args:
        folios: filas con al menos las columnas 'folio' y `COLUMNAS_DIGITALES`.

    Returns:
        (folios válidos, metadatos con folios_entrada, folios_folio_cero,
        folios_sin_fecha, folios_descartados, folios_validos).
    """
    es_folio_cero = folios['folio'].astype(str) == '0'
    sin_ninguna_fecha = folios[COLUMNAS_DIGITALES].isna().all(axis=1)
    filas_invalidas = es_folio_cero | sin_ninguna_fecha
    metadatos = {
        'folios_entrada': int(len(folios)),
        'folios_folio_cero': int(es_folio_cero.sum()),
        'folios_sin_fecha': int(sin_ninguna_fecha.sum()),
        'folios_descartados': int(filas_invalidas.sum()),
        'folios_validos': int((~filas_invalidas).sum()),
    }
    return folios[~filas_invalidas].copy(), metadatos


MINUTOS_MINIMOS_ODP = 1  # bajo este umbral, una ODP es un cierre administrativo


def regla_odps_validas(odps: pd.DataFrame, contexto: dict) -> tuple[pd.DataFrame, dict]:
    """Descarta ODPs instantáneas (< `MINUTOS_MINIMOS_ODP`) y reenvíos.

    Una ODP (orden de producción) que dura segundos no fue trabajo de
    impresión real — es un cierre administrativo en el sistema (alguien
    marca la orden como terminada sin haber impreso nada). Un reenvío es una
    ODP que arranca después de que ya se hizo Pick & Pack: es una reimpresión
    de algo dañado o perdido en el empaque, no parte del ciclo original de
    producción, y contarla movería la fecha de fin de Impresión más allá de
    lo que en realidad tardó la campaña.

    Args:
        odps: filas con 'inicio_produccion' y 'fin_produccion'.
        contexto: debe traer 'fin_pick_pack' (Timestamp o NaT) — Pick & Pack
            se calcula ANTES que Impresión (ver ORDEN_ETAPAS).

    Returns:
        (odps válidas, metadatos con los conteos de cada motivo de descarte).

    Raises:
        ValueError: si 'fin_pick_pack' no está en `contexto` — bug de orden
            de ejecución, nunca debería pasar en producción.
    """
    if 'fin_pick_pack' not in contexto:
        raise ValueError(
            'regla_odps_validas necesita el Fin de Pick & Pack ya calculado. '
            'Pick & Pack debe ejecutarse antes que Impresión (ver ORDEN_ETAPAS).'
        )
    fin_pick_pack = contexto['fin_pick_pack']

    sin_inicio = odps['inicio_produccion'].isna()
    sin_fin = odps['fin_produccion'].isna()
    odps_con_fechas = odps[~(sin_inicio | sin_fin)].copy()

    duracion_minutos = (odps_con_fechas['fin_produccion'] - odps_con_fechas['inicio_produccion']).dt.total_seconds() / 60
    es_instantanea = duracion_minutos < MINUTOS_MINIMOS_ODP

    sin_referencia_pick_pack = pd.isna(fin_pick_pack)
    if sin_referencia_pick_pack:
        es_reenvio = pd.Series(False, index=odps_con_fechas.index)
        numero_sin_referencia_pick_pack = len(odps_con_fechas)
    else:
        es_reenvio = odps_con_fechas['inicio_produccion'] > fin_pick_pack
        numero_sin_referencia_pick_pack = 0

    filas_invalidas = es_instantanea | es_reenvio
    metadatos = {
        'odps_entrada': int(len(odps)),
        'odps_sin_ninguna_fecha': int((sin_inicio & sin_fin).sum()),
        'odps_media_abierta': int((sin_inicio ^ sin_fin).sum()),
        'odps_con_fechas': int(len(odps_con_fechas)),
        'odps_instantaneas': int(es_instantanea.sum()),
        'odps_reenvio': int(es_reenvio.sum()),
        'odps_sin_referencia_pick_pack': numero_sin_referencia_pick_pack,
        'odps_validas': int((~filas_invalidas).sum()),
    }
    return odps_con_fechas[~filas_invalidas].copy(), metadatos


def regla_precampana_dia_sin_operacion(registros: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Marca abiertos los registros que abarcan un día en que nadie abrió
    ninguna actividad de esta campaña — la planta no estaba trabajando ese día.

    Un registro de precampaña puede quedar abierto por error (alguien olvidó
    cerrarlo) y arrastrar su `hora_fin` varios días, aunque la planta no
    trabajó en la campaña esos días intermedios. Si se usara esa `hora_fin`
    tal cual, la etapa de precampaña se vería durando días de inactividad
    real. Esta regla no borra la fila: conserva `hora_inicio` (alguien sí
    estuvo ahí y la abrió) y anula `hora_fin` en una columna nueva
    `hora_fin_valida`. Sin parámetros calibrados — el día de operación sale
    de los propios datos (AUDITORIA_ETL.txt §17.1-17.2).

    Args:
        registros: filas con 'hora_inicio' y 'hora_fin'.

    Returns:
        (registros con columnas 'abierto' y 'hora_fin_valida', metadatos con
        registros_entrada, registros, registros_abiertos).
    """
    registros_con_inicio = registros.dropna(subset=['hora_inicio']).copy()
    registros_con_inicio['abierto'] = False

    dias_con_operacion = set(registros_con_inicio['hora_inicio'].dt.normalize())
    for indice_fila, fila in registros_con_inicio.iterrows():
        if pd.isna(fila['hora_fin']):
            continue
        dias_que_abarca_el_registro = pd.date_range(
            fila['hora_inicio'].normalize(), fila['hora_fin'].normalize(), freq='D'
        )
        if any(dia not in dias_con_operacion for dia in dias_que_abarca_el_registro):
            registros_con_inicio.loc[indice_fila, 'abierto'] = True

    registros_con_inicio['hora_fin_valida'] = registros_con_inicio['hora_fin'].where(~registros_con_inicio['abierto'])

    metadatos = {
        'registros_entrada': int(len(registros)),
        'registros': int(len(registros_con_inicio)),
        'registros_abiertos': int(registros_con_inicio['abierto'].sum()),
    }
    return registros_con_inicio, metadatos


def regla_rescate_entregas(envios: pd.DataFrame, contexto: dict) -> tuple[pd.DataFrame, dict]:
    """Rellena Fecha Entrega con la última actualización + `desfase_rescate_dias`
    cuando falta y el estatus es 'Entregado'.

    La paquetería a veces marca un envío como 'Entregado' en su sistema de
    tracking sin nunca poblar la fecha exacta de entrega — el dato existe en
    el negocio (el paquete sí llegó) pero no en la columna que se necesita
    para calcular la etapa de Entregas. Esta regla "rescata" esos envíos
    usando su última actualización de tracking como aproximación, en vez de
    perderlos del cálculo o tratarlos como si nunca hubieran llegado. No
    borra filas: todas se conservan, con `fecha_final` poblada donde se pudo.
    Las columnas de "última actualización" y "estatus" se detectan por
    substring (`'ltima'`, `'statu'`), no por nombre exacto — Claw no
    garantiza el nombre exacto de esas dos columnas.

    Args:
        envios: filas con al menos 'Fecha Entrega' y las dos columnas
            detectadas por substring.
        contexto: debe traer 'desfase_rescate_dias' (parámetro configurable).

    Returns:
        (envios con columna 'fecha_final', metadatos con universo,
        con_fecha_original, rescatados, sin_fecha_entregado,
        sin_registro_entrega, y los nombres de columna detectados).

    Raises:
        ValueError: si no se encuentran las dos columnas por substring.
    """
    envios_con_fecha_final = envios.copy()
    columna_ultima_actualizacion = next(
        (columna for columna in envios_con_fecha_final.columns if 'ltima' in columna.lower()), None
    )
    columna_estatus = next(
        (columna for columna in envios_con_fecha_final.columns if 'statu' in columna.lower()), None
    )
    if columna_ultima_actualizacion is None or columna_estatus is None:
        raise ValueError(
            'No se encontraron las columnas de tracking (última actualización / estatus). '
            f'Columnas disponibles: {list(envios_con_fecha_final.columns)}'
        )

    fecha_ultima_actualizacion = pd.to_datetime(envios_con_fecha_final[columna_ultima_actualizacion], errors='coerce')
    fecha_entrega = pd.to_datetime(envios_con_fecha_final['Fecha Entrega'], errors='coerce')
    es_rescatable = (
        fecha_entrega.isna()
        & fecha_ultima_actualizacion.notna()
        & (envios_con_fecha_final[columna_estatus].astype(str) == 'Entregado')
    )

    envios_con_fecha_final['fecha_final'] = fecha_entrega
    envios_con_fecha_final.loc[es_rescatable, 'fecha_final'] = (
        fecha_ultima_actualizacion[es_rescatable] + pd.Timedelta(days=contexto['desfase_rescate_dias'])
    )

    es_entregado = envios_con_fecha_final[columna_estatus].astype(str) == 'Entregado'
    sin_fecha_final = envios_con_fecha_final['fecha_final'].isna()
    sin_fecha_entregado = sin_fecha_final & es_entregado
    sin_registro_de_entrega = ~es_entregado

    metadatos = {
        'columna_ultima_actualizacion': columna_ultima_actualizacion,
        'columna_estatus': columna_estatus,
        'universo': int(len(envios_con_fecha_final)),
        'con_fecha_original': int(fecha_entrega.notna().sum()),
        'rescatados': int(es_rescatable.sum()),
        'sin_fecha_entregado': int(sin_fecha_entregado.sum()),
        'sin_registro_entrega': int(sin_registro_de_entrega.sum()),
    }
    return envios_con_fecha_final, metadatos


def regla_ciclo_folio_valido(folios: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Descarta folios con algún tramo negativo, para los KPIs de ciclo.

    Los KPIs de ciclo miden cuánto tarda Buho y cuánto tarda FDA en responder
    dentro del flujo de un folio. Un tramo negativo (por ejemplo, la
    aprobación registrada antes que el arte) es un error de captura en
    Claw, no un ciclo real — incluirlo metería una duración negativa que
    distorsionaría la mediana de todo el KPI. La aprobación de un folio es
    la MÁS TARDÍA de arte y ODT.

    Args:
        folios: filas con 'fecha_arte', 'fecha_preproyecto',
            'fecha_aprobacion_arte', 'fecha_aprobacion_odt'.

    Returns:
        (folios con ciclo válido, metadatos con folios_entrada,
        folios_invertidos, folios_validos).
    """
    aprobacion_mas_tardia = folios[['fecha_aprobacion_arte', 'fecha_aprobacion_odt']].max(axis=1)
    duracion_buho_segundos = (folios['fecha_preproyecto'] - folios['fecha_arte']).dt.total_seconds()
    duracion_fda_segundos = (aprobacion_mas_tardia - folios['fecha_preproyecto']).dt.total_seconds()
    folios_invertidos = (duracion_buho_segundos < 0) | (duracion_fda_segundos < 0)

    metadatos = {
        'folios_entrada': int(len(folios)),
        'folios_invertidos': int(folios_invertidos.sum()),
        'folios_validos': int((~folios_invertidos).sum()),
    }
    return folios[~folios_invertidos].copy(), metadatos


REGLAS_DISPONIBLES = {
    'folios_validos':                lambda datos, contexto: regla_folios_validos(datos),
    'odps_validas':                  lambda datos, contexto: regla_odps_validas(datos, contexto),
    'precampana_dia_sin_operacion':  lambda datos, contexto: regla_precampana_dia_sin_operacion(datos),
    'rescate_entregas':              lambda datos, contexto: regla_rescate_entregas(datos, contexto),
}
