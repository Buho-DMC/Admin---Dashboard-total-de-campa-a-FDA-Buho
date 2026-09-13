"""Campañas: selector, gráficas, análisis de fechas, hitos y acciones de una campaña."""

from datetime import datetime

import streamlit as st

import analisis_de_fechas
import api_client
import charts

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

snapshots_ordenados = sorted(snapshots_vigentes, key=lambda snapshot: snapshot.get('calculado_en') or '', reverse=True)
snapshots_por_id = {snapshot['id_campana']: snapshot for snapshot in snapshots_ordenados}
ids_disponibles = list(snapshots_por_id.keys())

if st.button('Dar de alta una campaña nueva'):
    st.switch_page('views/alta_de_campana.py')


@st.cache_data(ttl=30)
def _obtener_eventos_de_campana_cacheado(id_campana: int) -> list[dict]:
    """Envoltura cacheada de `api_client.list_eventos_de_campana` para el selector de campaña."""
    return api_client.list_eventos_de_campana(id_campana)


@st.cache_data(ttl=30)
def _obtener_ultimo_job_cacheado(id_campana: int) -> dict:
    """Envoltura cacheada de `api_client.get_ultimo_job_de_campana` para el selector de campaña."""
    return api_client.get_ultimo_job_de_campana(id_campana)


@st.fragment
def _mostrar_campana_seleccionada(ids_disponibles: list[int], snapshots_por_id: dict[int, dict], snapshots_vigentes: list[dict]) -> None:
    """Selector, gráfica, análisis de fechas, hitos y acciones de la campaña elegida.

    Aislado en un fragment: cambiar de vista de gráfica, de tipo de análisis, o
    guardar hitos no debe volver a pedir `list_snapshots_vigentes` a la API —
    ya está completa en memoria para todas las campañas.

    Args:
        ids_disponibles: ids de campaña, ordenados de más a menos reciente.
        snapshots_por_id: snapshot de cada campaña, indexado por id.
        snapshots_vigentes: lista completa de snapshots, para los promedios
            históricos del análisis de fechas.

    Returns:
        None.
    """
    id_campana = st.selectbox('Campaña', ids_disponibles, format_func=lambda id_campana: f'Campaña {id_campana}')
    snapshot = snapshots_por_id[id_campana]

    vista_grafica = st.radio('Gráfica', ['Por actividad', 'Por responsable'], horizontal=True)
    if vista_grafica == 'Por responsable':
        figura = charts.construir_grafica_por_responsable(snapshot)
    else:
        figura = charts.construir_grafica_por_actividad(snapshot)

    if figura is not None:
        st.plotly_chart(figura, use_container_width=True)
    else:
        st.info('Todavía no hay etapas con fecha de inicio y fin.')

    st.subheader('Análisis de fechas')
    tipo_de_analisis = st.radio('Tipo de análisis', ['Duración', 'Offset', 'Fechas'], horizontal=True)
    if tipo_de_analisis == 'Duración':
        _mostrar_tarjetas_con_delta(analisis_de_fechas.calcular_duracion_vs_promedio(snapshot, snapshots_vigentes))
    elif tipo_de_analisis == 'Offset':
        _mostrar_tarjetas_con_delta(analisis_de_fechas.calcular_offset_vs_promedio(snapshot, snapshots_vigentes))
    else:
        for etiqueta, fecha in analisis_de_fechas.listar_fechas_ordenadas(snapshot):
            st.write(f"{etiqueta}: {fecha.strftime('%Y-%m-%d')}")

    try:
        eventos_de_campana = _obtener_eventos_de_campana_cacheado(id_campana)
        ultimo_job = _obtener_ultimo_job_cacheado(id_campana)
    except Exception as error:
        st.error('No se pudo obtener el detalle de la campaña.')
        with st.expander('Detalles técnicos'):
            st.exception(error)
        st.stop()

    with st.expander('Fechas de hitos'):
        valores_originales = {}
        valores_nuevos = {}
        columnas = st.columns(2)
        for indice, evento in enumerate(eventos_de_campana):
            fecha_actual = None
            if evento['fecha']:
                try:
                    fecha_actual = datetime.fromisoformat(evento['fecha']).date()
                except (ValueError, TypeError):
                    pass
            valores_originales[evento['codigo']] = fecha_actual
            with columnas[indice % 2]:
                valores_nuevos[evento['codigo']] = st.date_input(
                    evento['nombre'], value=fecha_actual, key=f"fecha_{evento['codigo']}"
                )

        if st.button('Actualizar fechas modificadas'):
            campos_modificados = [
                (codigo, fecha) for codigo, fecha in valores_nuevos.items()
                if fecha is not None and fecha != valores_originales[codigo]
            ]
            if not campos_modificados:
                st.info('No hay cambios que guardar.')
            else:
                errores = []
                for codigo, fecha in campos_modificados:
                    try:
                        api_client.upsert_evento_de_campana(id_campana, codigo, fecha.isoformat())
                    except Exception as error:
                        errores.append((codigo, error))
                if errores:
                    st.error(f'No se pudieron guardar {len(errores)} de {len(campos_modificados)} fecha(s).')
                else:
                    st.success(f'{len(campos_modificados)} fecha(s) actualizada(s).')

    columna_estado, columna_borrar = st.columns(2)
    with columna_estado:
        st.write(f"Último job: {ultimo_job['estado']}")
        if ultimo_job['estado'] == 'fallido' and ultimo_job.get('error'):
            st.error(ultimo_job['error'])
    with columna_borrar:
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


def _mostrar_tarjetas_con_delta(resultado: dict[str, tuple[float, float] | None]) -> None:
    """Pinta una tarjeta `st.metric` por etapa, con el delta vs. el promedio histórico.

    Args:
        resultado: dict de `analisis_de_fechas.calcular_duracion_vs_promedio` o
            `calcular_offset_vs_promedio` — `(valor_real, delta)` por etapa.

    Returns:
        None.
    """
    columnas = st.columns(4)
    indice = 0
    for nombre_etapa, valores in resultado.items():
        if valores is None:
            continue
        valor_real, delta = valores
        with columnas[indice % 4]:
            st.metric(nombre_etapa, f'{valor_real:.2f} días', delta=f'{delta:+.2f} días', delta_color='inverse')
        indice += 1


_mostrar_campana_seleccionada(ids_disponibles, snapshots_por_id, snapshots_ordenados)
