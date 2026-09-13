"""Bandeja de jobs: activos, fallidos e historial reciente, con auto-refresh."""

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import api_client

st.title('Jobs')
st_autorefresh(interval=30_000, key='autorefresh_jobs')

columna_actualizar, columna_reintentar = st.columns(2)
if columna_actualizar.button('Actualizar estado'):
    st.rerun()

if columna_reintentar.button('Reintentar fallidos'):
    try:
        resultado_reintento = api_client.reintentar_fallidos()
    except Exception as error:
        st.error('No se pudo reintentar los jobs fallidos.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
    else:
        st.success(f"Se reencolaron {resultado_reintento['total_reintentados']} jobs.")

try:
    resumen_jobs = api_client.get_resumen_jobs()
except Exception as error:
    st.error('No se pudo obtener el resumen de jobs.')
    with st.expander('Detalles técnicos'):
        st.exception(error)
    st.stop()

if not resumen_jobs:
    st.info('No hay jobs en el resumen (la base de datos está vacía o sin actividad).')
    st.stop()

st.dataframe(resumen_jobs, hide_index=True)

# Los botones individuales de reintento ahora operan sobre la misma lista que la tabla.
# st.dataframe no tiene botones embebidos, se renderizan abajo temporalmente para no
# perder la capacidad de reintento individual sin tener que meter AG Grid u otras dependencias.
st.subheader('Reintentos individuales')
hay_fallidos = False
for job in resumen_jobs:
    if job['estado'] == 'fallido':
        hay_fallidos = True
        columna_texto, columna_boton = st.columns([3, 1])
        columna_texto.write(f"Campaña {job['id_campana']} (Job {job['id_job_ejecucion']}): falló.")
        if columna_boton.button('Reintentar', key=f"reintentar_{job['id_job_ejecucion']}"):
            try:
                api_client.reintentar_job(job['id_job_ejecucion'])
            except Exception as error:
                st.error(f"No se pudo reintentar el job {job['id_job_ejecucion']}.")
                with st.expander('Detalles técnicos'):
                    st.exception(error)
            else:
                st.success(f"Job {job['id_job_ejecucion']} reencolado.")
                st.rerun()

if not hay_fallidos:
    st.write('No hay jobs fallidos vigentes.')
