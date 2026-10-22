"""Entidades persistidas para solicitudes de reserva y su auditoría."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReservationStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("starts_at < ends_at", name="positive_interval"),
        Index("ix_reservations_space_status_interval", "space_id", "status", "starts_at", "ends_at"),
        Index("ix_reservations_requester_created_at", "requester_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        SqlEnum(
            ReservationStatus,
            native_enum=False,
            length=20,
            create_constraint=True,
            name="reservation_status",
        ),
        nullable=False,
        default=ReservationStatus.PENDIENTE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    requester: Mapped["User"] = relationship(back_populates="reservations")
    space: Mapped["Space"] = relationship(back_populates="reservations")
    events: Mapped[list["ReservationEvent"]] = relationship(
        back_populates="reservation", passive_deletes="all"
    )


class ReservationEvent(Base):
    __tablename__ = "reservation_events"
    __table_args__ = (Index("ix_reservation_events_reservation_occurred", "reservation_id", "occurred_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), nullable=False
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    reservation: Mapped[Reservation] = relationship(back_populates="events")
