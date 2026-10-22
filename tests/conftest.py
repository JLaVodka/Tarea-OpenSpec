"""Fixtures compartidas para pruebas de persistencia aisladas."""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.base import Base
import app.db.models  # noqa: F401 - registra todos los modelos en metadata
from app.db.session import create_database_engine
from app.main import app
from app.db.session import get_db


@pytest.fixture
def db_session(tmp_path) -> Session:
    """Crea un archivo SQLite temporal y compartido entre hilos por prueba."""
    database_path = tmp_path / "reservas_test.db"
    test_engine = create_database_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    test_engine.dispose()


@pytest.fixture
def api_client(db_session: Session):
    """Conecta la API a la misma base temporal usada por la prueba."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
