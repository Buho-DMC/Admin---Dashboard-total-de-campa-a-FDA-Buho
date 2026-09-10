"""Detalle de una campaña: fechas de hitos, snapshot y estado del último job."""

from datetime import datetime

import streamlit as st

import api_client

st.title('Detalle de campaña')

id_campana_preseleccionada = st.session_state.get('id_campana_seleccionada')

try:
    campanas = api_client.list_campanas()
except Exception as error:
    st.error('No se pudieron obtener las campañas.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

if not campanas:
    st.info('Todavía no hay campañas dadas de alta.')
    st.stop()

campanas_por_id = {campana['id_campana']: campana for campana in campanas}
ids_disponibles = list(campanas_por_id.keys())
indice_por_defecto = ids_disponibles.index(id_campana_preseleccionada) if id_campana_preseleccionada in ids_disponibles else 0
id_campana = st.selectbox(
    'Campaña', ids_disponibles, index=indice_por_defecto, format_func=lambda id_campana: campanas_por_id[id_campana]['nombre']
)

try:
    eventos_de_campana = api_client.list_eventos_de_campana(id_campana)
    snapshot = api_client.get_snapshot_de_campana(id_campana)
    ultimo_job = api_client.get_ultimo_job_de_campana(id_campana)
except Exception as error:
    st.error('No se pudo obtener el detalle de la campaña.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

st.subheader('Fechas de hitos')
for evento in eventos_de_campana:
    fecha_actual = datetime.fromisoformat(evento['fecha']).date() if evento['fecha'] else None
    fecha_nueva = st.date_input(evento['nombre'], value=fecha_actual, key=f"fecha_{evento['codigo']}")
    if st.button(f"Guardar {evento['nombre']}", key=f"guardar_{evento['codigo']}") and fecha_nueva is not None:
        try:
            api_client.upsert_evento_de_campana(id_campana, evento['codigo'], fecha_nueva.isoformat())
        except Exception as error:
            st.error('No se pudo guardar la fecha.')
            with st.expander('Detalles técnicos'):
                st.exception(error)
        else:
            st.success('Fecha guardada.')

st.subheader('Snapshot')
if snapshot is None:
    st.info('Aún no se ha calculado el snapshot de esta campaña.')
else:
    st.json(snapshot)

st.subheader('Último job')
st.write(f"Estado: {ultimo_job['estado']}")
