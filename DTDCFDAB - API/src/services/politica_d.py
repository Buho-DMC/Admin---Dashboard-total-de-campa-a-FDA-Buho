"""Política D: 14 fechas Búho + 13 metadatos por (campaña, configuración).

Pendiente de portar desde etl.ipynb / AUDITORIA_ETL.txt (repo "[Direccion] Reporte proceso total
de campana", no leído en esta sesión) — ver Pendientes explícitos en
docs/superpowers/specs/2026-09-08-api-design.md. Requiere además las credenciales de Claw
(CLAW_BASE_URL_PICKS, CLAW_BASE_URL_TRACKING, CLAW_API_KEY), aún sin confirmar.
"""


def calcular(id_claw: int, configuracion: dict, claw_picks_client, claw_tracking_client, retool_engine) -> dict:
    """Calcula las 14 fechas Búho + 13 metadatos de una campaña (Política D).

    Args:
        id_claw: id de la campaña en Claw.
        configuracion: los 6 parámetros del método (`porcentaje_fin`, etc.).
        claw_picks_client: cliente HTTP de Pick & Pack (ver `clients.get_claw_picks_client`).
        claw_tracking_client: cliente HTTP de Entregas (ver `clients.get_claw_tracking_client`).
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
