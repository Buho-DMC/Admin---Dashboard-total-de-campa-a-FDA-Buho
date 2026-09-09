import os
import ssl

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        host = os.environ["MYSQL_HOST_DMC_GENERAL"]
        port = os.environ["MYSQL_PORT_DMC_GENERAL"]
        user = os.environ["MYSQL_USER_DMC_GENERAL"]
        password = os.environ["MYSQL_PASSWORD_DMC_GENERAL"]
        db = os.environ["MYSQL_DB_DMC_GENERAL"]

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        _engine = create_engine(
            url,
            connect_args={"ssl": ctx},
            pool_pre_ping=True,
        )
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()
