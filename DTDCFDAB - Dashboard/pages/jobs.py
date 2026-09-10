"""Progreso de jobs: búsqueda por lote (recálculo global) o por job individual (alta), con auto-refresh."""

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import api_client

st.title('Jobs')

st_autorefresh(interval=30_000, key='autorefresh_jobs')

id_lote_preseleccionado = st.session_state.get('id_lote_seleccionado', '')
id_job_preseleccionado = st.session_state.get('id_job_seleccionado')

modo_de_busqueda = st.radio('Buscar por', ['Lote (recálculo global)', 'Job individual (alta de campaña)'])

if st.button('Actualizar estado'):
    st.rerun()

jobs_a_mostrar = []
if modo_de_busqueda == 'Lote (recálculo global)':
    id_lote = st.text_input('Id de lote', value=id_lote_preseleccionado)
    if not id_lote:
        st.info('Escribe un id de lote para ver el progreso de sus jobs.')
        st.stop()
    try:
        jobs_a_mostrar = api_client.list_jobs_de_lote(id_lote)
    except Exception as error:
        st.error('No se pudo obtener el progreso de los jobs.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
        st.stop()
else:
    id_job = st.number_input('Id de job', min_value=1, value=id_job_preseleccionado or 1, step=1)
    try:
        jobs_a_mostrar = [api_client.get_job(int(id_job))]
    except Exception as error:
        st.error('No se pudo obtener el job.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
        st.stop()

if not jobs_a_mostrar:
    st.info('No se encontraron jobs.')
    st.stop()

total_de_jobs = len(jobs_a_mostrar)
jobs_listos = sum(1 for job in jobs_a_mostrar if job['estado'] in ('exitoso', 'fallido'))
st.progress(jobs_listos / total_de_jobs, text=f'{jobs_listos} de {total_de_jobs} listas')

for job in jobs_a_mostrar:
    columna_estado, columna_accion = st.columns([3, 1])
    columna_estado.write(f"Campaña {job['id_campana']} — {job['estado']}")
    if job['estado'] == 'fallido':
        if columna_accion.button('Reintentar', key=f"reintentar_{job['id_job']}"):
            try:
                api_client.reintentar_job(job['id_job'])
            except Exception as error:
                st.error('No se pudo reintentar el job.')
                with st.expander('Detalles técnicos'):
                    st.exception(error)
            else:
                st.success('Job reencolado.')
