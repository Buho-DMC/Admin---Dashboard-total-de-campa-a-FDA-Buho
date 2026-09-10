"""Metodología: explica el cálculo, permite ajustar parámetros y recalcular."""

import streamlit as st

import api_client
import charts

st.title('Metodología')

st.markdown(
    'Estos parámetros controlan cómo se calcula el snapshot de cada campaña a partir de '
    'las fechas de entrega. Ajusta los valores y usa las gráficas de abajo para ver qué '
    'proporción de una distribución de ejemplo queda a cada lado de un corte de percentil '
    'antes de guardar un cambio.'
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


@st.fragment
def _mostrar_parametros_y_guardar(configuracion_vigente: dict) -> None:
    """Pinta los 6 parámetros, sus gráficas y el botón de guardar, aislados del resto de la página.

    Mover un slider re-ejecuta este fragment (para que su gráfica de
    percentil se mueva en vivo), pero no el script completo — el título, el
    expander de historial y la carga inicial de `configuracion_vigente` de
    arriba no se vuelven a pedir a la API en cada arrastre.

    Args:
        configuracion_vigente: parámetros actualmente vigentes, para
            precargar el valor inicial de cada control.

    Returns:
        None.
    """
    st.subheader('Cortes de percentil')

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown(
            'Define desde qué punto se considera que Entregas arrancó de verdad, ignorando '
            'registros sueltos y prematuros.'
        )
        with st.expander('Ver justificación'):
            st.markdown(
                'Es el percentil sobre las unidades ya capturadas, no sobre el universo completo. '
                'En la campaña 134 había un solo registro suelto de más de un año antes del arranque '
                'real; con el corte al 1%, ese registro queda fuera sin necesidad de una regla aparte '
                '(el envío número ~20 de 1,956 ya marca el arranque real).'
            )
    with columna_control:
        porcentaje_inicio = st.slider(
            'Porcentaje inicio', min_value=0.01, max_value=0.5, value=float(configuracion_vigente['porcentaje_inicio']), step=0.01
        )
        st.plotly_chart(charts.construir_grafica_de_percentil(porcentaje_inicio, f'Porcentaje inicio ({porcentaje_inicio:.0%})'))

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown(
            'Define cuándo Pick & Pack se considera terminado. **Ya no aplica a Entregas** — '
            'Entregas usa "Hueco de entregas" en su lugar.'
        )
        with st.expander('Ver justificación'):
            st.markdown(
                'El costo de seguir esperando es plano hasta el 98-99% del universo y se dispara '
                'después: subir de 95% a 98% cuesta 1 día de mediana, y de 98% a 99% cuesta 1.13 '
                'días — no hay un salto real que marque un corte "natural", así que el valor es una '
                'decisión de negocio, confirmada con la medición de las 19 campañas.'
            )
    with columna_control:
        porcentaje_fin = st.slider(
            'Porcentaje fin', min_value=0.5, max_value=0.99, value=float(configuracion_vigente['porcentaje_fin']), step=0.01
        )
        st.plotly_chart(charts.construir_grafica_de_percentil(porcentaje_fin, f'Porcentaje fin ({porcentaje_fin:.0%})'))

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown(
            'Umbral de datos capturados por debajo del cual el sistema avisa que una campaña tiene '
            'información incompleta. No cambia ningún cálculo, es un semáforo.'
        )
        with st.expander('Ver justificación'):
            st.markdown(
                'Desde que el denominador de los cortes de percentil pasó a ser lo capturado (y no '
                'el universo completo), una campaña con captura incompleta se mide sobre menos '
                'unidades y se ve algo más rápida. Eso no se esconde: junto a cada fecha se publican '
                'siempre el universo, cuántas unidades tienen dato, y se avisa cuando la cobertura '
                'cae por debajo de este umbral.'
            )
    with columna_control:
        cobertura_aviso = st.slider(
            'Cobertura de aviso', min_value=0.5, max_value=0.99, value=float(configuracion_vigente['cobertura_aviso']), step=0.01
        )
        st.plotly_chart(charts.construir_grafica_de_percentil(cobertura_aviso, f'Cobertura de aviso ({cobertura_aviso:.0%})'))

    st.subheader('Otros parámetros')

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown(
            'Filtra escaneos sueltos de pre-surtido para que no se confundan con el arranque real '
            'de Pick & Pack.'
        )
        with st.expander('Ver justificación'):
            st.markdown(
                'Es el peso mínimo, como % del total de escaneos, que debe tener el primer bloque de '
                'actividad para contar como arranque. Se probó con 5%, 10%, 20% y 30% y el arranque '
                'resultante no cambió en ninguna de las 16 campañas comparadas — se eligió el valor '
                'más conservador (5%) porque no corta trabajo real.'
            )
    with columna_control:
        porcentaje_bloque_minimo = st.number_input(
            'Porcentaje bloque mínimo', min_value=0.0, max_value=1.0, value=float(configuracion_vigente['porcentaje_bloque_minimo'])
        )

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown('Días sin entregas que separan el cierre real de un rezagado aislado. Define el fin de Entregas.')
        with st.expander('Ver justificación'):
            st.markdown(
                'Se comparó contra la hoja capturada a mano en 15 campañas, barriendo el hueco de 3 '
                'a 30 días: entre 9 y 30 días el resultado es idéntico, así que se eligió 10 por ser '
                'el extremo más ajustado del tramo estable. Un caso real que lo justifica: una '
                'campaña de enero con un solo envío aislado en agosto — sin este corte, el "fin" '
                'quedaba 188 días tarde.'
            )
    with columna_control:
        hueco_entregas_dias = st.number_input(
            'Hueco de entregas (días)', min_value=0.0, value=float(configuracion_vigente['hueco_entregas_dias'])
        )

    columna_explicacion, columna_control = st.columns(2)
    with columna_explicacion:
        st.markdown(
            'Corrección aplicada cuando se usa una fecha de respaldo en vez de la fecha de entrega '
            'real, para no sesgar el resultado.'
        )
        with st.expander('Ver justificación'):
            st.markdown(
                'Cuando falta la fecha de entrega pero el estatus ya es "Entregado", se usa la fecha '
                'de última actualización como sustituto. Sin corrección esa fecha llega '
                'sistemáticamente antes que la entrega real; el valor es la mediana de esa diferencia, '
                'medida sobre 28,810 pares en 16 campañas, y sube la cobertura de fecha de 86-99% a '
                '100% en 12 de ellas sin tocar ninguna fecha que ya existía.'
            )
    with columna_control:
        desfase_rescate_dias = st.number_input(
            'Desfase de rescate (días)', min_value=0.0, value=float(configuracion_vigente['desfase_rescate_dias'])
        )

    nombre_nueva_configuracion = st.text_input('Nombre de esta combinación de parámetros')
    entiendo_el_recalculo = st.checkbox('Entiendo que esto recalculará todas las campañas')

    if st.button('Guardar y recalcular', disabled=not entiendo_el_recalculo):
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
                st.switch_page('pages/jobs.py')


_mostrar_parametros_y_guardar(configuracion_vigente)
