"""Escenarios HTTP de registro y autenticación de usuarios."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pwdlib import PasswordHash

from app.roles.models import Role, user_roles
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space, space_admin_assignments
from app.users.models import User


TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)


def register(client, *, email="student@university.edu", password="correct horse battery"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client, *, email="student@university.edu", password="correct horse battery"):
    return client.post("/auth/login", json={"email": email, "password": password})


def create_system_admin(db_session, email="admin@university.edu"):
    roles = seed_role_permissions(db_session)
    user = User(
        email=email,
        password_hash=PasswordHash.recommended().hash("admin test password"),
    )
    user.roles.append(roles["ADMIN_SISTEMA"])
    db_session.add(user)
    db_session.commit()
    return user


def admin_headers(api_client, db_session):
    create_system_admin(db_session)
    response = login(
        api_client, email="admin@university.edu", password="admin test password"
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_registration_creates_active_student_without_exposing_secrets(api_client):
    response = register(api_client, email="  Student@University.edu ")

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "student@university.edu"
    assert payload["is_active"] is True
    assert payload["roles"] == ["ESTUDIANTE"]
    assert "password" not in payload
    assert "password_hash" not in payload


def test_registration_rejects_normalized_duplicate_email(api_client):
    first = register(api_client, email="Student@University.edu")
    second = register(api_client, email=" student@university.edu ")

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]


def test_registration_rejects_attempt_to_choose_privileged_role(api_client):
    response = api_client.post(
        "/auth/register",
        json={"email": "student@university.edu", "password": "a password", "role": "ADMIN_SISTEMA"},
    )

    assert response.status_code == 422


def test_registration_rejects_invalid_email(api_client):
    response = api_client.post(
        "/auth/register", json={"email": "not-an-email", "password": "a password"}
    )

    assert response.status_code == 422


def test_registration_persists_only_an_argon2_password_hash(api_client, db_session):
    response = register(api_client)

    assert response.status_code == 201
    stored_user = db_session.query(User).one()
    assert stored_user.password_hash.startswith("$argon2id$")
    assert stored_user.password_hash != "correct horse battery"


def test_login_returns_bearer_token_and_public_user(api_client):
    register(api_client)

    response = login(api_client)

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "student@university.edu"
    assert payload["user"]["roles"] == ["ESTUDIANTE"]
    assert "password_hash" not in response.text
    assert "correct horse battery" not in response.text


@pytest.mark.parametrize(
    ("email", "password", "active"),
    [
        ("student@university.edu", "wrong password", True),
        ("missing@university.edu", "wrong password", True),
        ("student@university.edu", "correct horse battery", False),
    ],
)
def test_invalid_credentials_and_inactive_account_have_same_response(
    api_client, db_session, email, password, active
):
    if email == "student@university.edu":
        register(api_client)
        user = db_session.query(User).one()
        user.is_active = active
        db_session.commit()

    response = login(api_client, email=email, password=password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas"}


@pytest.mark.parametrize("token_kind", ["malformed", "expired", "wrong_signature", "missing_subject"])
def test_invalid_or_expired_token_cannot_access_protected_route(api_client, token_kind):
    if token_kind == "malformed":
        token = "not.a.jwt"
    else:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=5)
            if token_kind == "missing_subject"
            else datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        claims = {"exp": expires_at}
        if token_kind != "missing_subject":
            claims["sub"] = "123"
        signing_key = (
            "other-test-secret-with-more-than-thirty-two-bytes"
            if token_kind == "wrong_signature"
            else TEST_SECRET
        )
        token = jwt.encode(claims, signing_key, algorithm="HS256")

    response = api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado"}


def test_missing_credentials_cannot_access_protected_route(api_client):
    response = api_client.get("/auth/me")

    assert response.status_code == 401


def test_token_for_inactive_account_is_rejected(api_client, db_session):
    register(api_client)
    auth_response = login(api_client)
    db_session.query(User).one().is_active = False
    db_session.commit()

    response = api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth_response.json()['access_token']}"},
    )

    assert response.status_code == 401


def test_system_admin_can_list_accounts(api_client, db_session):
    headers = admin_headers(api_client, db_session)
    registration = register(api_client)
    assert registration.status_code == 201, registration.text

    response = api_client.get("/users", headers=headers)

    assert response.status_code == 200
    assert {item["email"] for item in response.json()} == {
        "admin@university.edu",
        "student@university.edu",
    }


def test_system_admin_can_assign_role_to_another_account_and_actor_is_recorded(
    api_client, db_session
):
    headers = admin_headers(api_client, db_session)
    registration = register(api_client)
    assert registration.status_code == 201, registration.text
    target = registration.json()
    admin = db_session.query(User).filter_by(email="admin@university.edu").one()

    response = api_client.put(
        f"/users/{target['id']}/roles/DOCENTE", headers=headers
    )

    assert response.status_code == 200
    assert "DOCENTE" in response.json()["roles"]
    assignment = db_session.execute(
        user_roles.select().where(
            user_roles.c.user_id == target["id"],
            user_roles.c.role_id
            == db_session.query(Role.id).filter_by(name="DOCENTE").scalar_subquery(),
        )
    ).mappings().one()
    assert assignment["assigned_by_user_id"] == admin.id


def test_system_admin_cannot_assign_new_role_to_self(api_client, db_session):
    headers = admin_headers(api_client, db_session)
    admin = db_session.query(User).filter_by(email="admin@university.edu").one()

    response = api_client.put(
        f"/users/{admin.id}/roles/ADMIN_ESPACIOS", headers=headers
    )

    assert response.status_code == 403
    assert "ADMIN_ESPACIOS" not in {role.name for role in admin.roles}


def test_student_cannot_change_account_status(api_client, db_session):
    registration = register(api_client)
    assert registration.status_code == 201, registration.text
    student = login(api_client)
    another_response = register(api_client, email="other@university.edu")
    assert another_response.status_code == 201, another_response.text
    another = another_response.json()

    response = api_client.patch(
        f"/users/{another['id']}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {student.json()['access_token']}"},
    )

    assert response.status_code == 403
    assert db_session.query(User).filter_by(id=another["id"]).one().is_active is True


def test_system_admin_can_deactivate_account_and_its_token_stops_working(
    api_client, db_session
):
    headers = admin_headers(api_client, db_session)
    registration = register(api_client)
    assert registration.status_code == 201
    student = registration.json()
    student_token = login(api_client).json()["access_token"]

    response = api_client.patch(
        f"/users/{student['id']}/status",
        json={"is_active": False},
        headers=headers,
    )
    protected_response = api_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {student_token}"}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert protected_response.status_code == 401


def test_system_admin_can_assign_space_to_existing_space_admin_and_actor_is_recorded(
    api_client, db_session
):
    headers = admin_headers(api_client, db_session)
    space_admin_role = db_session.query(Role).filter_by(name="ADMIN_ESPACIOS").one()
    target = User(email="space-admin@university.edu", password_hash="not-used")
    assert not db_session.query(User).filter_by(email=target.email).first()
    target.roles.append(space_admin_role)
    space = Space(
        name="Laboratorio 1",
        space_type="LABORATORIO",
        capacity=20,
        location="Edificio A",
    )
    db_session.add_all([target, space])
    db_session.commit()
    admin = db_session.query(User).filter_by(email="admin@university.edu").one()

    response = api_client.put(
        f"/users/{target.id}/spaces/{space.id}", headers=headers
    )

    assert response.status_code == 200
    assignment = db_session.execute(
        space_admin_assignments.select().where(
            space_admin_assignments.c.user_id == target.id
        )
    ).mappings().one()
    assert assignment["assigned_by_user_id"] == admin.id


def test_system_admin_cannot_assign_space_to_user_without_space_admin_role(
    api_client, db_session
):
    headers = admin_headers(api_client, db_session)
    target = User(email="ordinary@university.edu", password_hash="not-used")
    assert not db_session.query(User).filter_by(email=target.email).first()
    space = Space(
        name="Auditorio",
        space_type="AUDITORIO",
        capacity=50,
        location="Edificio B",
    )
    db_session.add_all([target, space])
    db_session.commit()

    response = api_client.put(
        f"/users/{target.id}/spaces/{space.id}", headers=headers
    )

    assert response.status_code == 409
    assert not db_session.execute(
        space_admin_assignments.select().where(
            space_admin_assignments.c.user_id == target.id
        )
    ).first()
