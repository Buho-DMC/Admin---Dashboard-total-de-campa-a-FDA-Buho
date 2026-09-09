"""Crea dtdcfdab_job_ejecucion."""

import sqlalchemy as sa

from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla dtdcfdab_job_ejecucion."""
    op.create_table(
        'dtdcfdab_job_ejecucion',
        sa.Column('id_job_ejecucion', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('id_campana', sa.Integer, sa.ForeignKey('dtdcfdab_campana.id_campana'), nullable=False),
        sa.Column('id_lote', sa.String(36), nullable=True),
        sa.Column(
            'id_configuracion',
            sa.Integer,
            sa.ForeignKey('dtdcfdab_configuracion.id_configuracion'),
            nullable=False,
        ),
        sa.Column('tipo', sa.String(16), nullable=False),
        sa.Column('estado', sa.String(16), nullable=False, server_default='pendiente'),
        sa.Column('iniciado_en', sa.DateTime, nullable=True),
        sa.Column('terminado_en', sa.DateTime, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.CheckConstraint("tipo IN ('alta','recalculo')", name='ck_job_tipo'),
        sa.CheckConstraint("estado IN ('pendiente','corriendo','exitoso','fallido')", name='ck_job_estado'),
        mysql_engine='InnoDB',
    )
    op.create_index('ix_job_ejecucion_id_lote', 'dtdcfdab_job_ejecucion', ['id_lote'])


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_job_ejecucion."""
    op.drop_table('dtdcfdab_job_ejecucion')
