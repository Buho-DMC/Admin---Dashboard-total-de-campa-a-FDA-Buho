"""Crea dtdcfdab_campana_snapshot (14 fechas Buho + 13 metadatos)."""

import sqlalchemy as sa

from alembic import op

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

COLUMNAS_FECHA = [
    'inicio_carga_artes', 'fin_carga_artes',
    'inicio_carga_preproyectos', 'fin_carga_preproyectos',
    'inicio_aprobaciones', 'fin_aprobaciones',
    'inicio_impresion', 'fin_impresion',
    'inicio_precampana', 'fin_precampana',
    'inicio_pick_pack', 'fin_pick_pack',
    'inicio_entregas', 'fin_entregas',
]


def upgrade() -> None:
    """Crea la tabla dtdcfdab_campana_snapshot."""
    columnas = [
        sa.Column('id_campana', sa.Integer, sa.ForeignKey('dtdcfdab_campana.id_campana'), primary_key=True),
        sa.Column(
            'id_configuracion',
            sa.Integer,
            sa.ForeignKey('dtdcfdab_configuracion.id_configuracion'),
            primary_key=True,
        ),
    ]
    columnas += [sa.Column(nombre_columna, sa.DateTime, nullable=True) for nombre_columna in COLUMNAS_FECHA]
    columnas += [
        sa.Column('porcentaje_alcanzado_entregas', sa.DECIMAL(9, 6), nullable=True),
        sa.Column('ultima_entrega', sa.DateTime, nullable=True),
        sa.Column('numero_envios', sa.Integer, nullable=True),
        sa.Column('envios_con_fecha', sa.Integer, nullable=True),
        sa.Column('envios_sin_fecha', sa.Integer, nullable=True),
        sa.Column('envios_sin_registro_entrega', sa.Integer, nullable=True),
        sa.Column('numero_cajas_pick_pack', sa.Integer, nullable=True),
        sa.Column('numero_folios', sa.Integer, nullable=True),
        sa.Column('numero_odps', sa.Integer, nullable=True),
        sa.Column('numero_actividades', sa.Integer, nullable=True),
        sa.Column('respuesta_buho_dias', sa.DECIMAL(9, 4), nullable=True),
        sa.Column('respuesta_fda_dias', sa.DECIMAL(9, 4), nullable=True),
        sa.Column('folios_invertidos', sa.Integer, nullable=True),
        sa.Column('calculado_en', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    ]
    op.create_table('dtdcfdab_campana_snapshot', *columnas, mysql_engine='InnoDB')


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_campana_snapshot."""
    op.drop_table('dtdcfdab_campana_snapshot')
