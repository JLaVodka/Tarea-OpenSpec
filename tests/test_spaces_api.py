"""Pruebas de catálogo, mutación y conservación de espacios."""

from datetime import datetime, timedelta, timezone

import pytest

from app.reservations.models import Reservation, ReservationStatus
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space, space_admin_assignments
from app.users.models import User
from app.users.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "spaces-test-secret-with-at-least-thirty-two-bytes")


def create_account(db_session, role_names, email):
    roles = seed_role_permissions(db_session)
    user = User(email=email, password_hash=hash_password("space test password"))
    user.roles.extend(roles[name] for name in role_names)
    db_session.add(user)
    db_session.commit()
    return user


def authorize(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def create_space(db_session, *, name="Laboratorio", active=True):
    space = Space(
        name=name,
        space_type="LABORATORIO",
        capacity=24,
        location="Edificio A",
        is_active=active,
    )
    db_session.add(space)
    db_session.commit()
    return space


def create_assigned_manager(db_session, space):
    user = create_account(db_session, ["ADMIN_ESPACIOS"], "manager@university.edu")
    space.administrators.append(user)
    db_session.commit()
    return user


def test_authenticated_catalog_includes_inactive_space(api_client, db_session):
    student = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    active = create_space(db_session, name="Activo")
    inactive = create_space(db_session, name="Inactivo", active=False)

    response = api_client.get("/spaces", headers=authorize(student))

    assert response.status_code == 200
    spaces = {item["id"]: item for item in response.json()}
    assert spaces[active.id]["is_active"] is True
    assert spaces[inactive.id]["is_active"] is False


def test_assigned_space_admin_can_create_space_and_is_assigned_as_manager(
    api_client, db_session
):
    manager = create_account(db_session, ["ADMIN_ESPACIOS"], "creator@university.edu")

    response = api_client.post(
        "/spaces",
        json={
            "name": "Laboratorio nuevo",
            "space_type": "LABORATORIO",
            "capacity": 18,
            "location": "Edificio C",
        },
        headers=authorize(manager),
    )

    assert response.status_code == 201
    created = response.json()
    assert created["is_active"] is True
    assignment = db_session.execute(
        space_admin_assignments.select().where(
            space_admin_assignments.c.space_id == created["id"],
            space_admin_assignments.c.user_id == manager.id,
        )
    ).mappings().one()
    assert assignment["assigned_by_user_id"] == manager.id


@pytest.mark.parametrize("role_name", ["ESTUDIANTE", "DOCENTE", "ADMIN_SISTEMA"])
def test_user_without_space_creation_permission_cannot_create_space(
    api_client, db_session, role_name
):
    user = create_account(db_session, [role_name], f"{role_name.lower()}@university.edu")

    response = api_client.post(
        "/spaces",
        json={
            "name": "No autorizado",
            "space_type": "SALA_COMPUTO",
            "capacity": 25,
            "location": "Edificio C",
        },
        headers=authorize(user),
    )

    assert response.status_code == 403
    assert db_session.query(Space).count() == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Sin tipo", "capacity": 10, "location": "Edificio A"},
        {"name": "Sin ubicación", "space_type": "LABORATORIO", "capacity": 10},
        {
            "name": "Capacidad inválida",
            "space_type": "LABORATORIO",
            "capacity": 0,
            "location": "Edificio A",
        },
    ],
)
def test_space_creation_rejects_invalid_or_missing_required_data(
    api_client, db_session, payload
):
    manager = create_account(db_session, ["ADMIN_ESPACIOS"], "creator@university.edu")

    response = api_client.post("/spaces", json=payload, headers=authorize(manager))

    assert response.status_code == 422
    assert db_session.query(Space).count() == 0


def test_assigned_space_admin_can_update_and_deactivate_space(api_client, db_session):
    space = create_space(db_session)
    manager = create_assigned_manager(db_session, space)
    headers = authorize(manager)

    update_response = api_client.put(
        f"/spaces/{space.id}",
        json={"name": "Laboratorio actualizado", "capacity": 30},
        headers=headers,
    )
    deactivate_response = api_client.patch(
        f"/spaces/{space.id}/status", json={"is_active": False}, headers=headers
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Laboratorio actualizado"
    assert update_response.json()["capacity"] == 30
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False


def test_assigned_space_admin_cannot_mutate_space_outside_scope(api_client, db_session):
    assigned = create_space(db_session, name="Asignado")
    unassigned = create_space(db_session, name="No asignado")
    manager = create_assigned_manager(db_session, assigned)

    response = api_client.put(
        f"/spaces/{unassigned.id}",
        json={"capacity": 40},
        headers=authorize(manager),
    )

    assert response.status_code == 403
    assert db_session.get(Space, unassigned.id).capacity == 24


@pytest.mark.parametrize("role_name", ["ESTUDIANTE", "DOCENTE", "ADMIN_SISTEMA"])
def test_user_without_space_management_permission_cannot_mutate_catalog(
    api_client, db_session, role_name
):
    space = create_space(db_session)
    user = create_account(db_session, [role_name], f"{role_name.lower()}@university.edu")

    response = api_client.patch(
        f"/spaces/{space.id}/status",
        json={"is_active": False},
        headers=authorize(user),
    )

    assert response.status_code == 403
    assert db_session.get(Space, space.id).is_active is True


def test_invalid_space_capacity_is_rejected_without_modification(api_client, db_session):
    space = create_space(db_session)
    manager = create_assigned_manager(db_session, space)

    response = api_client.put(
        f"/spaces/{space.id}",
        json={"capacity": 0},
        headers=authorize(manager),
    )

    assert response.status_code == 422
    assert db_session.get(Space, space.id).capacity == 24


def test_assigned_space_admin_can_delete_space_without_reservations(api_client, db_session):
    space = create_space(db_session)
    manager = create_assigned_manager(db_session, space)

    response = api_client.delete(f"/spaces/{space.id}", headers=authorize(manager))

    assert response.status_code == 204
    assert db_session.get(Space, space.id) is None


def test_space_with_any_reservation_cannot_be_deleted(api_client, db_session):
    manager = create_account(db_session, ["ADMIN_ESPACIOS"], "manager@university.edu")
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    space.administrators.append(manager)
    reservation = Reservation(
        requester=requester,
        space=space,
        starts_at=datetime.now(timezone.utc) + timedelta(days=2),
        ends_at=datetime.now(timezone.utc) + timedelta(days=2, hours=1),
        status=ReservationStatus.PENDIENTE,
    )
    db_session.add(reservation)
    db_session.commit()

    response = api_client.delete(
        f"/spaces/{space.id}", headers=authorize(manager)
    )

    assert response.status_code == 409
    assert db_session.get(Space, space.id) is not None
    assert db_session.get(Reservation, reservation.id) is not None
