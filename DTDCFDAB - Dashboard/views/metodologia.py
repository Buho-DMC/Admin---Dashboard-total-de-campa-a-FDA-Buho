"""Metodología: explica el cálculo, permite ajustar parámetros y recalcular."""

import streamlit as st

import api_client
import charts

st.title('Metodología')

st.markdown(
    'Estos parámetros controlan cómo se calcula el snapshot de cada campaña a partir de '
    'las fechas de entrega. Ajusta los valores y usa la gráfica de abajo para ver dónde '
    'cae cada corte de percentil antes de guardar un cambio.'
)

try:
    configuracion_vigente = api_client.get_configuracion_vigente()
    historial_configuracion = api_client.list_historial_configuracion()
except Exception as error:
    st.error('No se pudo obtener la configuración de la Metodología.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

with st.expander('Historial de combinaciones ya usadas'):
    st.dataframe(historial_configuracion, hide_index=True)

CORTES_DE_PERCENTIL = [
    {
        'clave': 'porcentaje_inicio',
        'etiqueta': 'Porcentaje inicio',
        'leyenda': (
            'Define desde qué punto se considera que Entregas arrancó de verdad, '
            'ignorando registros sueltos y prematuros.'
        ),
        'justificacion': (
            'Es el percentil sobre las unidades ya capturadas, no sobre el universo completo. '
            'En la campaña 134 había un solo registro suelto de más de un año antes del arranque '
            'real; con el corte al 1%, ese registro queda fuera sin necesidad de una regla aparte '
            '(el envío número ~20 de 1,956 ya marca el arranque real).'
        ),
        'actividades': ['Entregas — fija su fecha de inicio.'],
        'min_value': 0.01, 'max_value': 0.5, 'step': 0.01,
    },
    {
        'clave': 'porcentaje_fin',
        'etiqueta': 'Porcentaje fin',
        'leyenda': (
            'Define cuándo Pick & Pack se considera terminado. **Ya no aplica a Entregas** — '
            'Entregas usa "Hueco de entregas" en su lugar. También toca **Impresión de forma '
            'indirecta**: su fecha de fin de Pick & Pack se usa para descartar reenvíos de '
            'Impresión posteriores al corte (`regla_odps_validas`).'
        ),
        'justificacion': (
            'El costo de seguir esperando es plano hasta el 98-99% del universo y se dispara '
            'después: subir de 95% a 98% cuesta 1 día de mediana, y de 98% a 99% cuesta 1.13 '
            'días — no hay un salto real que marque un corte "natural", así que el valor es una '
            'decisión de negocio, confirmada con la medición de las 19 campañas.'
        ),
        'actividades': ['Pick & Pack — fija su fecha de fin.'],
        'min_value': 0.5, 'max_value': 0.99, 'step': 0.01,
    },
    {
        'clave': 'cobertura_aviso',
        'etiqueta': 'Cobertura de aviso',
        'leyenda': (
            'Umbral de datos capturados por debajo del cual el sistema avisa que una campaña '
            'tiene información incompleta. No cambia ningún cálculo, es un semáforo.'
        ),
        'justificacion': (
            'Desde que el denominador de los cortes de percentil pasó a ser lo capturado (y no '
            'el universo completo), una campaña con captura incompleta se mide sobre menos '
            'unidades y se ve algo más rápida. Eso no se esconde: junto a cada fecha se publican '
            'siempre el universo, cuántas unidades tienen dato, y se avisa cuando la cobertura '
            'cae por debajo de este umbral.'
        ),
        'actividades': ['No afecta ningún cálculo del ETL — solo funciona como aviso/semáforo en el Dashboard.'],
        'min_value': 0.5, 'max_value': 0.99, 'step': 0.01,
    },
]

OTROS_PARAMETROS = [
    {
        'clave': 'porcentaje_bloque_minimo',
        'etiqueta': 'Porcentaje bloque mínimo',
        'leyenda': (
            'Filtra escaneos sueltos de pre-surtido para que no se confundan con el arranque '
            'real de Pick & Pack.'
        ),
        'justificacion': (
            'Es el peso mínimo, como % del total de escaneos, que debe tener el primer bloque de '
            'actividad para contar como arranque. Se probó con 5%, 10%, 20% y 30% y el arranque '
            'resultante no cambió en ninguna de las 16 campañas comparadas — se eligió el valor '
            'más conservador (5%) porque no corta trabajo real.'
        ),
        'actividades': ['Pick & Pack — fija su fecha de inicio.'],
        'tipo_control': 'slider', 'min_value': 0.0, 'max_value': 1.0,
    },
    {
        'clave': 'hueco_entregas_dias',
        'etiqueta': 'Hueco de entregas (días)',
        'leyenda': 'Días sin entregas que separan el cierre real de un rezagado aislado. Define el fin de Entregas.',
        'justificacion': (
            'Se comparó contra la hoja capturada a mano en 15 campañas, barriendo el hueco de 3 '
            'a 30 días: entre 9 y 30 días el resultado es idéntico, así que se eligió 10 por ser '
            'el extremo más ajustado del tramo estable. Un caso real que lo justifica: una '
            'campaña de enero con un solo envío aislado en agosto — sin este corte, el "fin" '
            'quedaba 188 días tarde.'
        ),
        'actividades': ['Entregas — define su fecha de fin.'],
        'tipo_control': 'number_input', 'min_value': 0.0,
    },
    {
        'clave': 'desfase_rescate_dias',
        'etiqueta': 'Desfase de rescate (días)',
        'leyenda': (
            'Corrección aplicada cuando se usa una fecha de respaldo en vez de la fecha de '
            'entrega real, para no sesgar el resultado.'
        ),
        'justificacion': (
            'Cuando falta la fecha de entrega pero el estatus ya es "Entregado", se usa la fecha '
            'de última actualización como sustituto. Sin corrección esa fecha llega '
            'sistemáticamente antes que la entrega real; el valor es la mediana de esa diferencia, '
            'medida sobre 28,810 pares en 16 campañas, y sube la cobertura de fecha de 86-99% a '
            '100% en 12 de ellas sin tocar ninguna fecha que ya existía.'
        ),
        'actividades': ['Entregas — rellena la fecha faltante con última actualización + este desfase.'],
        'tipo_control': 'number_input', 'min_value': 0.0,
    },
]


@st.fragment
def _mostrar_parametros_y_guardar(configuracion_vigente: dict) -> None:
    """Pinta los 6 parámetros en grillas de 3 columnas, sus gráficas y el botón de guardar.

    Aislado en un fragment: mover un slider re-ejecuta este fragment (para que
    la gráfica combinada se mueva en vivo), pero no el script completo.

    Args:
        configuracion_vigente: parámetros actualmente vigentes, para
            precargar el valor inicial de cada control.

    Returns:
        None.
    """
    st.subheader('Cortes de percentil')

    columnas_leyenda = st.columns(3)
    for columna, parametro in zip(columnas_leyenda, CORTES_DE_PERCENTIL):
        with columna:
            st.markdown(f"**{parametro['etiqueta']}**")
            st.markdown(parametro['leyenda'])

    columnas_justificacion = st.columns(3)
    for columna, parametro in zip(columnas_justificacion, CORTES_DE_PERCENTIL):
        with columna:
            st.markdown(parametro['justificacion'])
            for actividad in parametro['actividades']:
                st.markdown(f'- {actividad}')

    valores_percentil = {}
    columnas_slider = st.columns(3)
    for columna, parametro in zip(columnas_slider, CORTES_DE_PERCENTIL):
        with columna:
            valores_percentil[parametro['clave']] = st.slider(
                parametro['etiqueta'],
                min_value=parametro['min_value'],
                max_value=parametro['max_value'],
                value=float(configuracion_vigente[parametro['clave']]),
                step=parametro['step'],
            )

    porcentaje_inicio = valores_percentil['porcentaje_inicio']
    porcentaje_fin = valores_percentil['porcentaje_fin']
    cobertura_aviso = valores_percentil['cobertura_aviso']

    st.plotly_chart(
        charts.construir_grafica_de_percentiles_combinada(
            {
                'Porcentaje inicio': porcentaje_inicio,
                'Porcentaje fin': porcentaje_fin,
                'Cobertura de aviso': cobertura_aviso,
            }
        ),
        use_container_width=True,
    )

    st.subheader('Otros parámetros')

    columnas_leyenda_otros = st.columns(3)
    for columna, parametro in zip(columnas_leyenda_otros, OTROS_PARAMETROS):
        with columna:
            st.markdown(f"**{parametro['etiqueta']}**")
            st.markdown(parametro['leyenda'])

    columnas_justificacion_otros = st.columns(3)
    for columna, parametro in zip(columnas_justificacion_otros, OTROS_PARAMETROS):
        with columna:
            st.markdown(parametro['justificacion'])
            for actividad in parametro['actividades']:
                st.markdown(f'- {actividad}')

    valores_otros = {}
    columnas_valor_otros = st.columns(3)
    for columna, parametro in zip(columnas_valor_otros, OTROS_PARAMETROS):
        with columna:
            if parametro['tipo_control'] == 'slider':
                valores_otros[parametro['clave']] = st.slider(
                    parametro['etiqueta'],
                    min_value=parametro['min_value'],
                    max_value=parametro['max_value'],
                    value=float(configuracion_vigente[parametro['clave']]),
                )
            else:
                valores_otros[parametro['clave']] = st.number_input(
                    parametro['etiqueta'],
                    min_value=parametro['min_value'],
                    value=float(configuracion_vigente[parametro['clave']]),
                )

    porcentaje_bloque_minimo = valores_otros['porcentaje_bloque_minimo']
    hueco_entregas_dias = valores_otros['hueco_entregas_dias']
    desfase_rescate_dias = valores_otros['desfase_rescate_dias']

    valores_configuracion = {**valores_percentil, **valores_otros}
    hay_cambios = any(
        valores_configuracion[clave] != float(configuracion_vigente[clave]) for clave in valores_configuracion
    )

    _, columna_centro, _ = st.columns([1, 2, 1])
    with columna_centro:
        nombre_nueva_configuracion = st.text_input('Nombre de esta combinación de parámetros')
        entiendo_el_recalculo = st.checkbox('Entiendo que esto recalculará todas las campañas')
        hay_nombre = bool(nombre_nueva_configuracion.strip())
        guardar = st.button(
            'Guardar y recalcular',
            disabled=not (entiendo_el_recalculo and hay_cambios and hay_nombre),
        )

    if guardar:
        try:
            resultado = api_client.crear_configuracion(
                nombre=nombre_nueva_configuracion,
                porcentaje_fin=porcentaje_fin,
                porcentaje_inicio=porcentaje_inicio,
                porcentaje_bloque_minimo=porcentaje_bloque_minimo,
                hueco_entregas_dias=hueco_entregas_dias,
                desfase_rescate_dias=desfase_rescate_dias,
                cobertura_aviso=cobertura_aviso,
            )
        except Exception as error:
            st.error('No se pudo guardar la nueva configuración.')
            with st.expander('Detalles técnicos'):
                st.exception(error)
        else:
            st.success(f"Configuración guardada. Recalculando {resultado['total_campanas']} campañas.")
            st.session_state['id_lote_seleccionado'] = resultado['id_lote']
            if st.button('Ver progreso del recálculo'):
                st.switch_page('views/jobs.py')


_mostrar_parametros_y_guardar(configuracion_vigente)
