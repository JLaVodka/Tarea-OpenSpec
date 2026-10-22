"""Pruebas de la matriz de permisos y el alcance de los roles."""

import pytest

from app.roles.policy import has_permission, has_space_permission, seed_role_permissions
from app.spaces.models import Space
from app.users.models import User
from app.users.security import create_access_token, hash_password


TEST_SECRET = "role-policy-test-secret-with-at-least-thirty-two-bytes"


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)


@pytest.fixture
def role_catalog(db_session):
    return seed_role_permissions(db_session)


def make_user(db_session, roles, email):
    user = User(email=email, password_hash=hash_password("test password"))
    user.roles.extend(roles)
    db_session.add(user)
    db_session.commit()
    return user


def test_student_and_teacher_receive_requester_permissions(role_catalog, db_session):
    for role_name in ("ESTUDIANTE", "DOCENTE"):
        user = make_user(
            db_session, [role_catalog[role_name]], f"{role_name.lower()}@university.edu"
        )

        assert has_permission(user, "reservations", "create_own") is True
        assert has_permission(user, "reservations", "read_own") is True
        assert has_permission(user, "spaces", "manage") is False
        assert has_permission(user, "accounts", "manage") is False


def test_space_admin_permissions_are_limited_to_assigned_spaces(role_catalog, db_session):
    user = make_user(
        db_session, [role_catalog["ADMIN_ESPACIOS"]], "space-admin@university.edu"
    )
    assigned_space = Space(
        name="Laboratorio asignado",
        space_type="LABORATORIO",
        capacity=20,
        location="Edificio A",
    )
    other_space = Space(
        name="Auditorio ajeno",
        space_type="AUDITORIO",
        capacity=100,
        location="Edificio B",
    )
    assigned_space.administrators.append(user)
    db_session.add_all([assigned_space, other_space])
    db_session.commit()

    assert has_space_permission(user, assigned_space.id, "spaces", "manage") is True
    assert has_space_permission(user, other_space.id, "spaces", "manage") is False
    assert has_space_permission(user, assigned_space.id, "reservations", "approve") is True


def test_system_admin_alone_has_no_business_permissions(role_catalog, db_session):
    user = make_user(
        db_session, [role_catalog["ADMIN_SISTEMA"]], "system-admin@university.edu"
    )

    assert has_permission(user, "accounts", "manage") is True
    assert has_permission(user, "spaces", "assign_admin") is True
    assert has_permission(user, "reservations", "approve") is False
    assert has_permission(user, "reservations", "create_own") is False


def test_combined_roles_use_union_without_expanding_space_scope(role_catalog, db_session):
    user = make_user(
        db_session,
        [role_catalog["ADMIN_SISTEMA"], role_catalog["ADMIN_ESPACIOS"]],
        "combined-admin@university.edu",
    )
    assigned_space = Space(
        name="Laboratorio propio",
        space_type="LABORATORIO",
        capacity=10,
        location="Edificio A",
    )
    other_space = Space(
        name="Laboratorio ajeno",
        space_type="LABORATORIO",
        capacity=10,
        location="Edificio B",
    )
    assigned_space.administrators.append(user)
    db_session.add_all([assigned_space, other_space])
    db_session.commit()

    assert has_permission(user, "accounts", "manage") is True
    assert has_space_permission(user, assigned_space.id, "reservations", "approve") is True
    assert has_space_permission(user, other_space.id, "reservations", "approve") is False


def test_unlisted_permission_is_denied_by_default(role_catalog, db_session):
    user = make_user(
        db_session, [role_catalog["ADMIN_SISTEMA"]], "deny-default@university.edu"
    )

    assert has_permission(user, "unlisted-resource", "unlisted-action") is False


def test_space_admin_cannot_assign_roles_or_administer_accounts(api_client, db_session):
    role_catalog = seed_role_permissions(db_session)
    target = make_user(
        db_session, [role_catalog["ESTUDIANTE"]], "target@university.edu"
    )
    user = User(
        email="space-admin@university.edu",
        password_hash=hash_password("space admin password"),
    )
    db_session.add(user)
    user.roles.append(role_catalog["ADMIN_ESPACIOS"])
    db_session.commit()
    # Firmar el token con la clave configurada para esta prueba.
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = api_client.get("/users", headers=headers)
    assignment_response = api_client.put(
        f"/users/{target.id}/roles/DOCENTE", headers=headers
    )

    assert response.status_code == 403
    assert assignment_response.status_code == 403
