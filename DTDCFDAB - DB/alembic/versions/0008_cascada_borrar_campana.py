"""Agrega ON DELETE CASCADE a las FKs hacia dtdcfdab_campana.id_campana.

Permite que la API borre una campaña con un solo DELETE sobre
dtdcfdab_campana — MySQL se encarga de limpiar sus hitos, snapshot y jobs
en dtdcfdab_campana_evento, dtdcfdab_campana_snapshot y
dtdcfdab_job_ejecucion. Los nombres de las FKs se descubren en tiempo de
ejecución (sqlalchemy.inspect) en vez de hardcodearse: no hay
naming_convention configurado en este proyecto, así que MySQL les puso
nombres autogenerados (`..._ibfk_N`) que no se pueden adivinar de forma
confiable sin consultar el esquema real.
"""

import sqlalchemy as sa

from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

TABLAS_CON_FK_HACIA_CAMPANA = ['dtdcfdab_campana_evento', 'dtdcfdab_campana_snapshot', 'dtdcfdab_job_ejecucion']


def _fk_hacia_campana(inspector: sa.Inspector, tabla: str) -> dict:
    """Encuentra, entre las FKs de `tabla`, la que apunta a dtdcfdab_campana.id_campana.

    Args:
        inspector: inspector de SQLAlchemy sobre la conexión activa de la migración.
        tabla: nombre de la tabla a inspeccionar.

    Returns:
        Dict de `Inspector.get_foreign_keys` para esa FK — trae al menos
        `name` (el nombre real en MySQL) y `constrained_columns`.
    """
    return next(
        foreign_key
        for foreign_key in inspector.get_foreign_keys(tabla)
        if foreign_key['referred_table'] == 'dtdcfdab_campana'
    )


def upgrade() -> None:
    """Recrea cada FK hacia dtdcfdab_campana.id_campana con ondelete='CASCADE'."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    for tabla in TABLAS_CON_FK_HACIA_CAMPANA:
        fk = _fk_hacia_campana(inspector, tabla)
        op.drop_constraint(fk['name'], tabla, type_='foreignkey')
        op.create_foreign_key(
            fk['name'], tabla, 'dtdcfdab_campana', fk['constrained_columns'], ['id_campana'], ondelete='CASCADE'
        )


def downgrade() -> None:
    """Recrea cada FK sin cascada, como estaba antes de esta migración."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    for tabla in TABLAS_CON_FK_HACIA_CAMPANA:
        fk = _fk_hacia_campana(inspector, tabla)
        op.drop_constraint(fk['name'], tabla, type_='foreignkey')
        op.create_foreign_key(fk['name'], tabla, 'dtdcfdab_campana', fk['constrained_columns'], ['id_campana'])
