"""Análisis de fechas de una campaña vs. el promedio histórico de todas las campañas.

Adaptado de `calcular_kpis`/`calcular_duracion_vs_promedio`/`calcular_offsets_promedio`/
`calcular_offset_vs_promedio`/`mostrar_analisis_por_campaña` del proyecto legacy
(`[Direccion] Reporte proceso total de campaña/main.py`), pero operando sobre los 7 pares
inicio/fin de `SnapshotOut` en vez de las columnas de hitos crudos del Google Sheet legacy.
"""

from datetime import datetime

import charts

_CLAVE_BASE_DE_OFFSET = 'inicio_carga_artes'


def _parsear_fecha(valor_iso: str | None) -> datetime | None:
    """Convierte una fecha ISO 8601 a `datetime`, o `None` si falta o es inválida."""
    if not valor_iso:
        return None
    try:
        return datetime.fromisoformat(valor_iso)
    except (ValueError, TypeError):
        return None


def calcular_duracion_por_etapa(snapshot: dict) -> dict[str, float | None]:
    """Días de duración (fin - inicio) de cada etapa de un snapshot.

    Args:
        snapshot: diccionario con los campos de `SnapshotOut`.

    Returns:
        Dict con el nombre de cada etapa de `charts.ETAPAS` como llave, y su
        duración en días (o `None` si falta la fecha de inicio o de fin).
    """
    resultado = {}
    for nombre_etapa, clave_inicio, clave_fin in charts.ETAPAS:
        inicio = _parsear_fecha(snapshot.get(clave_inicio))
        fin = _parsear_fecha(snapshot.get(clave_fin))
        resultado[nombre_etapa] = round((fin - inicio).total_seconds() / 86400, 2) if inicio and fin else None
    return resultado


def calcular_duracion_promedio(snapshots: list[dict]) -> dict[str, float | None]:
    """Promedio de duración por etapa entre varios snapshots.

    Args:
        snapshots: lista de diccionarios `SnapshotOut`, una por campaña.

    Returns:
        Dict con el promedio en días por etapa, o `None` si ninguna campaña
        tiene ambas fechas de esa etapa.
    """
    duraciones_por_etapa = {nombre: [] for nombre, _, _ in charts.ETAPAS}
    for snapshot in snapshots:
        for nombre_etapa, duracion in calcular_duracion_por_etapa(snapshot).items():
            if duracion is not None:
                duraciones_por_etapa[nombre_etapa].append(duracion)
    return {
        nombre: round(sum(valores) / len(valores), 2) if valores else None
        for nombre, valores in duraciones_por_etapa.items()
    }


def calcular_duracion_vs_promedio(snapshot: dict, snapshots: list[dict]) -> dict[str, tuple[float, float] | None]:
    """Duración real de una campaña vs. el promedio histórico, por etapa.

    Args:
        snapshot: snapshot de la campaña a analizar.
        snapshots: snapshots de todas las campañas, para calcular el promedio.

    Returns:
        Dict con `(duracion_real, delta)` por etapa — delta negativo significa
        que esta campaña fue más rápida que el promedio. `None` si falta el
        dato real o el promedio de esa etapa.
    """
    promedios = calcular_duracion_promedio(snapshots)
    duraciones = calcular_duracion_por_etapa(snapshot)
    resultado = {}
    for nombre_etapa, duracion in duraciones.items():
        promedio = promedios[nombre_etapa]
        if duracion is not None and promedio is not None:
            resultado[nombre_etapa] = (duracion, round(duracion - promedio, 2))
        else:
            resultado[nombre_etapa] = None
    return resultado


def calcular_offset_por_etapa(snapshot: dict) -> dict[str, float | None]:
    """Días desde `inicio_carga_artes` hasta el inicio y el fin de cada etapa.

    Args:
        snapshot: diccionario con los campos de `SnapshotOut`.

    Returns:
        Dict con `'Inicio <etapa>'` y `'Fin <etapa>'` como llave por cada etapa de
        `charts.ETAPAS`, y su offset en días — o `None` si falta la fecha base o esa
        fecha en particular.
    """
    base = _parsear_fecha(snapshot.get(_CLAVE_BASE_DE_OFFSET))
    resultado = {}
    for nombre_etapa, clave_inicio, clave_fin in charts.ETAPAS:
        inicio = _parsear_fecha(snapshot.get(clave_inicio))
        fin = _parsear_fecha(snapshot.get(clave_fin))
        resultado[f'Inicio {nombre_etapa}'] = round((inicio - base).total_seconds() / 86400, 2) if base and inicio else None
        resultado[f'Fin {nombre_etapa}'] = round((fin - base).total_seconds() / 86400, 2) if base and fin else None
    return resultado


def calcular_offset_promedio(snapshots: list[dict]) -> dict[str, float | None]:
    """Promedio de offset por etiqueta (inicio/fin de etapa) entre varios snapshots.

    Args:
        snapshots: lista de diccionarios `SnapshotOut`, una por campaña.

    Returns:
        Dict con el offset promedio en días por `'Inicio <etapa>'`/`'Fin <etapa>'`,
        o `None` si ninguna campaña tiene ese dato.
    """
    etiquetas = [f'{prefijo} {nombre}' for nombre, _, _ in charts.ETAPAS for prefijo in ('Inicio', 'Fin')]
    offsets_por_etiqueta = {etiqueta: [] for etiqueta in etiquetas}
    for snapshot in snapshots:
        for etiqueta, offset in calcular_offset_por_etapa(snapshot).items():
            if offset is not None:
                offsets_por_etiqueta[etiqueta].append(offset)
    return {
        etiqueta: round(sum(valores) / len(valores), 2) if valores else None
        for etiqueta, valores in offsets_por_etiqueta.items()
    }


def calcular_offset_vs_promedio(snapshot: dict, snapshots: list[dict]) -> dict[str, tuple[float, float] | None]:
    """Offset real de una campaña vs. el promedio histórico, por inicio/fin de etapa.

    Args:
        snapshot: snapshot de la campaña a analizar.
        snapshots: snapshots de todas las campañas, para calcular el promedio.

    Returns:
        Dict con `(offset_real, delta)` por `'Inicio <etapa>'`/`'Fin <etapa>'`. `None`
        si falta el dato real o el promedio de esa etiqueta.
    """
    promedios = calcular_offset_promedio(snapshots)
    offsets = calcular_offset_por_etapa(snapshot)
    resultado = {}
    for etiqueta, offset in offsets.items():
        promedio = promedios[etiqueta]
        if offset is not None and promedio is not None:
            resultado[etiqueta] = (offset, round(offset - promedio, 2))
        else:
            resultado[etiqueta] = None
    return resultado


def listar_fechas_ordenadas(snapshot: dict) -> list[tuple[str, datetime]]:
    """Todas las fechas de inicio/fin de un snapshot, etiquetadas y ordenadas.

    Args:
        snapshot: diccionario con los campos de `SnapshotOut`.

    Returns:
        Lista de `(etiqueta, fecha)` ordenada cronológicamente, por ejemplo
        `('Inicio Carga de artes', datetime(...))`.
    """
    eventos = []
    for nombre_etapa, clave_inicio, clave_fin in charts.ETAPAS:
        inicio = _parsear_fecha(snapshot.get(clave_inicio))
        fin = _parsear_fecha(snapshot.get(clave_fin))
        if inicio is not None:
            eventos.append((f'Inicio {nombre_etapa}', inicio))
        if fin is not None:
            eventos.append((f'Fin {nombre_etapa}', fin))
    eventos.sort(key=lambda evento: evento[1])
    return eventos


def calcular_dia_del_mes_vs_promedio(snapshot: dict, snapshots: list[dict]) -> dict[str, tuple[float, float] | None]:
    """Día del mes de cada fecha de una campaña vs. el promedio histórico, en orden cronológico.

    Args:
        snapshot: snapshot de la campaña a analizar.
        snapshots: snapshots de todas las campañas (incluida `snapshot`), para calcular el
            promedio de cada fecha.

    Returns:
        Dict con `(dia_real, delta)` por cada fecha presente en `snapshot` (`'Inicio <etapa>'` /
        `'Fin <etapa>'`), ordenado cronológicamente igual que `listar_fechas_ordenadas`. El día del
        mes se promedia de forma aritmética simple, sin ajuste de ciclo entre fin e inicio de mes.
        `None` si `snapshots` no trae ninguna campaña con esa fecha (caso defensivo — no ocurre en
        el flujo normal, donde `snapshots` siempre incluye a la campaña seleccionada).
    """
    entradas = []
    for nombre_etapa, clave_inicio, clave_fin in charts.ETAPAS:
        for etiqueta, clave in ((f'Inicio {nombre_etapa}', clave_inicio), (f'Fin {nombre_etapa}', clave_fin)):
            fecha_real = _parsear_fecha(snapshot.get(clave))
            if fecha_real is None:
                continue

            fechas_de_todas_las_campanas = [_parsear_fecha(otro.get(clave)) for otro in snapshots]
            dias_del_mes = [fecha.day for fecha in fechas_de_todas_las_campanas if fecha is not None]

            if dias_del_mes:
                promedio = round(sum(dias_del_mes) / len(dias_del_mes), 1)
                valores = (float(fecha_real.day), round(fecha_real.day - promedio, 1))
            else:
                valores = None
            entradas.append((etiqueta, fecha_real, valores))

    entradas.sort(key=lambda entrada: entrada[1])
    return {etiqueta: valores for etiqueta, _, valores in entradas}


def aplicar_percentiles_a_snapshot(
    snapshot: dict,
    percentiles_inicio: dict[str, float],
    percentiles_fin: dict[str, float],
) -> dict:
    """Ajusta en memoria las fechas de inicio y fin del snapshot según percentiles seleccionados.

    Args:
        snapshot: dict con campos de `SnapshotOut` (incluyendo `distribucion_percentiles`).
        percentiles_inicio: dict con percentil de inicio (0.1 a 10.0) por etapa (ej: {'pick_pack': 1.0}).
        percentiles_fin: dict con percentil de fin (90.1 a 100.0) por etapa (ej: {'pick_pack': 99.0}).

    Returns:
        Copia del snapshot con las fechas de inicio/fin ajustadas según la rejilla en JSON.
    """
    nuevo = dict(snapshot)
    distribucion = snapshot.get('distribucion_percentiles')
    if not distribucion or not isinstance(distribucion, dict):
        return nuevo

    mapeo_columnas = {
        'pick_pack': ('inicio_pick_pack', 'fin_pick_pack'),
        'entregas': ('inicio_entregas', 'fin_entregas'),
    }

    for etapa, (columna_inicio, columna_fin) in mapeo_columnas.items():
        if etapa in distribucion and isinstance(distribucion[etapa], dict):
            rejilla_etapa = distribucion[etapa]
            if etapa in percentiles_inicio and 'inicio' in rejilla_etapa:
                clave_inicio = f'{percentiles_inicio[etapa]:.1f}'
                if clave_inicio in rejilla_etapa['inicio'] and rejilla_etapa['inicio'][clave_inicio]:
                    nuevo[columna_inicio] = rejilla_etapa['inicio'][clave_inicio]

            if etapa in percentiles_fin and 'fin' in rejilla_etapa:
                clave_fin = f'{percentiles_fin[etapa]:.1f}'
                if clave_fin in rejilla_etapa['fin'] and rejilla_etapa['fin'][clave_fin]:
                    nuevo[columna_fin] = rejilla_etapa['fin'][clave_fin]

    return nuevo


def calcular_offset_cronologico(
    snapshot: dict, eventos_de_campana: list[dict] | None = None
) -> dict[str, tuple[float, float | None]]:
    """Calcula el offset en días desde el Día 0 (hito más temprano), ordenado cronológicamente.

    Args:
        snapshot: dict con campos de `SnapshotOut`.
        eventos_de_campana: lista opcional de hitos FDA con llaves 'nombre' y 'fecha'.

    Returns:
        Dict con `(offset_dias, None)` para cada hito y extremo de etapa presente,
        ordenado cronológicamente de forma ascendente.
    """
    entradas = []
    fechas_hitos = []

    if eventos_de_campana:
        for evento in eventos_de_campana:
            fecha_hito = _parsear_fecha(evento.get('fecha'))
            if fecha_hito is not None:
                etiqueta = evento.get('nombre') or 'Hito'
                entradas.append((etiqueta, fecha_hito))
                fechas_hitos.append(fecha_hito)

    for nombre_etapa, clave_inicio, clave_fin in charts.ETAPAS:
        inicio = _parsear_fecha(snapshot.get(clave_inicio))
        fin = _parsear_fecha(snapshot.get(clave_fin))
        if inicio is not None:
            entradas.append((f'Inicio {nombre_etapa}', inicio))
        if fin is not None:
            entradas.append((f'Fin {nombre_etapa}', fin))

    if not entradas:
        return {}

    dia_cero = min(fechas_hitos) if fechas_hitos else min(fecha for _, fecha in entradas)
    entradas.sort(key=lambda entrada: entrada[1])

    resultado = {}
    for etiqueta, fecha in entradas:
        dias = round((fecha - dia_cero).total_seconds() / 86400, 2)
        resultado[etiqueta] = (dias, None)

    return resultado

