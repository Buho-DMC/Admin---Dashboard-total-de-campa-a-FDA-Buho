"""Agrega distribucion_percentiles (JSON nullable) a dtdcfdab_campana_snapshot.

Almacena la curva de cuantiles de inicio (0.1% a 10.0%) y de fin (90.1% a 100.0%)
para las 7 etapas de la campaña, permitiendo interacción fluida con sliders
en el Dashboard sin recalcular en backend.
"""

import sqlalchemy as sa
from alembic import op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade la columna JSON nullable distribucion_percentiles a dtdcfdab_campana_snapshot."""
    op.add_column(
        'dtdcfdab_campana_snapshot',
        sa.Column('distribucion_percentiles', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Elimina la columna distribucion_percentiles de dtdcfdab_campana_snapshot."""
    op.drop_column('dtdcfdab_campana_snapshot', 'distribucion_percentiles')
