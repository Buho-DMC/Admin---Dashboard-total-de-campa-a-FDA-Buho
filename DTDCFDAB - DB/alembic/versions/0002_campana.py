"""Crea dtdcfdab_campana."""

import sqlalchemy as sa

from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla dtdcfdab_campana."""
    op.create_table(
        'dtdcfdab_campana',
        sa.Column('id_campana', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('id_claw', sa.Integer, nullable=False, unique=True),
        sa.Column('cliente', sa.String(32), nullable=False, server_default='FDA'),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('inicio_campana', sa.DateTime, nullable=False),
        sa.Column('fecha_alta', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        mysql_engine='InnoDB',
    )


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_campana."""
    op.drop_table('dtdcfdab_campana')
