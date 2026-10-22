"""Reglas de negocio de solicitudes y disponibilidad."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.reservations.models import Reservation, ReservationEvent, ReservationStatus
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


class DurationLimitExceeded(Exception):
    """La solicitud supera el máximo de cuatro horas consecutivas."""


class ReservationNotFound(Exception):
    """No existe la solicitud indicada."""


class SpaceUnavailable(Exception):
    """El espacio no está activo para aprobar nuevas reservas."""


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

    try:
        validate_consecutive_duration(session, requester, space_id, starts_at, ends_at)
    except DurationLimitExceeded:
        session.rollback()
        raise

    reservation = Reservation(
        requester_id=requester.id,
        space_id=space_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=ReservationStatus.PENDIENTE,
    )
    session.add(reservation)
    session.flush()
    session.add(
        ReservationEvent(
            reservation_id=reservation.id,
            actor_user_id=requester.id,
            event_type="SOLICITADA",
            details={
                "starts_at": starts_at.isoformat(),
                "ends_at": ends_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    )
    session.commit()
    session.refresh(reservation)
    return reservation


def validate_consecutive_duration(
    session: Session,
    requester: User,
    space_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    """Limita la cadena contigua activa por solicitante y espacio."""
    if any(role.name in {"ADMIN_ESPACIOS", "ADMIN_SISTEMA"} for role in requester.roles):
        return

    maximum = timedelta(hours=4)
    if ends_at - starts_at > maximum:
        raise DurationLimitExceeded

    reservations = session.scalars(
        select(Reservation).where(
            Reservation.requester_id == requester.id,
            Reservation.space_id == space_id,
            Reservation.status.in_(
                [ReservationStatus.PENDIENTE, ReservationStatus.APROBADA]
            ),
        )
    ).all()

    def utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    intervals = [
        (utc(item.starts_at), utc(item.ends_at), False) for item in reservations
    ]
    intervals.append((starts_at, ends_at, True))
    intervals.sort(key=lambda item: (item[0], item[1]))

    chain_start: datetime | None = None
    chain_end: datetime | None = None
    contains_new_interval = False
    for interval_start, interval_end, is_new in intervals:
        if chain_end is None or interval_start > chain_end:
            if (
                contains_new_interval
                and chain_start is not None
                and chain_end is not None
                and chain_end - chain_start > maximum
            ):
                raise DurationLimitExceeded
            chain_start = interval_start
            chain_end = interval_end
            contains_new_interval = is_new
            continue
        chain_end = max(chain_end, interval_end)
        contains_new_interval = contains_new_interval or is_new

    if (
        contains_new_interval
        and chain_start is not None
        and chain_end is not None
        and chain_end - chain_start > maximum
    ):
        raise DurationLimitExceeded


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


def decide_reservation(
    session: Session,
    reservation_id: int,
    actor: User,
    *,
    approve: bool,
    reason: str | None = None,
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFound

    # Serializar todas las decisiones del mismo espacio evita dos aprobaciones
    # solapadas, incluso si cada administrador procesa una solicitud distinta.
    if session.bind is not None and session.bind.dialect.name == "sqlite":
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    else:
        session.execute(
            select(Space.id).where(Space.id == reservation.space_id).with_for_update()
        ).scalar_one()
        reservation = session.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        ).scalar_one()

    if reservation.status != ReservationStatus.PENDIENTE:
        session.rollback()
        raise ReservationConflict("Solo pueden decidirse solicitudes pendientes")

    space = session.get(Space, reservation.space_id)
    if approve:
        if space is None or not space.is_active:
            session.rollback()
            raise SpaceUnavailable
        conflict = session.scalar(
            select(Reservation.id).where(
                Reservation.id != reservation.id,
                Reservation.space_id == reservation.space_id,
                Reservation.status == ReservationStatus.APROBADA,
                Reservation.starts_at < reservation.ends_at,
                Reservation.ends_at > reservation.starts_at,
            ).limit(1)
        )
        if conflict is not None:
            session.rollback()
            raise ReservationConflict("El intervalo se solapa con una reserva aprobada")
        reservation.status = ReservationStatus.APROBADA
        event_type = "APROBADA"
        details = {}
    else:
        normalized_reason = (reason or "").strip()
        if not normalized_reason:
            session.rollback()
            raise ValueError("El motivo de rechazo es obligatorio")
        reservation.status = ReservationStatus.RECHAZADA
        event_type = "RECHAZADA"
        details = {"reason": normalized_reason}

    details["decided_at"] = datetime.now(timezone.utc).isoformat()
    session.add(
        ReservationEvent(
            reservation_id=reservation.id,
            actor_user_id=actor.id,
            event_type=event_type,
            details=details,
        )
    )
    session.commit()
    session.refresh(reservation)
    return reservation


def cancel_reservation(
    session: Session,
    reservation_id: int,
    actor: User,
    *,
    reason: str | None = None,
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFound
    if session.bind is not None and session.bind.dialect.name == "sqlite":
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    else:
        session.execute(
            select(Space.id).where(Space.id == reservation.space_id).with_for_update()
        ).scalar_one()
        reservation = session.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        ).scalar_one()

    if reservation.status not in {ReservationStatus.PENDIENTE, ReservationStatus.APROBADA}:
        session.rollback()
        raise ReservationConflict("Solo pueden cancelarse solicitudes pendientes o aprobadas")

    details = {"decided_at": datetime.now(timezone.utc).isoformat()}
    if reason is not None:
        normalized_reason = reason.strip()
        if not normalized_reason:
            session.rollback()
            raise ValueError("El motivo de cancelación es obligatorio")
        details["reason"] = normalized_reason

    reservation.status = ReservationStatus.CANCELADA
    session.add(
        ReservationEvent(
            reservation_id=reservation.id,
            actor_user_id=actor.id,
            event_type="CANCELADA",
            details=details,
        )
    )
    session.commit()
    session.refresh(reservation)
    return reservation
