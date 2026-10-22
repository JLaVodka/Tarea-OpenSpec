"""Creación del motor y sesiones transaccionales SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_database_engine(database_url: str, *, echo: bool = False) -> Engine:
    """Crea un motor y habilita claves foráneas en conexiones SQLite."""
    url = make_url(database_url)
    connect_args = {"check_same_thread": False} if url.get_backend_name() == "sqlite" else {}
    engine = create_engine(database_url, echo=echo, connect_args=connect_args)

    if url.get_backend_name() == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión por solicitud y la cierra al terminar."""
    with SessionLocal() as session:
        yield session
