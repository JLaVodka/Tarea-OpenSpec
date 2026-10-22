"""Casos de uso de registro, autenticación y administración de cuentas."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.reservations.models import Reservation  # Registra relaciones ORM.
from app.roles.models import Role, user_roles
from app.spaces.models import Space, space_admin_assignments
from app.users.models import User
from app.users.security import create_access_token, hash_password, verify_password


ROLE_NAMES = ("ESTUDIANTE", "DOCENTE", "ADMIN_ESPACIOS", "ADMIN_SISTEMA")


class AccountNotFound(Exception):
    pass


class RoleNotFound(Exception):
    pass


class PermissionDenied(Exception):
    pass


class AssignmentConflict(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "roles": sorted(role.name for role in user.roles),
    }


def _ensure_roles(session: Session) -> dict[str, Role]:
    existing = {role.name: role for role in session.scalars(select(Role)).all()}
    for role_name in ROLE_NAMES:
        if role_name not in existing:
            role = Role(name=role_name)
            session.add(role)
            existing[role_name] = role
    session.flush()
    return existing


def register_student(session: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    roles = _ensure_roles(session)
    user = User(email=normalized_email, password_hash=hash_password(password), is_active=True)
    user.roles.append(roles["ESTUDIANTE"])
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    session.refresh(user)
    return user


def authenticate(session: Session, email: str, password: str) -> tuple[User, str] | None:
    user = session.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user, create_access_token(user.id)


def list_accounts(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.email)).all())


def get_account(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise AccountNotFound
    return user


def update_account_status(session: Session, user_id: int, is_active: bool) -> User:
    user = get_account(session, user_id)
    user.is_active = is_active
    session.commit()
    session.refresh(user)
    return user


def assign_role(session: Session, actor: User, target_id: int, role_name: str) -> User:
    target = get_account(session, target_id)
    role = session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        raise RoleNotFound
    if target.id == actor.id and role not in target.roles:
        raise PermissionDenied
    if role not in target.roles:
        session.execute(
            user_roles.insert().values(
                user_id=target.id,
                role_id=role.id,
                assigned_by_user_id=actor.id,
            )
        )
        session.commit()
        session.expire(target, ["roles"])
    return target


def assign_space(session: Session, actor: User, target_id: int, space_id: int) -> User:
    target = get_account(session, target_id)
    space = session.get(Space, space_id)
    if space is None:
        raise AccountNotFound
    if not any(role.name == "ADMIN_ESPACIOS" for role in target.roles):
        raise AssignmentConflict
    existing_ids = {admin.id for admin in space.administrators}
    if target.id == actor.id and target.id not in existing_ids:
        raise PermissionDenied
    if target.id not in existing_ids:
        session.execute(
            space_admin_assignments.insert().values(
                space_id=space.id,
                user_id=target.id,
                assigned_by_user_id=actor.id,
            )
        )
        session.commit()
        session.expire(space, ["administrators"])
    return target
