"""Rutas HTTP para registro, autenticación y cuentas."""

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.roles.policy import has_permission
from app.users.models import User
from app.users.schemas import (
    AccountStatusUpdate,
    LoginRequest,
    PublicUser,
    RegisterRequest,
    TokenResponse,
)
from app.users.security import decode_access_token
from app.users.service import (
    AccountNotFound,
    AssignmentConflict,
    PermissionDenied,
    RoleNotFound,
    assign_role,
    assign_space,
    authenticate,
    get_account,
    list_accounts,
    public_user,
    register_student,
    update_account_status,
)


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)
Database = Annotated[Session, Depends(get_db)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(credentials: Credentials, session: Database) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_system_admin(user: CurrentUser) -> User:
    if not has_permission(user, "accounts", "manage"):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    return user


SystemAdmin = Annotated[User, Depends(require_system_admin)]


@router.post("/auth/register", response_model=PublicUser, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Database) -> dict:
    try:
        user = register_student(session, str(payload.email), payload.password)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="El correo ya está registrado") from None
    return public_user(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Database) -> dict:
    result = authenticate(session, str(payload.email), payload.password)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user, token = result
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@router.get("/auth/me", response_model=PublicUser)
def read_current_user(user: CurrentUser) -> dict:
    return public_user(user)


@router.get("/users", response_model=list[PublicUser])
def read_accounts(session: Database, _admin: SystemAdmin) -> list[dict]:
    return [public_user(user) for user in list_accounts(session)]


@router.patch("/users/{user_id}/status", response_model=PublicUser)
def change_account_status(
    user_id: int, payload: AccountStatusUpdate, session: Database, _admin: SystemAdmin
) -> dict:
    try:
        user = update_account_status(session, user_id, payload.is_active)
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada") from None
    return public_user(user)


@router.put("/users/{user_id}/roles/{role_name}", response_model=PublicUser)
def change_account_role(
    user_id: int, role_name: str, session: Database, admin: SystemAdmin
) -> dict:
    if role_name not in {"DOCENTE", "ADMIN_ESPACIOS", "ADMIN_SISTEMA"}:
        raise HTTPException(status_code=422, detail="Rol no asignable")
    try:
        user = assign_role(session, admin, user_id, role_name)
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada") from None
    except RoleNotFound:
        raise HTTPException(status_code=404, detail="Rol no encontrado") from None
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="No puede elevar sus propios permisos") from None
    return public_user(user)


@router.put("/users/{user_id}/spaces/{space_id}", status_code=status.HTTP_200_OK)
def assign_space_admin(
    user_id: int, space_id: int, session: Database, admin: SystemAdmin
) -> dict:
    try:
        user = assign_space(session, admin, user_id, space_id)
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="Cuenta o espacio no encontrado") from None
    except AssignmentConflict:
        raise HTTPException(
            status_code=409, detail="La cuenta no tiene el rol ADMIN_ESPACIOS"
        ) from None
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="No puede ampliar su propio ámbito") from None
    return {"user_id": user.id, "space_id": space_id, "assigned_by_user_id": admin.id}
