"""Detalle de una campaña: fechas de hitos, snapshot y estado del último job."""

from datetime import datetime

import streamlit as st

import api_client
import charts


def _formatear_metrica(valor, formato='', usar_pct=False) -> str:
    """Aplica un formato a un valor de métrica o retorna 'Sin dato' si es None."""
    if valor is None:
        return 'Sin dato'
    if usar_pct:
        valor = valor * 100
        formato = formato or '.2f'
    
    texto = f"{valor:{formato}}" if formato else str(valor)
    return f"{texto}%" if usar_pct else texto


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
        fecha_actual = None
        if evento['fecha']:
            try:
                fecha_actual = datetime.fromisoformat(evento['fecha']).date()
            except Exception:
                pass
        
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
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Envíos', _formatear_metrica(snapshot.get('numero_envios')))
    col2.metric('Alcanzado entregas', _formatear_metrica(snapshot.get('porcentaje_alcanzado_entregas'), formato='.2f', usar_pct=True))
    col3.metric('ODPs', _formatear_metrica(snapshot.get('numero_odps')))
    col4.metric('Folios', _formatear_metrica(snapshot.get('numero_folios')))
    
    col5, col6, col7 = st.columns(3)
    col5.metric('Respuesta Buho', _formatear_metrica(snapshot.get('respuesta_buho_dias'), formato='.2f'))
    col6.metric('Respuesta FDA', _formatear_metrica(snapshot.get('respuesta_fda_dias'), formato='.2f'))
    
    ultima_entrega_iso = snapshot.get('ultima_entrega')
    ultima_entrega_str = 'Sin dato'
    if ultima_entrega_iso:
        try:
            ultima_entrega_str = datetime.fromisoformat(ultima_entrega_iso).strftime('%Y-%m-%d')
        except Exception as error:
            st.error('No se pudo interpretar la fecha de última entrega.')
            with st.expander('Detalles técnicos'):
                st.exception(error)

    col7.metric('Última entrega', ultima_entrega_str)

    figura = charts.construir_grafica_de_linea_de_tiempo(snapshot)
    if figura is not None:
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.info('Todavía no hay etapas con fecha de inicio y fin.')
        
    with st.expander('Ver datos crudos'):
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
