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

    Solo se usa para el INICIO de una etapa: al final, un bloque chico es la
    cola de cierre (trabajo real), no ruido — no se aplica ahí.

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
