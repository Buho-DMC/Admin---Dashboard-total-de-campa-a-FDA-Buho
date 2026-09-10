"""Cliente HTTP hacia DTDCFDAB - API: una función por endpoint del catálogo."""

import logging
import time

import requests

import config

NUMERO_MAXIMO_DE_REINTENTOS = 3
TIMEOUT_EN_SEGUNDOS = 20


def _realizar_peticion(metodo: str, ruta: str, **kwargs) -> requests.Response:
    """Ejecuta una petición HTTP hacia DTDCFDAB - API con reintentos y manejo de errores.

    Punto único de entrada de todas las demás funciones de este módulo: agrega el
    header `X-API-Key`, aplica timeout, y reintenta con backoff exponencial solo
    en errores 5xx o timeout — nunca en errores 4xx, que son del cliente y no se
    resuelven reintentando (regla de `python/api-client.md`).

    Args:
        metodo: verbo HTTP en mayúsculas, por ejemplo `'GET'`, `'POST'`, `'PUT'`.
        ruta: ruta del endpoint sin el host, por ejemplo `'/campanas'` o
            `f'/campanas/{id_campana}'`.
        **kwargs: se pasan tal cual a `requests.request` (`params`, `json`, etc.).

    Returns:
        La respuesta de `requests` cuando el status code está en el rango 200-299.

    Raises:
        PermissionError: si la API responde 401 (llave de API inválida).
        RuntimeError: si la API responde 429, o 5xx tras agotar los reintentos.
        requests.HTTPError: si la API responde otro código 4xx.
    """
    url = f'{config.obtener_url_base_api()}{ruta}'
    encabezados = {'X-API-Key': config.obtener_llave_de_api()}

    for numero_de_intento in range(1, NUMERO_MAXIMO_DE_REINTENTOS + 1):
        try:
            logging.info(f'{metodo} {ruta} (intento {numero_de_intento}/{NUMERO_MAXIMO_DE_REINTENTOS})')
            respuesta = requests.request(metodo, url, headers=encabezados, timeout=TIMEOUT_EN_SEGUNDOS, **kwargs)
        except requests.exceptions.Timeout:
            logging.warning(f'Timeout en {metodo} {ruta} (intento {numero_de_intento}/{NUMERO_MAXIMO_DE_REINTENTOS})')
            time.sleep(2**numero_de_intento)
            continue

        if respuesta.status_code < 300:
            logging.info(f'{metodo} {ruta} — {respuesta.status_code} OK')
            return respuesta
        if respuesta.status_code == 401:
            raise PermissionError('Llave de API inválida o no configurada')
        if respuesta.status_code == 429:
            raise RuntimeError('Límite de peticiones alcanzado en DTDCFDAB - API')
        if respuesta.status_code >= 500:
            logging.warning(
                f'{metodo} {ruta} — {respuesta.status_code} '
                f'(intento {numero_de_intento}/{NUMERO_MAXIMO_DE_REINTENTOS})'
            )
            time.sleep(2**numero_de_intento)
            continue
        respuesta.raise_for_status()

    raise RuntimeError(f'{metodo} {ruta} falló tras {NUMERO_MAXIMO_DE_REINTENTOS} intentos')


def list_eventos() -> list[dict]:
    """Catálogo completo de hitos FDA, ordenado por `orden`.

    Returns:
        Lista de dicts con `id_evento`, `codigo`, `nombre`, `origen`, `rol`, `orden`.
    """
    return _realizar_peticion('GET', '/eventos').json()


def list_campanas_retool() -> list[dict]:
    """Campañas FDA disponibles en Retool para dar de alta (proxy en vivo, sin persistencia).

    Returns:
        Lista de dicts `{'id_claw', 'campana', 'cliente', 'cliente_clave', 'inicio_campana'}`,
        ordenada por `inicio_campana` descendente.
    """
    return _realizar_peticion('GET', '/campanas/retool').json()


def list_campanas() -> list[dict]:
    """Campañas ya dadas de alta en DTDCFDAB.

    Returns:
        Lista de dicts con `id_campana`, `id_claw`, `cliente`, `nombre`,
        `inicio_campana`, `fecha_alta`.
    """
    return _realizar_peticion('GET', '/campanas').json()


def list_eventos_de_campana(id_campana: int) -> list[dict]:
    """Catálogo completo de hitos con la fecha capturada para una campaña (si existe).

    Args:
        id_campana: campaña a consultar.

    Returns:
        Lista de dicts con `id_evento`, `codigo`, `nombre`, `fecha` (`None` si aún
        no se ha capturado) y `actualizado_en`.
    """
    return _realizar_peticion('GET', f'/campanas/{id_campana}/eventos').json()


def get_snapshot_de_campana(id_campana: int) -> dict | None:
    """Snapshot vigente de una campaña.

    Usan esta función tanto la página de Detalle de campaña como la vista global —
    ambas necesitan distinguir "aún no calculado" (respuesta 404, no es un error)
    de una falla real de la API.

    Args:
        id_campana: campaña a consultar.

    Returns:
        Dict con el snapshot, o `None` si la API respondió 404 porque el snapshot
        todavía no se ha calculado para esta campaña.
    """
    try:
        return _realizar_peticion('GET', f'/campanas/{id_campana}/snapshot').json()
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            return None
        raise


def get_ultimo_job_de_campana(id_campana: int) -> dict:
    """Último job (alta o recálculo) de una campaña.

    Args:
        id_campana: campaña a consultar.

    Returns:
        Dict con el estado del job — ver `get_job` para la forma exacta.
    """
    return _realizar_peticion('GET', f'/campanas/{id_campana}/job').json()


def get_configuracion_vigente() -> dict:
    """Parámetros de la Metodología actualmente vigentes.

    Returns:
        Dict con `id_configuracion`, `nombre`, `porcentaje_fin`, `porcentaje_inicio`,
        `porcentaje_bloque_minimo`, `hueco_entregas_dias`, `desfase_rescate_dias`,
        `cobertura_aviso`, `es_vigente`, `creado_en`.
    """
    return _realizar_peticion('GET', '/configuracion/vigente').json()


def list_historial_configuracion() -> list[dict]:
    """Historial de combinaciones de parámetros de la Metodología ya usadas.

    Returns:
        Lista de dicts con la misma forma que `get_configuracion_vigente`.
    """
    return _realizar_peticion('GET', '/configuracion').json()


def list_snapshots_vigentes() -> list[dict]:
    """Snapshots de todas las campañas bajo la configuración vigente.

    Alimenta la vista global "Todas" — el offset y la duración promedio se
    calculan en el Dashboard a partir de estas filas, no en la API (pendiente,
    ver nota en el spec de diseño).

    Returns:
        Lista de dicts, uno por campaña con snapshot calculado bajo la
        configuración vigente.
    """
    return _realizar_peticion('GET', '/snapshots', params={'vigente': 'true'}).json()


def get_job(id_job: int) -> dict:
    """Estado de un job de ETL.

    Args:
        id_job: id del job.

    Returns:
        Dict con `id_job`, `id_campana`, `id_configuracion`, `tipo`, `id_lote`,
        `estado`, y el mensaje de error si `estado == 'fallido'`.
    """
    return _realizar_peticion('GET', f'/jobs/{id_job}').json()


def list_jobs_de_lote(id_lote: str) -> list[dict]:
    """Todos los jobs de un lote de recálculo global.

    Args:
        id_lote: uuid del lote (ver `crear_configuracion`).

    Returns:
        Lista de dicts con la misma forma que `get_job`.
    """
    return _realizar_peticion('GET', '/jobs', params={'id_lote': id_lote}).json()


def dar_de_alta_campana(id_claw: int, cliente: str, nombre: str, inicio_campana: str, milestones: list[dict]) -> dict:
    """Da de alta una campaña nueva y encola su primer cálculo de snapshot.

    Args:
        id_claw: id de la campaña en Claw/Retool.
        cliente: clave del cliente, por ejemplo `'FDA'`.
        nombre: nombre de la campaña.
        inicio_campana: fecha de inicio en formato ISO 8601 (`'2026-09-09T00:00:00'`).
        milestones: lista de `{'codigo_evento': str, 'fecha': str}` (fecha en ISO 8601)
            — los hitos FDA capturados en el formulario de alta.

    Returns:
        Dict `{'campana': dict, 'job': dict}` — la campaña insertada y el job de
        ETL `'alta'` recién encolado.
    """
    cuerpo_de_la_peticion = {
        'id_claw': id_claw,
        'cliente': cliente,
        'nombre': nombre,
        'inicio_campana': inicio_campana,
        'milestones': milestones,
    }
    return _realizar_peticion('POST', '/campanas', json=cuerpo_de_la_peticion).json()


def upsert_evento_de_campana(id_campana: int, codigo_evento: str, fecha: str) -> dict:
    """Captura o corrige la fecha de un hito FDA para una campaña.

    Args:
        id_campana: campaña a la que pertenece el hito.
        codigo_evento: slug del evento en el catálogo (ver `list_eventos`).
        fecha: fecha en formato ISO 8601.

    Returns:
        Dict con `id_evento`, `codigo`, `nombre`, `fecha` y `actualizado_en`.
    """
    return _realizar_peticion('PUT', f'/campanas/{id_campana}/eventos/{codigo_evento}', json={'fecha': fecha}).json()


def crear_configuracion(
    nombre: str,
    porcentaje_fin: float,
    porcentaje_inicio: float,
    porcentaje_bloque_minimo: float,
    hueco_entregas_dias: float,
    desfase_rescate_dias: float,
    cobertura_aviso: float,
) -> dict:
    """Crea una combinación nueva de parámetros de la Metodología, la marca vigente, y
    encola el recálculo de todas las campañas.

    Esta es la única función de este módulo que dispara un trabajo global — cada
    llamada recalcula el snapshot de todas las campañas ya dadas de alta, no solo
    una. La página de Metodología solo debe llamarla tras una confirmación
    explícita del usuario (ver spec de diseño, sección 3).

    Args:
        nombre: nombre descriptivo de la combinación, por ejemplo
            `'Metodología (ajuste percentil fin, 2026-09-09)'`.
        porcentaje_fin: corte de percentil que marca el fin de la campaña (0-1).
        porcentaje_inicio: corte de percentil que marca el inicio de la campaña (0-1).
        porcentaje_bloque_minimo: proporción mínima de un bloque de entregas (0-1).
        hueco_entregas_dias: días de hueco permitido entre entregas.
        desfase_rescate_dias: desfase en días para el rescate de datos.
        cobertura_aviso: corte de percentil de cobertura para el aviso (0-1).

    Returns:
        Dict `{'configuracion': dict, 'id_lote': str, 'total_campanas': int}`.
    """
    cuerpo_de_la_peticion = {
        'nombre': nombre,
        'porcentaje_fin': porcentaje_fin,
        'porcentaje_inicio': porcentaje_inicio,
        'porcentaje_bloque_minimo': porcentaje_bloque_minimo,
        'hueco_entregas_dias': hueco_entregas_dias,
        'desfase_rescate_dias': desfase_rescate_dias,
        'cobertura_aviso': cobertura_aviso,
    }
    return _realizar_peticion('POST', '/configuracion', json=cuerpo_de_la_peticion).json()


def reintentar_job(id_job: int) -> dict:
    """Reencola manualmente un job fallido, creando una fila y una tarea nuevas.

    Args:
        id_job: job fallido a reintentar.

    Returns:
        Dict con el nuevo job, en estado `'pendiente'`.
    """
    return _realizar_peticion('POST', f'/jobs/{id_job}/reintentar').json()
