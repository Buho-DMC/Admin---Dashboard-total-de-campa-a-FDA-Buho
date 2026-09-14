"""Gráficas ilustrativas de la página de Metodología."""

import statistics
from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px

_DISTRIBUCION_NORMAL_ESTANDAR = statistics.NormalDist(mu=0, sigma=1)
_LIMITE_INFERIOR_EJE_X = -4
_LIMITE_SUPERIOR_EJE_X = 4
_NUMERO_DE_PUNTOS = 400


def construir_grafica_de_percentil(valor_percentil: float, titulo: str) -> go.Figure:
    """Construye una curva normal ilustrativa con el área bajo un corte de percentil sombreada.

    No usa datos reales de campañas — es un ejemplo genérico (distribución normal
    estándar) para que, al mover el valor de un parámetro como `porcentaje_fin`,
    el usuario vea de inmediato qué proporción de una distribución queda a la
    izquierda de ese corte, sin tener que entender la fórmula del cálculo real.

    Args:
        valor_percentil: proporción entre 0 y 1 (ej. 0.99 para `porcentaje_fin`).
        titulo: título de la gráfica, ej. `'Porcentaje fin (0.99)'`.

    Returns:
        Figura de plotly con la curva y el área sombreada hasta el corte.

    Raises:
        ValueError: si `valor_percentil` no está estrictamente entre 0 y 1.
    """
    if not 0 < valor_percentil < 1:
        raise ValueError(f'valor_percentil debe estar entre 0 y 1, se recibió {valor_percentil}')

    paso = (_LIMITE_SUPERIOR_EJE_X - _LIMITE_INFERIOR_EJE_X) / (_NUMERO_DE_PUNTOS - 1)
    valores_x = [_LIMITE_INFERIOR_EJE_X + indice_de_punto * paso for indice_de_punto in range(_NUMERO_DE_PUNTOS)]
    valores_y = [_DISTRIBUCION_NORMAL_ESTANDAR.pdf(valor_x) for valor_x in valores_x]
    corte_z = _DISTRIBUCION_NORMAL_ESTANDAR.inv_cdf(valor_percentil)

    valores_x_sombreados = [valor_x for valor_x in valores_x if valor_x <= corte_z]
    valores_y_sombreados = [_DISTRIBUCION_NORMAL_ESTANDAR.pdf(valor_x) for valor_x in valores_x_sombreados]

    figura = go.Figure()
    figura.add_trace(go.Scatter(x=valores_x, y=valores_y, mode='lines', name='Distribución ilustrativa'))
    figura.add_trace(
        go.Scatter(
            x=valores_x_sombreados,
            y=valores_y_sombreados,
            fill='tozeroy',
            mode='none',
            name=f'{valor_percentil:.0%} de los datos',
        )
    )
    figura.update_layout(title=titulo, showlegend=True, xaxis_title='Valor ilustrativo', yaxis_title='Densidad')
    return figura


ETAPAS = [
    ('Carga de artes', 'inicio_carga_artes', 'fin_carga_artes'),
    ('Carga de preproyectos', 'inicio_carga_preproyectos', 'fin_carga_preproyectos'),
    ('Aprobaciones', 'inicio_aprobaciones', 'fin_aprobaciones'),
    ('Impresión', 'inicio_impresion', 'fin_impresion'),
    ('Precampaña', 'inicio_precampana', 'fin_precampana'),
    ('Pick & Pack', 'inicio_pick_pack', 'fin_pick_pack'),
    ('Entregas', 'inicio_entregas', 'fin_entregas'),
]


_SIMBOLOS_POR_CODIGO_DE_HITO = {
    'entrega_promociones_ac': 'diamond',
    'entrega_concentrado_folleto': 'square',
    'entrega_diagramacion_mkt': 'circle',
    'cierre_comercializacion_espacios': 'x',
    'entrega_diagramacion_comercializacion': 'triangle-up',
    'liberacion_pop': 'star',
    'liberacion_folleto': 'triangle-down',
}


def construir_grafica_por_actividad(snapshot: dict, eventos_de_campana: list[dict]) -> go.Figure | None:
    """Construye una línea de tiempo con las 7 etapas de la campaña y marcadores de hitos FDA.

    Args:
        snapshot: Diccionario con la información del snapshot de la campaña.
        eventos_de_campana: Hitos FDA de la campaña (`api_client.list_eventos_de_campana`), cada
            uno con `codigo`, `nombre` y `fecha` (`None` si aún no se ha capturado).

    Returns:
        Figura de Plotly con las etapas como barras y los hitos FDA como marcadores, o None si no
        hay ni etapas completas ni hitos con fecha.
    """
    nombres_etapas = []
    inicios = []
    fines = []

    for nombre_etapa, clave_inicio, clave_fin in ETAPAS:
        inicio_iso = snapshot.get(clave_inicio)
        fin_iso = snapshot.get(clave_fin)

        if inicio_iso and fin_iso:
            try:
                dt_inicio = datetime.fromisoformat(inicio_iso)
                dt_fin = datetime.fromisoformat(fin_iso)
            except (ValueError, TypeError):
                continue

            inicios.append(dt_inicio)
            fines.append(dt_fin)
            nombres_etapas.append(nombre_etapa)

    hitos_con_fecha = [evento for evento in eventos_de_campana if evento.get('fecha')]

    if not nombres_etapas and not hitos_con_fecha:
        return None

    if nombres_etapas:
        datos = {'Etapa': nombres_etapas, 'Inicio': inicios, 'Fin': fines}
        figura = px.timeline(datos, x_start='Inicio', x_end='Fin', y='Etapa')
    else:
        figura = go.Figure()

    for evento in hitos_con_fecha:
        try:
            fecha_del_hito = datetime.fromisoformat(evento['fecha'])
        except (ValueError, TypeError):
            continue
        figura.add_trace(go.Scatter(
            x=[fecha_del_hito],
            y=[evento['nombre']],
            mode='markers',
            marker=dict(size=10, symbol=_SIMBOLOS_POR_CODIGO_DE_HITO.get(evento['codigo'], 'circle')),
            name=evento['nombre'],
        ))

    orden_del_eje = [evento['nombre'] for evento in hitos_con_fecha] + nombres_etapas
    figura.update_yaxes(categoryorder='array', categoryarray=orden_del_eje, autorange='reversed')
    return figura


_COLORES_POR_RESPONSABLE = {
    'FDA — Carga de artes y aprobaciones': '#fb7185',
    'Tiempo muerto': '#9ca3af',
    'Búho — Carga de preproyectos': '#38bdf8',
    'Búho — Ejecución': '#1e3a8a',
    'Entregas': '#22c55e',
}


def construir_grafica_por_responsable(snapshot: dict) -> go.Figure | None:
    """Construye la línea de tiempo agrupada por responsable (FDA / Búho / Entregas).

    Adaptación de `plot_timeline` del proyecto legacy: ese usaba hitos FDA granulares
    que no existen en `SnapshotOut`, así que el bloque FDA aquí solo cubre
    Carga de artes + Aprobaciones — sin el segmento "Planeación FDA" previo.

    Args:
        snapshot: Diccionario con la información del snapshot de la campaña.

    Returns:
        Figura de Plotly, o None si no hay ningún bloque con fechas completas.
    """
    def _fecha(clave: str) -> datetime | None:
        valor = snapshot.get(clave)
        if not valor:
            return None
        try:
            return datetime.fromisoformat(valor)
        except (ValueError, TypeError):
            return None

    inicio_artes = _fecha('inicio_carga_artes')
    fin_aprob = _fecha('fin_aprobaciones')
    carga_pre_inicio = _fecha('inicio_carga_preproyectos')
    carga_pre_fin = _fecha('fin_carga_preproyectos')

    inicio_ejecucion_buho = None
    for clave in ('inicio_impresion', 'inicio_precampana', 'inicio_pick_pack'):
        inicio_ejecucion_buho = _fecha(clave)
        if inicio_ejecucion_buho is not None:
            break
    fin_ejecucion_buho = _fecha('fin_pick_pack')

    ent_inicio = _fecha('inicio_entregas')
    ent_fin = _fecha('fin_entregas')

    grupos, inicios, fines, lineas = [], [], [], []

    def _agregar(grupo: str, inicio: datetime | None, fin: datetime | None, linea: str) -> None:
        if inicio is not None and fin is not None:
            grupos.append(grupo)
            inicios.append(inicio)
            fines.append(fin)
            lineas.append(linea)

    _agregar('FDA — Carga de artes y aprobaciones', inicio_artes, fin_aprob, 'FDA')
    _agregar('Búho — Carga de preproyectos', carga_pre_inicio, carga_pre_fin, 'Búho')
    if fin_aprob is not None and inicio_ejecucion_buho is not None and inicio_ejecucion_buho > fin_aprob:
        _agregar('Tiempo muerto', fin_aprob, inicio_ejecucion_buho, 'Búho')
    _agregar('Búho — Ejecución', inicio_ejecucion_buho, fin_ejecucion_buho, 'Búho')
    _agregar('Entregas', ent_inicio, ent_fin, 'Entregas')

    if not grupos:
        return None

    datos = {'Grupo': grupos, 'Inicio': inicios, 'Fin': fines, 'Linea': lineas}
    figura = px.timeline(
        datos, x_start='Inicio', x_end='Fin', y='Linea', color='Grupo',
        color_discrete_map=_COLORES_POR_RESPONSABLE,
    )
    figura.update_yaxes(categoryorder='array', categoryarray=['FDA', 'Búho', 'Entregas'], autorange='reversed')
    return figura


def construir_grafica_de_percentiles_combinada(valores_percentil: dict[str, float]) -> go.Figure:
    """Curva normal única con varios cortes de percentil marcados como líneas verticales.

    Reemplaza tener una gráfica separada por cada corte (inicio/fin/cobertura de
    aviso) — todos se marcan sobre la misma distribución ilustrativa, para
    verlos relativos entre sí de un vistazo.

    Args:
        valores_percentil: dict `{etiqueta: valor_percentil}`, uno por corte a
            marcar — por ejemplo `{'Porcentaje inicio': 0.01, 'Porcentaje fin': 0.99}`.
            Cada valor debe estar estrictamente entre 0 y 1.

    Returns:
        Figura de Plotly con la curva normal estándar y una línea vertical
        punteada por cada corte, etiquetada con su nombre y porcentaje.
    """
    paso = (_LIMITE_SUPERIOR_EJE_X - _LIMITE_INFERIOR_EJE_X) / (_NUMERO_DE_PUNTOS - 1)
    valores_x = [_LIMITE_INFERIOR_EJE_X + indice_de_punto * paso for indice_de_punto in range(_NUMERO_DE_PUNTOS)]
    valores_y = [_DISTRIBUCION_NORMAL_ESTANDAR.pdf(valor_x) for valor_x in valores_x]

    figura = go.Figure()
    figura.add_trace(go.Scatter(x=valores_x, y=valores_y, mode='lines', name='Distribución ilustrativa'))

    for etiqueta, valor_percentil in valores_percentil.items():
        corte_z = _DISTRIBUCION_NORMAL_ESTANDAR.inv_cdf(valor_percentil)
        figura.add_vline(x=corte_z, line_dash='dash', annotation_text=f'{etiqueta} ({valor_percentil:.0%})')

    figura.update_layout(title='Cortes de percentil', showlegend=True, xaxis_title='Valor ilustrativo', yaxis_title='Densidad')
    return figura
