"""API para consultar y administrar el catálogo de espacios."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.reservations.models import Reservation
from app.roles.policy import has_permission, has_space_permission
from app.spaces.models import Space, space_admin_assignments
from app.spaces.schemas import SpaceCreate, SpacePublic, SpaceStatusUpdate, SpaceUpdate
from app.users.router import CurrentUser


router = APIRouter(prefix="/spaces", tags=["Espacios"])
Database = Annotated[Session, Depends(get_db)]


def _space_or_404(session: Session, space_id: int) -> Space:
    space = session.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return space


def _require_creation_permission(user) -> None:
    if not has_permission(user, "spaces", "manage"):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")


def _require_scope(user, space_id: int) -> None:
    if not has_space_permission(user, space_id, "spaces", "manage"):
        raise HTTPException(status_code=403, detail="Espacio fuera del ámbito asignado")


@router.get("", response_model=list[SpacePublic])
def list_spaces(session: Database, _user: CurrentUser) -> list[Space]:
    return list(session.scalars(select(Space).order_by(Space.id)).all())


@router.get("/{space_id}", response_model=SpacePublic)
def get_space(space_id: int, session: Database, _user: CurrentUser) -> Space:
    return _space_or_404(session, space_id)


@router.post("", response_model=SpacePublic, status_code=status.HTTP_201_CREATED)
def create_space(payload: SpaceCreate, session: Database, user: CurrentUser) -> Space:
    _require_creation_permission(user)
    space = Space(**payload.model_dump(), is_active=True)
    try:
        session.add(space)
        session.flush()
        session.execute(
            space_admin_assignments.insert().values(
                space_id=space.id,
                user_id=user.id,
                assigned_by_user_id=user.id,
            )
        )
        session.commit()
        session.refresh(space)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="No se pudo crear el espacio") from None
    return space


@router.put("/{space_id}", response_model=SpacePublic)
def update_space(
    space_id: int, payload: SpaceUpdate, session: Database, user: CurrentUser
) -> Space:
    space = _space_or_404(session, space_id)
    _require_scope(user, space.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(space, field, value)
    session.commit()
    session.refresh(space)
    return space


@router.patch("/{space_id}/status", response_model=SpacePublic)
def update_space_status(
    space_id: int, payload: SpaceStatusUpdate, session: Database, user: CurrentUser
) -> Space:
    space = _space_or_404(session, space_id)
    _require_scope(user, space.id)
    space.is_active = payload.is_active
    session.commit()
    session.refresh(space)
    return space


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_space(space_id: int, session: Database, user: CurrentUser) -> None:
    space = _space_or_404(session, space_id)
    _require_scope(user, space.id)
    if session.scalar(select(Reservation.id).where(Reservation.space_id == space.id).limit(1)):
        raise HTTPException(
            status_code=409,
            detail="El espacio tiene solicitudes o reservas; debe desactivarse",
        )
    session.delete(space)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="El espacio tiene solicitudes o reservas; debe desactivarse",
        ) from None
