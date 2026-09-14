from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

if settings.ytb_database_url.startswith("sqlite:///"):
    db_path = Path(settings.ytb_database_url[len("sqlite:///"):].strip())
    db_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.ytb_database_url.startswith("sqlite") else {}
engine = create_engine(settings.ytb_database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    from .models import User, Project, MediaAsset, Job
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()