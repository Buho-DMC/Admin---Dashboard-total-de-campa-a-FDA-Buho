"""Gráficas ilustrativas de la página de Metodología."""

import statistics

import plotly.graph_objects as go

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
