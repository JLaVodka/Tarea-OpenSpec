"""Importa todas las entidades para registrar el esquema de SQLAlchemy."""

from app.reservations.models import Reservation, ReservationEvent, ReservationStatus
from app.roles.models import Permission, Role
from app.spaces.models import Space
from app.users.models import User

__all__ = [
    "Permission",
    "Reservation",
    "ReservationEvent",
    "ReservationStatus",
    "Role",
    "Space",
    "User",
]
