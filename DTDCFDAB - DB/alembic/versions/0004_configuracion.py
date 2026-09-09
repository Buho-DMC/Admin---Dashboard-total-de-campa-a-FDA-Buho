"""Crea dtdcfdab_configuracion, fuerza una sola fila vigente, y siembra Politica D."""

import sqlalchemy as sa

from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

SEMILLA_POLITICA_D = {
    'nombre': 'Politica D (etl.ipynb, 2026-09-04)',
    'porcentaje_fin': '0.9900',
    'porcentaje_inicio': '0.0100',
    'porcentaje_bloque_minimo': '0.0500',
    'hueco_entregas_dias': '10.00',
    'desfase_rescate_dias': '0.622',
    'cobertura_aviso': '0.9500',
    'es_vigente': True,
}


def upgrade() -> None:
    """Crea dtdcfdab_configuracion, fuerza una sola fila vigente, y siembra Politica D."""
    op.create_table(
        'dtdcfdab_configuracion',
        sa.Column('id_configuracion', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(255), nullable=True),
        sa.Column('porcentaje_fin', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('porcentaje_inicio', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('porcentaje_bloque_minimo', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('hueco_entregas_dias', sa.DECIMAL(6, 2), nullable=False),
        sa.Column('desfase_rescate_dias', sa.DECIMAL(6, 3), nullable=False),
        sa.Column('cobertura_aviso', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('es_vigente', sa.Boolean, nullable=False, server_default=sa.text('0')),
        sa.Column('creado_en', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        mysql_engine='InnoDB',
    )

    # MySQL no tiene indices unicos parciales (WHERE es_vigente) como Postgres.
    # Columna generada: NULL si es_vigente=0, 1 si es_vigente=1 -> el indice
    # unico permite muchos NULL pero solo un 1, forzando una sola fila vigente.
    op.execute(
        'ALTER TABLE dtdcfdab_configuracion '
        'ADD COLUMN vigente_unico TINYINT '
        'GENERATED ALWAYS AS (IF(es_vigente = 1, 1, NULL)) VIRTUAL, '
        'ADD UNIQUE INDEX ux_configuracion_vigente_unico (vigente_unico)'
    )

    op.bulk_insert(
        sa.table(
            'dtdcfdab_configuracion',
            sa.column('nombre', sa.String),
            sa.column('porcentaje_fin', sa.DECIMAL),
            sa.column('porcentaje_inicio', sa.DECIMAL),
            sa.column('porcentaje_bloque_minimo', sa.DECIMAL),
            sa.column('hueco_entregas_dias', sa.DECIMAL),
            sa.column('desfase_rescate_dias', sa.DECIMAL),
            sa.column('cobertura_aviso', sa.DECIMAL),
            sa.column('es_vigente', sa.Boolean),
        ),
        [SEMILLA_POLITICA_D],
    )


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_configuracion."""
    op.drop_table('dtdcfdab_configuracion')
