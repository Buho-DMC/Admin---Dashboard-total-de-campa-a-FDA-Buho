"""Entrypoint de Alembic: conecta contra dmc-general vía get_engine() y corre las migraciones."""

import sys
from logging.config import fileConfig
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from alembic import context

from dtdcfdab_db.db import get_engine
from dtdcfdab_db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    """Aplica las migraciones directo contra la conexión real de dmc-general."""
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
