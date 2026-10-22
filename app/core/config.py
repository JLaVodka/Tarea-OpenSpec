"""Configuración de la aplicación obtenida del entorno."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./reservas.db"
    jwt_secret_key: str | None = None
    jwt_access_token_minutes: int = 30

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./reservas.db"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            jwt_access_token_minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30")),
        )


settings = Settings.from_environment()


def get_settings() -> Settings:
    """Lee configuración vigente para que secretos rotables no queden en caché."""
    return Settings.from_environment()
