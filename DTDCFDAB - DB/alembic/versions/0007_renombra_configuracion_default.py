"""Renombra la configuracion sembrada en 0004 a 'Default'."""

import sqlalchemy as sa

from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None

NOMBRE_ORIGINAL = 'Politica D (etl.ipynb, 2026-09-04)'
NOMBRE_NUEVO = 'Default'


def upgrade() -> None:
    """Renombra la fila sembrada en 0004 a 'Default' para dejar claro que es la propuesta inicial."""
    tabla_configuracion = sa.table('dtdcfdab_configuracion', sa.column('nombre', sa.String))
    op.execute(
        tabla_configuracion.update()
        .where(tabla_configuracion.c.nombre == NOMBRE_ORIGINAL)
        .values(nombre=NOMBRE_NUEVO)
    )


def downgrade() -> None:
    """Revierte el nombre a como quedó sembrado originalmente en 0004."""
    tabla_configuracion = sa.table('dtdcfdab_configuracion', sa.column('nombre', sa.String))
    op.execute(
        tabla_configuracion.update()
        .where(tabla_configuracion.c.nombre == NOMBRE_NUEVO)
        .values(nombre=NOMBRE_ORIGINAL)
    )
