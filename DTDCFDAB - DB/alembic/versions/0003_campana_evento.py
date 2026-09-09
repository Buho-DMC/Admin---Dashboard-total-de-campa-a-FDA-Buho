"""Crea dtdcfdab_campana_evento."""

import sqlalchemy as sa

from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla dtdcfdab_campana_evento con PK compuesta (id_campana, id_evento)."""
    op.create_table(
        'dtdcfdab_campana_evento',
        sa.Column('id_campana', sa.Integer, sa.ForeignKey('dtdcfdab_campana.id_campana'), primary_key=True),
        sa.Column('id_evento', sa.Integer, sa.ForeignKey('dtdcfdab_evento.id_evento'), primary_key=True),
        sa.Column('fecha', sa.DateTime, nullable=False),
        sa.Column(
            'actualizado_en',
            sa.DateTime,
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            server_onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        mysql_engine='InnoDB',
    )


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_campana_evento."""
    op.drop_table('dtdcfdab_campana_evento')
