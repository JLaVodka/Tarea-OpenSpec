"""Configuración de la aplicación obtenida del entorno."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./reservas.db"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(database_url=os.getenv("DATABASE_URL", "sqlite:///./reservas.db"))


settings = Settings.from_environment()
