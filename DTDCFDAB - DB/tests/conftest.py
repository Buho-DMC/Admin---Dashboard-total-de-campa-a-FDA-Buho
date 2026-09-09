"""Fixture compartida por todos los tests de tablas: sesión real con rollback."""

import pytest
from sqlalchemy.orm import sessionmaker

from dtdcfdab_db.db import get_engine


@pytest.fixture
def db_session():
    """Sesión de SQLAlchemy sobre una transacción que se revierte al final del test.

    dmc-general es una base compartida con otros proyectos chicos del
    departamento — envolver cada test en una transacción que nunca se
    confirma evita dejar basura ahí, sin necesidad de mockear MySQL.

    Yields:
        Una `Session` de SQLAlchemy lista para usarse dentro de un test.
    """
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
