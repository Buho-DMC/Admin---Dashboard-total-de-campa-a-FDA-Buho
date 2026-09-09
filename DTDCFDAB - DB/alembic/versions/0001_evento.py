"""Crea dtdcfdab_evento y siembra los 7 hitos FDA."""

import sqlalchemy as sa

from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

HITOS_FDA = [
    {'codigo': 'entrega_promociones_ac', 'nombre': 'Entrega Promociones Área Comercial', 'orden': 1},
    {'codigo': 'entrega_concentrado_folleto', 'nombre': 'Entrega Concentrado de Folleto Promociones', 'orden': 2},
    {'codigo': 'entrega_diagramacion_mkt', 'nombre': 'Entrega Diagramación MKT', 'orden': 3},
    {'codigo': 'cierre_comercializacion_espacios', 'nombre': 'Cierre Comercialización Espacios', 'orden': 4},
    {
        'codigo': 'entrega_diagramacion_comercializacion',
        'nombre': 'Entrega Diagramación Comercialización',
        'orden': 5,
    },
    {'codigo': 'liberacion_pop', 'nombre': 'Liberación POP', 'orden': 6},
    {'codigo': 'liberacion_folleto', 'nombre': 'Liberación Folleto', 'orden': 7},
]


def upgrade() -> None:
    """Crea la tabla dtdcfdab_evento y siembra el catálogo de 7 hitos FDA."""
    op.create_table(
        'dtdcfdab_evento',
        sa.Column('id_evento', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('codigo', sa.String(64), nullable=False, unique=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('origen', sa.String(16), nullable=False, server_default='manual'),
        sa.Column('rol', sa.String(16), nullable=False, server_default='hito'),
        sa.Column('orden', sa.Integer, nullable=False),
        sa.CheckConstraint("origen IN ('manual')", name='ck_evento_origen'),
        sa.CheckConstraint("rol IN ('hito')", name='ck_evento_rol'),
        mysql_engine='InnoDB',
    )
    op.bulk_insert(
        sa.table(
            'dtdcfdab_evento',
            sa.column('codigo', sa.String),
            sa.column('nombre', sa.String),
            sa.column('orden', sa.Integer),
        ),
        HITOS_FDA,
    )


def downgrade() -> None:
    """Elimina la tabla dtdcfdab_evento."""
    op.drop_table('dtdcfdab_evento')
