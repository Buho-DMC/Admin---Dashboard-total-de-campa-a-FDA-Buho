"""Vista global de campañas: snapshots bajo la configuración vigente."""

import streamlit as st

import api_client

st.title('Campañas')

try:
    snapshots_vigentes = api_client.list_snapshots_vigentes()
except Exception as error:
    st.error('No se pudieron obtener las campañas.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

if not snapshots_vigentes:
    st.info('Todavía no hay campañas con snapshot calculado bajo la configuración vigente.')
    st.stop()

st.dataframe(
    snapshots_vigentes,
    column_order=['id_campana', 'numero_envios', 'porcentaje_alcanzado_entregas', 'ultima_entrega', 'calculado_en'],
    hide_index=True,
)

for snapshot in snapshots_vigentes:
    if st.button(f"Ver detalle — campaña {snapshot['id_campana']}", key=f"ver_detalle_{snapshot['id_campana']}"):
        st.session_state['id_campana_seleccionada'] = snapshot['id_campana']
        st.switch_page('pages/detalle_de_campana.py')

if st.button('Dar de alta una campaña nueva'):
    st.switch_page('pages/alta_de_campana.py')
