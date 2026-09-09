"""Política D: 14 fechas Búho + 13 metadatos por (campaña, configuración).

Pendiente de portar desde etl.ipynb / AUDITORIA_ETL.txt (repo "[Direccion] Reporte proceso total
de campana", no leído en esta sesión) — ver Pendientes explícitos en
docs/superpowers/specs/2026-09-08-api-design.md. Requiere además las credenciales de Claw
(API_KEY_CLAW, API_BASE_URL_CLAW), ya confirmadas — ver `clients.get_claw_client`.
"""


def calcular(id_claw: int, configuracion: dict, claw_client, retool_engine) -> dict:
    """Calcula las 14 fechas Búho + 13 metadatos de una campaña (Política D).

    Args:
        id_claw: id de la campaña en Claw.
        configuracion: los 6 parámetros del método (`porcentaje_fin`, etc.).
        claw_client: cliente HTTP hacia Claw (ver `clients.get_claw_client`) — quien
            implemente esta función arma la ruta de Pick & Pack
            (`/campaign/picks/{id_claw}`) y de Entregas (`/distribution/tracking/{id_claw}`)
            con este mismo cliente.
        retool_engine: engine hacia Retool DB (Postgres) — todavía sin definir cómo se obtiene.

    Returns:
        Dict con las columnas del snapshot (ver "Esquema asumido" de este plan) —
        cuando esté implementado.

    Raises:
        NotImplementedError: siempre, hasta que se porte la lógica real desde `etl.ipynb`.
    """
    raise NotImplementedError(
        'Politica D pendiente de portar desde etl.ipynb — ver Pendientes explicitos en '
        'docs/superpowers/specs/2026-09-08-api-design.md'
    )
