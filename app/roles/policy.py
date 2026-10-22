"""Matriz explícita y evaluación por unión de permisos de rol."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.roles.models import Permission, Role
from app.users.models import User


ROLE_PERMISSIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "ESTUDIANTE": (
        ("spaces", "read"),
        ("availability", "read"),
        ("reservations", "create_own"),
        ("reservations", "read_own"),
        ("reservations", "cancel_own"),
        ("history", "read_own"),
    ),
    "DOCENTE": (
        ("spaces", "read"),
        ("availability", "read"),
        ("reservations", "create_own"),
        ("reservations", "read_own"),
        ("reservations", "cancel_own"),
        ("history", "read_own"),
    ),
    "ADMIN_ESPACIOS": (
        ("spaces", "read"),
        ("spaces", "manage"),
        ("reservations", "review"),
        ("reservations", "approve"),
        ("reservations", "reject"),
        ("reservations", "cancel_forced"),
        ("history", "read_assigned"),
    ),
    "ADMIN_SISTEMA": (
        ("accounts", "manage"),
        ("roles", "assign"),
        ("spaces", "assign_admin"),
    ),
}


def seed_role_permissions(session: Session) -> dict[str, Role]:
    """Crea la matriz aprobada en el catálogo relacional sin confirmar la transacción."""
    roles = {role.name: role for role in session.scalars(select(Role)).all()}
    for role_name in ROLE_PERMISSIONS:
        if role_name not in roles:
            roles[role_name] = Role(name=role_name)
            session.add(roles[role_name])

    required_permissions = {
        permission
        for permissions in ROLE_PERMISSIONS.values()
        for permission in permissions
    }
    permissions = {
        (permission.resource, permission.action): permission
        for permission in session.scalars(select(Permission)).all()
    }
    for resource, action in sorted(required_permissions):
        if (resource, action) not in permissions:
            permission = Permission(resource=resource, action=action)
            session.add(permission)
            permissions[(resource, action)] = permission

    session.flush()
    for role_name, role_permissions in ROLE_PERMISSIONS.items():
        role = roles[role_name]
        assigned = {(item.resource, item.action) for item in role.permissions}
        for resource, action in role_permissions:
            permission = permissions[(resource, action)]
            if (resource, action) not in assigned:
                role.permissions.append(permission)
    session.flush()
    return roles


def has_permission(user: User, resource: str, action: str) -> bool:
    """Evalúa por unión los permisos explícitos de todos los roles del usuario."""
    return any(
        permission.resource == resource and permission.action == action
        for role in user.roles
        for permission in role.permissions
    )


def has_space_permission(user: User, space_id: int, resource: str, action: str) -> bool:
    """Aplica el ámbito asignado cuando el permiso procede de ADMIN_ESPACIOS."""
    scoped_permission = any(
        role.name == "ADMIN_ESPACIOS"
        and any(
            permission.resource == resource and permission.action == action
            for permission in role.permissions
        )
        for role in user.roles
    )
    return scoped_permission and any(space.id == space_id for space in user.administered_spaces)
