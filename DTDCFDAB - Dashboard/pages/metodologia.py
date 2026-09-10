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

st.subheader('Cortes de percentil')
porcentaje_inicio = st.slider(
    'Porcentaje inicio', min_value=0.01, max_value=0.5, value=float(configuracion_vigente['porcentaje_inicio']), step=0.01
)
st.plotly_chart(charts.construir_grafica_de_percentil(porcentaje_inicio, f'Porcentaje inicio ({porcentaje_inicio:.0%})'))

porcentaje_fin = st.slider(
    'Porcentaje fin', min_value=0.5, max_value=0.99, value=float(configuracion_vigente['porcentaje_fin']), step=0.01
)
st.plotly_chart(charts.construir_grafica_de_percentil(porcentaje_fin, f'Porcentaje fin ({porcentaje_fin:.0%})'))

cobertura_aviso = st.slider(
    'Cobertura de aviso', min_value=0.5, max_value=0.99, value=float(configuracion_vigente['cobertura_aviso']), step=0.01
)
st.plotly_chart(charts.construir_grafica_de_percentil(cobertura_aviso, f'Cobertura de aviso ({cobertura_aviso:.0%})'))

st.subheader('Otros parámetros')
porcentaje_bloque_minimo = st.number_input(
    'Porcentaje bloque mínimo', min_value=0.0, max_value=1.0, value=float(configuracion_vigente['porcentaje_bloque_minimo'])
)
hueco_entregas_dias = st.number_input(
    'Hueco de entregas (días)', min_value=0.0, value=float(configuracion_vigente['hueco_entregas_dias'])
)
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
