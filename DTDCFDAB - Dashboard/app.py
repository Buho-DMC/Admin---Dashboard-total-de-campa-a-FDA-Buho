"""Punto de entrada del Dashboard: gate de PIN y navegación entre páginas."""

import streamlit as st

import config

st.set_page_config(page_title='DTDCFDAB - Dashboard', page_icon='📋', layout='wide')


def _gate_de_contrasena() -> bool:
    """Bloquea el acceso a la UI hasta que se ingrese la contraseña correcta.

    Es una capa distinta del API key que usa `api_client.py`: este gate controla
    quién puede ver la app, el API key autentica las peticiones hacia
    DTDCFDAB - API — decisión ya cerrada en el spec de diseño.

    Returns:
        True si la sesión ya está autenticada o si la contraseña ingresada es
        correcta; False mientras se espera la contraseña.
    """
    if st.session_state.get('autenticado'):
        return True
    contrasena = st.text_input('Contraseña', type='password')
    if st.button('Entrar'):
        if contrasena == config.obtener_contrasena_de_acceso():
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error('Contraseña incorrecta.')
    return False


def main() -> None:
    """Valida el gate de PIN y arranca la navegación entre páginas."""
    if not _gate_de_contrasena():
        return

    navegacion = st.navigation(
        [
            st.Page('pages/campanas.py', title='Campañas', icon='📋', default=True),
            st.Page('pages/alta_de_campana.py', title='Alta de campaña', icon='➕'),
            st.Page('pages/detalle_de_campana.py', title='Detalle de campaña', icon='🔍'),
            st.Page('pages/metodologia.py', title='Metodología', icon='📐'),
            st.Page('pages/jobs.py', title='Jobs', icon='⚙️'),
        ]
    )
    navegacion.run()


if __name__ == '__main__':
    main()
