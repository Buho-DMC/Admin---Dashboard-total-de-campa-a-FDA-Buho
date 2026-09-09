from dtdcfdab_db.db import get_engine
from sqlalchemy import text


def test_conexion_real():
    engine = get_engine()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
    assert version is not None
    print(f"MySQL version: {version}")
