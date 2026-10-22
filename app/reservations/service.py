"""Reglas de negocio de solicitudes y disponibilidad."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.reservations.models import Reservation, ReservationStatus
from app.spaces.models import Space
from app.users.models import User


class InvalidInterval(Exception):
    """El intervalo no es futuro o no tiene duración positiva."""


class SpaceNotFound(Exception):
    """No existe el espacio solicitado."""


class SpaceInactive(Exception):
    """El espacio está inactivo."""


class ReservationConflict(Exception):
    """Una reserva aprobada o solicitud propia ya ocupa el intervalo."""


def normalize_interval(starts_at: datetime, ends_at: datetime) -> tuple[datetime, datetime]:
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise InvalidInterval("La fecha de inicio debe incluir desplazamiento horario")
    if ends_at.tzinfo is None or ends_at.utcoffset() is None:
        raise InvalidInterval("La fecha de fin debe incluir desplazamiento horario")
    starts_at = starts_at.astimezone(timezone.utc)
    ends_at = ends_at.astimezone(timezone.utc)
    if starts_at >= ends_at:
        raise InvalidInterval("El fin debe ser posterior al inicio")
    if starts_at <= datetime.now(timezone.utc):
        raise InvalidInterval("El inicio debe ser estrictamente futuro")
    return starts_at, ends_at


def intervals_overlap(starts_at: datetime, ends_at: datetime, other_start: datetime, other_end: datetime) -> bool:
    return starts_at < other_end and other_start < ends_at


def create_reservation(
    session: Session, requester: User, space_id: int, starts_at: datetime, ends_at: datetime
) -> Reservation:
    starts_at, ends_at = normalize_interval(starts_at, ends_at)
    space = session.get(Space, space_id)
    if space is None:
        raise SpaceNotFound
    if not space.is_active:
        raise SpaceInactive

    # SQLite serializa escritores con BEGIN IMMEDIATE; PostgreSQL bloquea la fila
    # del espacio. Así la comprobación de duplicados y la inserción quedan serializadas.
    if session.bind is not None and session.bind.dialect.name == "sqlite":
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    else:
        session.execute(select(Space.id).where(Space.id == space_id).with_for_update()).scalar_one()

    conflict = session.scalar(
        select(Reservation.id).where(
            Reservation.space_id == space_id,
            Reservation.status == ReservationStatus.APROBADA,
            Reservation.starts_at < ends_at,
            Reservation.ends_at > starts_at,
        ).limit(1)
    )
    duplicate = session.scalar(
        select(Reservation.id).where(
            Reservation.space_id == space_id,
            Reservation.requester_id == requester.id,
            Reservation.status == ReservationStatus.PENDIENTE,
            Reservation.starts_at < ends_at,
            Reservation.ends_at > starts_at,
        ).limit(1)
    )
    if conflict is not None or duplicate is not None:
        session.rollback()
        raise ReservationConflict

    reservation = Reservation(
        requester_id=requester.id,
        space_id=space_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=ReservationStatus.PENDIENTE,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


def is_available(session: Session, space: Space, starts_at: datetime, ends_at: datetime) -> bool:
    starts_at, ends_at = normalize_interval(starts_at, ends_at)
    if not space.is_active:
        return False
    conflict = session.scalar(
        select(Reservation.id).where(
            Reservation.space_id == space.id,
            Reservation.status == ReservationStatus.APROBADA,
            Reservation.starts_at < ends_at,
            Reservation.ends_at > starts_at,
        ).limit(1)
    )
    return conflict is None
