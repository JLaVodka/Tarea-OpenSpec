"""Comando local y de una sola vez para aprovisionar el administrador inicial."""

from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.roles.models import Role
from app.roles.policy import seed_role_permissions
from app.users.models import User
from app.users.security import hash_password
from app.users.service import normalize_email


class AdminAlreadyExists(Exception):
    """Señala que la base ya tiene un administrador del sistema."""


class InvalidProvisionCredentials(Exception):
    """Señala que el correo o la contraseña de provisión no son válidos."""


def create_initial_admin(session: Session, email: str, password: str) -> User:
    """Agrega el primer administrador a la transacción activa, si aún no existe."""
    try:
        normalized_email = normalize_email(str(TypeAdapter(EmailStr).validate_python(email)))
    except (ValidationError, ValueError):
        raise InvalidProvisionCredentials("El correo electrónico no es válido") from None
    if not password.strip():
        raise InvalidProvisionCredentials("La contraseña no puede estar vacía")

    existing_admin = session.scalar(
        select(User).join(User.roles).where(Role.name == "ADMIN_SISTEMA").limit(1)
    )
    if existing_admin is not None:
        raise AdminAlreadyExists("Ya existe una cuenta ADMIN_SISTEMA")

    roles = seed_role_permissions(session)
    admin = User(
        email=normalized_email,
        password_hash=hash_password(password),
        is_active=True,
    )
    admin.roles.append(roles["ADMIN_SISTEMA"])
    session.add(admin)
    session.flush()
    return admin


def main() -> None:
    """Solicita credenciales de forma interactiva y confirma una sola transacción."""
    email = input("Correo del administrador inicial: ")
    password = getpass("Contraseña (no se mostrará): ")
    try:
        with SessionLocal.begin() as session:
            admin = create_initial_admin(session, email, password)
    except (AdminAlreadyExists, InvalidProvisionCredentials) as error:
        print(f"No se pudo crear el administrador: {error}")
        raise SystemExit(1) from None

    print(f"Administrador inicial creado: {admin.email} (id={admin.id})")


if __name__ == "__main__":
    main()
