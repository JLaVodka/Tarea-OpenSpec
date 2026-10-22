"""Esquemas HTTP para solicitudes de reserva."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.reservations.models import ReservationStatus


class ReservationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    space_id: int
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha debe incluir desplazamiento horario")
        return value


class ReservationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    space_id: int
    starts_at: datetime
    ends_at: datetime
    status: ReservationStatus

    @field_serializer("starts_at", "ends_at")
    def serialize_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AvailabilityPublic(BaseModel):
    space_id: int
    active: bool
    available: bool
