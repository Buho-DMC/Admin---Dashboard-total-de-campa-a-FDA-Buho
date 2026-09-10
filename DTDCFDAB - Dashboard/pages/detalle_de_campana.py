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

@st.fragment
def _mostrar_fechas_de_hitos(id_campana: int, eventos_de_campana: list[dict]) -> None:
    """Pinta y guarda las fechas de hitos de una campaña sin refrescar el resto de la página.

    Aislado en un fragment: guardar la fecha de un hito no debe volver a pedir
    la lista de campañas, el snapshot ni el último job — eso solo hace falta
    si el usuario cambia de campaña en el selector de arriba (que sigue
    disparando un rerun completo, como debe).

    Args:
        id_campana: campaña a la que pertenecen los hitos.
        eventos_de_campana: catálogo de hitos con su fecha capturada (o `None`).

    Returns:
        None.
    """
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


st.subheader('Fechas de hitos')
_mostrar_fechas_de_hitos(id_campana, eventos_de_campana)

st.subheader('Snapshot')
if snapshot is None:
    st.info('Aún no se ha calculado el snapshot de esta campaña.')
else:
    st.json(snapshot)

st.subheader('Último job')
st.write(f"Estado: {ultimo_job['estado']}")
if ultimo_job['estado'] == 'fallido' and ultimo_job.get('error'):
    st.error(ultimo_job['error'])

st.subheader('Borrar campaña')
confirmar_borrado = st.checkbox('Confirmo que quiero borrar esta campaña y todo su historial')
if st.button('Borrar campaña', disabled=not confirmar_borrado):
    try:
        api_client.borrar_campana(id_campana)
    except Exception as error:
        st.error('No se pudo borrar la campaña.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
    else:
        st.success('Campaña borrada.')
