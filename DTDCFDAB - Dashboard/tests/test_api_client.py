"""Tests de api_client.py contra requests.request mockeado (sin red real)."""

import pytest

import api_client
import config


class _RespuestaFalsa:
    """Sustituye a requests.Response en los tests de api_client."""

    def __init__(self, datos_json=None, status_code=200):
        self._datos_json = datos_json
        self.status_code = status_code

    def json(self):
        return self._datos_json

    def raise_for_status(self):
        if self.status_code >= 400:
            error = api_client.requests.HTTPError(f'status {self.status_code}')
            error.response = self
            raise error


def _configurar_secrets(monkeypatch):
    monkeypatch.setattr(
        config.st,
        'secrets',
        {'api_base_url': 'https://dtdc-fda-buho-api.example.com', 'api_key': 'llave-de-prueba'},
    )


def test_realizar_peticion_manda_header_de_api_key(monkeypatch):
    _configurar_secrets(monkeypatch)
    peticiones_capturadas = []

    def peticion_falsa(metodo, url, headers=None, timeout=None, **kwargs):
        peticiones_capturadas.append({'metodo': metodo, 'url': url, 'headers': headers})
        return _RespuestaFalsa({'ok': True})

    monkeypatch.setattr(api_client.requests, 'request', peticion_falsa)

    api_client._realizar_peticion('GET', '/eventos')

    assert peticiones_capturadas[0]['metodo'] == 'GET'
    assert peticiones_capturadas[0]['url'] == 'https://dtdc-fda-buho-api.example.com/eventos'
    assert peticiones_capturadas[0]['headers']['X-API-Key'] == 'llave-de-prueba'


def test_realizar_peticion_reintenta_en_500_y_despues_tiene_exito(monkeypatch):
    _configurar_secrets(monkeypatch)
    respuestas_por_intento = [_RespuestaFalsa(status_code=500), _RespuestaFalsa({'ok': True})]

    monkeypatch.setattr(
        api_client.requests, 'request', lambda metodo, url, headers=None, timeout=None, **kwargs: respuestas_por_intento.pop(0)
    )
    monkeypatch.setattr(api_client.time, 'sleep', lambda segundos: None)

    respuesta = api_client._realizar_peticion('GET', '/eventos')

    assert respuesta.json() == {'ok': True}


def test_realizar_peticion_agota_reintentos_en_500_persistente(monkeypatch):
    _configurar_secrets(monkeypatch)
    monkeypatch.setattr(
        api_client.requests, 'request', lambda metodo, url, headers=None, timeout=None, **kwargs: _RespuestaFalsa(status_code=500)
    )
    monkeypatch.setattr(api_client.time, 'sleep', lambda segundos: None)

    with pytest.raises(RuntimeError, match='falló tras 3 intentos'):
        api_client._realizar_peticion('GET', '/eventos')


def test_realizar_peticion_reintenta_en_timeout_y_despues_tiene_exito(monkeypatch):
    _configurar_secrets(monkeypatch)
    llamadas = {'numero': 0}

    def peticion_falsa(metodo, url, headers=None, timeout=None, **kwargs):
        llamadas['numero'] += 1
        if llamadas['numero'] == 1:
            raise api_client.requests.exceptions.Timeout()
        return _RespuestaFalsa({'ok': True})

    monkeypatch.setattr(api_client.requests, 'request', peticion_falsa)
    monkeypatch.setattr(api_client.time, 'sleep', lambda segundos: None)

    respuesta = api_client._realizar_peticion('GET', '/eventos')

    assert respuesta.json() == {'ok': True}


def test_realizar_peticion_lanza_permission_error_en_401(monkeypatch):
    _configurar_secrets(monkeypatch)
    monkeypatch.setattr(api_client.requests, 'request', lambda *args, **kwargs: _RespuestaFalsa(status_code=401))

    with pytest.raises(PermissionError):
        api_client._realizar_peticion('GET', '/eventos')


def test_realizar_peticion_lanza_runtime_error_en_429(monkeypatch):
    _configurar_secrets(monkeypatch)
    monkeypatch.setattr(api_client.requests, 'request', lambda *args, **kwargs: _RespuestaFalsa(status_code=429))

    with pytest.raises(RuntimeError, match='Límite de peticiones'):
        api_client._realizar_peticion('GET', '/eventos')


def test_realizar_peticion_lanza_http_error_en_400_sin_reintentar(monkeypatch):
    _configurar_secrets(monkeypatch)
    numero_de_llamadas = {'total': 0}

    def peticion_falsa(metodo, url, headers=None, timeout=None, **kwargs):
        numero_de_llamadas['total'] += 1
        return _RespuestaFalsa(status_code=400)

    monkeypatch.setattr(api_client.requests, 'request', peticion_falsa)

    with pytest.raises(api_client.requests.HTTPError):
        api_client._realizar_peticion('GET', '/eventos')
    assert numero_de_llamadas['total'] == 1


def test_list_eventos_pide_get_a_eventos(monkeypatch):
    monkeypatch.setattr(api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: _RespuestaFalsa([{'codigo': 'arte'}]))
    assert api_client.list_eventos() == [{'codigo': 'arte'}]


def test_list_campanas_retool_pide_get_a_campanas_retool(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa([])
    )
    api_client.list_campanas_retool()
    assert rutas_capturadas == ['/campanas/retool']


def test_list_campanas_pide_get_a_campanas(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa([])
    )
    api_client.list_campanas()
    assert rutas_capturadas == ['/campanas']


def test_list_eventos_de_campana_pide_ruta_con_id(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa([])
    )
    api_client.list_eventos_de_campana(7)
    assert rutas_capturadas == ['/campanas/7/eventos']


def test_get_snapshot_de_campana_retorna_none_en_404(monkeypatch):
    def _realizar_peticion_falsa(metodo, ruta, **kwargs):
        _RespuestaFalsa(status_code=404).raise_for_status()

    monkeypatch.setattr(api_client, '_realizar_peticion', _realizar_peticion_falsa)
    assert api_client.get_snapshot_de_campana(1) is None


def test_get_snapshot_de_campana_retorna_datos_cuando_existe(monkeypatch):
    monkeypatch.setattr(api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: _RespuestaFalsa({'numero_envios': 10}))
    assert api_client.get_snapshot_de_campana(1) == {'numero_envios': 10}


def test_get_ultimo_job_de_campana_pide_ruta_con_id(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa({})
    )
    api_client.get_ultimo_job_de_campana(3)
    assert rutas_capturadas == ['/campanas/3/job']


def test_get_configuracion_vigente_pide_get_a_configuracion_vigente(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa({})
    )
    api_client.get_configuracion_vigente()
    assert rutas_capturadas == ['/configuracion/vigente']


def test_list_historial_configuracion_pide_get_a_configuracion(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa([])
    )
    api_client.list_historial_configuracion()
    assert rutas_capturadas == ['/configuracion']


def test_list_snapshots_vigentes_pide_parametro_vigente_true(monkeypatch):
    parametros_capturados = {}

    def _realizar_peticion_falsa(metodo, ruta, **kwargs):
        parametros_capturados.update(kwargs.get('params', {}))
        return _RespuestaFalsa([])

    monkeypatch.setattr(api_client, '_realizar_peticion', _realizar_peticion_falsa)
    api_client.list_snapshots_vigentes()
    assert parametros_capturados == {'vigente': 'true'}


def test_get_job_pide_ruta_con_id(monkeypatch):
    rutas_capturadas = []
    monkeypatch.setattr(
        api_client, '_realizar_peticion', lambda metodo, ruta, **kwargs: rutas_capturadas.append(ruta) or _RespuestaFalsa({})
    )
    api_client.get_job(5)
    assert rutas_capturadas == ['/jobs/5']


def test_list_jobs_de_lote_pide_parametro_id_lote(monkeypatch):
    parametros_capturados = {}

    def _realizar_peticion_falsa(metodo, ruta, **kwargs):
        parametros_capturados.update(kwargs.get('params', {}))
        return _RespuestaFalsa([])

    monkeypatch.setattr(api_client, '_realizar_peticion', _realizar_peticion_falsa)
    api_client.list_jobs_de_lote('lote-1')
    assert parametros_capturados == {'id_lote': 'lote-1'}
