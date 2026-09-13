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
    """Días desde `inicio_carga_artes` hasta el inicio de cada etapa.

    Args:
        snapshot: diccionario con los campos de `SnapshotOut`.

    Returns:
        Dict con el offset en días por etapa, o `None` si falta la fecha base
        o la de inicio de esa etapa.
    """
    base = _parsear_fecha(snapshot.get(_CLAVE_BASE_DE_OFFSET))
    resultado = {}
    for nombre_etapa, clave_inicio, _ in charts.ETAPAS:
        inicio = _parsear_fecha(snapshot.get(clave_inicio))
        resultado[nombre_etapa] = round((inicio - base).total_seconds() / 86400, 2) if base and inicio else None
    return resultado


def calcular_offset_promedio(snapshots: list[dict]) -> dict[str, float | None]:
    """Promedio de offset por etapa entre varios snapshots.

    Args:
        snapshots: lista de diccionarios `SnapshotOut`, una por campaña.

    Returns:
        Dict con el offset promedio en días por etapa, o `None` si ninguna
        campaña tiene ese dato.
    """
    offsets_por_etapa = {nombre: [] for nombre, _, _ in charts.ETAPAS}
    for snapshot in snapshots:
        for nombre_etapa, offset in calcular_offset_por_etapa(snapshot).items():
            if offset is not None:
                offsets_por_etapa[nombre_etapa].append(offset)
    return {
        nombre: round(sum(valores) / len(valores), 2) if valores else None
        for nombre, valores in offsets_por_etapa.items()
    }


def calcular_offset_vs_promedio(snapshot: dict, snapshots: list[dict]) -> dict[str, tuple[float, float] | None]:
    """Offset real de una campaña vs. el promedio histórico, por etapa.

    Args:
        snapshot: snapshot de la campaña a analizar.
        snapshots: snapshots de todas las campañas, para calcular el promedio.

    Returns:
        Dict con `(offset_real, delta)` por etapa. `None` si falta el dato
        real o el promedio de esa etapa.
    """
    promedios = calcular_offset_promedio(snapshots)
    offsets = calcular_offset_por_etapa(snapshot)
    resultado = {}
    for nombre_etapa, offset in offsets.items():
        promedio = promedios[nombre_etapa]
        if offset is not None and promedio is not None:
            resultado[nombre_etapa] = (offset, round(offset - promedio, 2))
        else:
            resultado[nombre_etapa] = None
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
