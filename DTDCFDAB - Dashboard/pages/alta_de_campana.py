"""Alta de una campaña nueva: selector de Retool + captura de hitos FDA."""

import math

import streamlit as st

import api_client

st.title('Alta de campaña')

try:
    campanas_retool = api_client.list_campanas_retool()
    catalogo_eventos = api_client.list_eventos()
except Exception as error:
    st.error('No se pudo cargar la información necesaria para dar de alta una campaña.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

if not campanas_retool:
    st.info('No hay campañas FDA disponibles en Retool para dar de alta.')
    st.stop()

campanas_por_id_claw = {campana['id_claw']: campana for campana in campanas_retool}
id_claw_seleccionado = st.selectbox(
    'Campaña en Claw',
    list(campanas_por_id_claw.keys()),
    format_func=lambda id_claw: campanas_por_id_claw[id_claw]['campana'],
)
campana_seleccionada = campanas_por_id_claw[id_claw_seleccionado]

st.subheader('Fechas de los hitos FDA')
mitad = math.ceil(len(catalogo_eventos) / 2)
eventos_por_columna = (catalogo_eventos[:mitad], catalogo_eventos[mitad:])

fechas_por_codigo_evento = {}
for columna, eventos_de_la_columna in zip(st.columns(2), eventos_por_columna):
    with columna:
        for evento in eventos_de_la_columna:
            fechas_por_codigo_evento[evento['codigo']] = st.date_input(evento['nombre'], key=f"fecha_{evento['codigo']}")

if st.button('Dar de alta'):
    milestones = [
        {'codigo_evento': codigo_evento, 'fecha': fecha.isoformat()}
        for codigo_evento, fecha in fechas_por_codigo_evento.items()
    ]
    try:
        resultado = api_client.dar_de_alta_campana(
            id_claw=campana_seleccionada['id_claw'],
            cliente=campana_seleccionada['cliente_clave'],
            nombre=campana_seleccionada['campana'],
            inicio_campana=str(campana_seleccionada['inicio_campana']),
            milestones=milestones,
        )
    except Exception as error:
        st.error('No se pudo dar de alta la campaña.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
    else:
        st.success(f"Campaña '{resultado['campana']['nombre']}' creada.")
        st.session_state['id_job_seleccionado'] = resultado['job']['id_job']
        if st.button('Ver progreso del job'):
            st.switch_page('pages/jobs.py')
