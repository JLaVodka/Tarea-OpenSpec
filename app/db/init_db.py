"""Inicializa el esquema relacional del prototipo desde la configuración vigente."""

from app.db.base import Base
import app.db.models  # noqa: F401 - registra las entidades en metadata
from app.db.session import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("Esquema de reservas inicializado correctamente.")


if __name__ == "__main__":
    main()
