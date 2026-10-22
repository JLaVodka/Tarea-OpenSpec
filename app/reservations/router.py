"""Rutas HTTP para solicitudes y consulta de disponibilidad."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.reservations.models import Reservation, ReservationEvent
from app.reservations.schemas import (
    AvailabilityPublic,
    CancellationRequest,
    RejectionRequest,
    ReservationEventPublic,
    ReservationCreate,
    ReservationPublic,
)
from app.reservations.service import (
    InvalidInterval,
    ReservationConflict,
    ReservationNotFound,
    SpaceInactive,
    SpaceNotFound,
    SpaceUnavailable,
    cancel_reservation,
    create_reservation,
    decide_reservation,
    is_available,
    normalize_interval,
)
from app.roles.policy import has_permission, has_space_permission
from app.spaces.models import Space
from app.users.router import CurrentUser


router = APIRouter(tags=["Reservas"])
Database = Annotated[Session, Depends(get_db)]


def _get_space(session: Session, space_id: int) -> Space:
    space = session.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return space


@router.post("/reservations", response_model=ReservationPublic, status_code=status.HTTP_201_CREATED)
def request_reservation(
    payload: ReservationCreate, session: Database, user: CurrentUser
) -> Reservation:
    if not has_permission(user, "reservations", "create_own"):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    try:
        return create_reservation(session, user, payload.space_id, payload.starts_at, payload.ends_at)
    except InvalidInterval as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except SpaceNotFound:
        raise HTTPException(status_code=404, detail="Espacio no encontrado") from None
    except SpaceInactive:
        raise HTTPException(status_code=409, detail="El espacio está inactivo y no es reservable") from None
    except ReservationConflict:
        raise HTTPException(
            status_code=409,
            detail="El intervalo se solapa con una reserva aprobada o solicitud propia pendiente",
        ) from None


@router.get("/reservations", response_model=list[ReservationPublic])
def list_reservations(session: Database, user: CurrentUser) -> list[Reservation]:
    scope_ids = [space.id for space in user.administered_spaces]
    conditions = [Reservation.requester_id == user.id]
    if scope_ids and has_permission(user, "reservations", "review"):
        conditions.append(Reservation.space_id.in_(scope_ids))
    return list(
        session.scalars(select(Reservation).where(or_(*conditions)).order_by(Reservation.id)).all()
    )


@router.get("/reservations/{reservation_id}", response_model=ReservationPublic)
def get_reservation(reservation_id: int, session: Database, user: CurrentUser) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if reservation.requester_id != user.id and not has_space_permission(
        user, reservation.space_id, "reservations", "review"
    ):
        raise HTTPException(status_code=403, detail="Solicitud fuera del ámbito permitido")
    return reservation


def _decide(
    reservation_id: int,
    session: Session,
    user,
    *,
    approve: bool,
    reason: str | None = None,
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if not has_space_permission(user, reservation.space_id, "reservations", "review"):
        raise HTTPException(status_code=403, detail="Solicitud fuera del ámbito asignado")
    try:
        return decide_reservation(
            session, reservation_id, user, approve=approve, reason=reason
        )
    except ReservationNotFound:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada") from None
    except ReservationConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except SpaceUnavailable:
        raise HTTPException(
            status_code=409, detail="El espacio está inactivo y no puede aprobarse"
        ) from None


@router.post("/reservations/{reservation_id}/approve", response_model=ReservationPublic)
def approve_reservation(
    reservation_id: int, session: Database, user: CurrentUser
) -> Reservation:
    return _decide(reservation_id, session, user, approve=True)


@router.post("/reservations/{reservation_id}/reject", response_model=ReservationPublic)
def reject_reservation(
    reservation_id: int,
    payload: RejectionRequest,
    session: Database,
    user: CurrentUser,
) -> Reservation:
    return _decide(
        reservation_id, session, user, approve=False, reason=payload.reason
    )


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationPublic)
def cancel_reservation_route(
    reservation_id: int,
    session: Database,
    user: CurrentUser,
    payload: Annotated[CancellationRequest | None, Body()] = None,
) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    requester_cancel = reservation.requester_id == user.id and has_permission(
        user, "reservations", "cancel_own"
    )
    manager_cancel = has_space_permission(
        user, reservation.space_id, "reservations", "cancel_forced"
    )
    if not requester_cancel and not manager_cancel:
        raise HTTPException(status_code=403, detail="No puede cancelar esta solicitud")

    reason = payload.reason if payload is not None else None
    if manager_cancel and not requester_cancel and not (reason or "").strip():
        raise HTTPException(status_code=422, detail="El motivo de cancelación es obligatorio")
    try:
        return cancel_reservation(
            session, reservation_id, user, reason=reason if manager_cancel and not requester_cancel else None
        )
    except ReservationNotFound:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada") from None
    except ReservationConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.get(
    "/reservations/{reservation_id}/history",
    response_model=list[ReservationEventPublic],
)
def reservation_history(
    reservation_id: int, session: Database, user: CurrentUser
) -> list[ReservationEvent]:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    own_history = reservation.requester_id == user.id and has_permission(
        user, "history", "read_own"
    )
    assigned_history = has_space_permission(
        user, reservation.space_id, "history", "read_assigned"
    )
    if not own_history and not assigned_history:
        raise HTTPException(status_code=403, detail="Historial fuera del ámbito permitido")
    return list(
        session.scalars(
            select(ReservationEvent)
            .where(ReservationEvent.reservation_id == reservation_id)
            .order_by(ReservationEvent.occurred_at, ReservationEvent.id)
        ).all()
    )


@router.get("/availability", response_model=AvailabilityPublic)
def check_availability(
    space_id: int,
    starts_at: Annotated[datetime, Query()],
    ends_at: Annotated[datetime, Query()],
    session: Database,
    _user: CurrentUser,
) -> dict:
    try:
        normalize_interval(starts_at, ends_at)
    except InvalidInterval as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    space = _get_space(session, space_id)
    try:
        available = is_available(session, space, starts_at, ends_at)
    except InvalidInterval as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    return {"space_id": space.id, "active": space.is_active, "available": available}
