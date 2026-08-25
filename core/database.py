"""Database setup and SQLAlchemy session helpers."""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from core.config import settings


class Base(DeclarativeBase):
    """Base class for all persisted entities."""


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for a request or task."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    """Create v1 database tables when they do not yet exist."""
    from core import models  # noqa: F401
    Base.metadata.create_all(engine)
