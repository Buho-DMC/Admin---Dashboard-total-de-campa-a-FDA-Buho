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


def construir_grafica_de_linea_de_tiempo(snapshot: dict) -> go.Figure | None:
    """Construye una gráfica de línea de tiempo con las etapas de la campaña.

    Mapea las 7 etapas del snapshot recibidas en el diccionario. Si alguna etapa
    no tiene fecha de inicio y de fin, se omite de la gráfica. Si no hay ninguna
    etapa válida, retorna None.

    Args:
        snapshot: Diccionario con la información del snapshot de la campaña.

    Returns:
        Figura de Plotly de tipo línea de tiempo (Gantt) o None si no hay etapas completas.
    """
    etapas = [
        ('Carga de artes', 'inicio_carga_artes', 'fin_carga_artes'),
        ('Carga de preproyectos', 'inicio_carga_preproyectos', 'fin_carga_preproyectos'),
        ('Aprobaciones', 'inicio_aprobaciones', 'fin_aprobaciones'),
        ('Impresión', 'inicio_impresion', 'fin_impresion'),
        ('Precampaña', 'inicio_precampana', 'fin_precampana'),
        ('Pick & Pack', 'inicio_pick_pack', 'fin_pick_pack'),
        ('Entregas', 'inicio_entregas', 'fin_entregas'),
    ]

    nombres_etapas = []
    inicios = []
    fines = []

    for nombre_etapa, clave_inicio, clave_fin in etapas:
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

    if not nombres_etapas:
        return None
    datos = {
        'Etapa': nombres_etapas,
        'Inicio': inicios,
        'Fin': fines,
    }

    figura = px.timeline(datos, x_start='Inicio', x_end='Fin', y='Etapa')
    figura.update_yaxes(autorange='reversed')  # Para que la primera etapa aparezca arriba
    return figura
