"""Pruebas de creación/consulta de solicitudes y disponibilidad."""

from datetime import datetime, timedelta, timezone

import pytest

from app.reservations.models import Reservation, ReservationStatus
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space
from app.users.models import User
from app.users.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "reservation-test-secret-with-at-least-thirty-two-bytes")


def create_account(db_session, role_name, email):
    roles = seed_role_permissions(db_session)
    user = User(email=email, password_hash=hash_password("reservation test password"))
    user.roles.append(roles[role_name])
    db_session.add(user)
    db_session.commit()
    return user


def authorize(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def create_space(db_session, *, active=True):
    space = Space(
        name="Laboratorio",
        space_type="LABORATORIO",
        capacity=24,
        location="Edificio A",
        is_active=active,
    )
    db_session.add(space)
    db_session.commit()
    return space


def future_interval(*, start=None, duration=timedelta(hours=1)):
    begins = start or datetime.now(timezone.utc) + timedelta(days=3)
    ends = begins + duration
    return begins, ends


def request_payload(space_id, *, starts_at=None, ends_at=None):
    begins, ends = future_interval()
    return {
        "space_id": space_id,
        "starts_at": (starts_at or begins).isoformat(),
        "ends_at": (ends_at or ends).isoformat(),
    }


def seed_reservation(db_session, requester, space, starts_at, ends_at, state):
    reservation = Reservation(
        requester=requester,
        space=space,
        starts_at=starts_at,
        ends_at=ends_at,
        status=state,
    )
    db_session.add(reservation)
    db_session.commit()
    return reservation


def test_student_can_create_pending_request_for_self(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session)

    response = api_client.post(
        "/reservations", json=request_payload(space.id), headers=authorize(student)
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDIENTE"
    assert response.json()["requester_id"] == student.id
    assert response.json()["starts_at"].endswith("Z") or response.json()["starts_at"].endswith("+00:00")


def test_teacher_can_create_request_but_cannot_choose_other_requester(api_client, db_session):
    teacher = create_account(db_session, "DOCENTE", "teacher@university.edu")
    space = create_space(db_session)
    payload = request_payload(space.id)
    payload["requester_id"] = 999

    response = api_client.post("/reservations", json=payload, headers=authorize(teacher))

    assert response.status_code == 422
    assert db_session.query(Reservation).count() == 0


@pytest.mark.parametrize(
    "starts_at,ends_at",
    [
        ("2020-01-01T12:00:00+00:00", "2020-01-01T12:00:00+00:00"),
        ("2020-01-01T13:00:00+00:00", "2020-01-01T12:00:00+00:00"),
        ("2020-01-01T12:00:00+00:00", "2020-01-01T13:00:00+00:00"),
        ("2030-01-01T12:00:00", "2030-01-01T13:00:00+00:00"),
    ],
)
def test_invalid_interval_is_rejected(api_client, db_session, starts_at, ends_at):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session)
    payload = request_payload(
        space.id,
        starts_at=datetime.fromisoformat(starts_at),
        ends_at=datetime.fromisoformat(ends_at),
    )

    response = api_client.post("/reservations", json=payload, headers=authorize(student))

    assert response.status_code == 422
    assert db_session.query(Reservation).count() == 0


def test_start_equal_to_current_time_is_rejected(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session)
    begins = datetime.now(timezone.utc)

    response = api_client.post(
        "/reservations",
        json=request_payload(space.id, starts_at=begins, ends_at=begins + timedelta(hours=1)),
        headers=authorize(student),
    )

    assert response.status_code == 422
    assert "futuro" in response.json()["detail"]


def test_request_for_inactive_space_is_rejected(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session, active=False)

    response = api_client.post(
        "/reservations", json=request_payload(space.id), headers=authorize(student)
    )

    assert response.status_code == 409
    assert db_session.query(Reservation).count() == 0


def test_request_conflicting_with_approved_reservation_is_rejected(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    other = create_account(db_session, "DOCENTE", "teacher@university.edu")
    space = create_space(db_session)
    begins, ends = future_interval()
    seed_reservation(db_session, other, space, begins, ends, ReservationStatus.APROBADA)

    response = api_client.post(
        "/reservations",
        json=request_payload(space.id, starts_at=begins, ends_at=ends),
        headers=authorize(student),
    )

    assert response.status_code == 409
    assert db_session.query(Reservation).count() == 1


def test_own_pending_overlap_is_rejected_but_another_requester_is_allowed(
    api_client, db_session
):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    teacher = create_account(db_session, "DOCENTE", "teacher@university.edu")
    space = create_space(db_session)
    begins, ends = future_interval()
    seed_reservation(db_session, student, space, begins, ends, ReservationStatus.PENDIENTE)
    payload = request_payload(space.id, starts_at=begins, ends_at=ends)

    duplicate = api_client.post("/reservations", json=payload, headers=authorize(student))
    allowed = api_client.post("/reservations", json=payload, headers=authorize(teacher))

    assert duplicate.status_code == 409
    assert allowed.status_code == 201


def test_users_can_only_list_own_requests(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    teacher = create_account(db_session, "DOCENTE", "teacher@university.edu")
    space = create_space(db_session)
    begins, ends = future_interval()
    own = seed_reservation(db_session, student, space, begins, ends, ReservationStatus.PENDIENTE)
    seed_reservation(
        db_session, teacher, space, begins + timedelta(days=1), ends + timedelta(days=1), ReservationStatus.PENDIENTE
    )

    response = api_client.get("/reservations", headers=authorize(student))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own.id]


def test_assigned_space_admin_can_list_and_read_only_scoped_requests(api_client, db_session):
    requester = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    manager = create_account(db_session, "ADMIN_ESPACIOS", "manager@university.edu")
    assigned = create_space(db_session)
    outside = create_space(db_session)
    assigned.administrators.append(manager)
    db_session.commit()
    begins, ends = future_interval()
    visible = seed_reservation(db_session, requester, assigned, begins, ends, ReservationStatus.PENDIENTE)
    hidden = seed_reservation(
        db_session,
        requester,
        outside,
        begins + timedelta(days=1),
        ends + timedelta(days=1),
        ReservationStatus.PENDIENTE,
    )

    listed = api_client.get("/reservations", headers=authorize(manager))
    visible_read = api_client.get(f"/reservations/{visible.id}", headers=authorize(manager))
    hidden_read = api_client.get(f"/reservations/{hidden.id}", headers=authorize(manager))

    assert [item["id"] for item in listed.json()] == [visible.id]
    assert visible_read.status_code == 200
    assert hidden_read.status_code == 403


def test_space_admin_cannot_create_request_and_availability_rejects_bad_interval(
    api_client, db_session
):
    manager = create_account(db_session, "ADMIN_ESPACIOS", "manager@university.edu")
    space = create_space(db_session)
    begins, ends = future_interval()

    create_response = api_client.post(
        "/reservations", json=request_payload(space.id), headers=authorize(manager)
    )
    invalid_availability = api_client.get(
        "/availability",
        params={"space_id": space.id, "starts_at": begins.isoformat(), "ends_at": begins.isoformat()},
        headers=authorize(manager),
    )
    naive_availability = api_client.get(
        "/availability",
        params={
            "space_id": space.id,
            "starts_at": begins.replace(tzinfo=None).isoformat(),
            "ends_at": ends.isoformat(),
        },
        headers=authorize(manager),
    )

    assert create_response.status_code == 403
    assert invalid_availability.status_code == 422
    assert naive_availability.status_code == 422


def test_availability_uses_approved_only_and_semi_open_intervals(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session)
    begins, ends = future_interval()
    seed_reservation(db_session, student, space, begins, ends, ReservationStatus.PENDIENTE)
    headers = authorize(student)

    pending = api_client.get(
        "/availability",
        params={"space_id": space.id, "starts_at": begins.isoformat(), "ends_at": ends.isoformat()},
        headers=headers,
    )
    adjacent = api_client.get(
        "/availability",
        params={"space_id": space.id, "starts_at": ends.isoformat(), "ends_at": (ends + timedelta(hours=1)).isoformat()},
        headers=headers,
    )
    assert pending.status_code == adjacent.status_code == 200
    assert pending.json()["available"] is True
    assert adjacent.json()["available"] is True

    seed_reservation(db_session, student, space, begins, ends, ReservationStatus.APROBADA)
    blocked = api_client.get(
        "/availability",
        params={"space_id": space.id, "starts_at": begins.isoformat(), "ends_at": ends.isoformat()},
        headers=headers,
    )
    assert blocked.json()["available"] is False
    partial = api_client.get(
        "/availability",
        params={
            "space_id": space.id,
            "starts_at": (begins - timedelta(minutes=30)).isoformat(),
            "ends_at": (begins + timedelta(minutes=30)).isoformat(),
        },
        headers=headers,
    )
    assert partial.status_code == 200
    assert partial.json()["available"] is False


def test_availability_marks_inactive_space_and_requires_authentication(api_client, db_session):
    student = create_account(db_session, "ESTUDIANTE", "student@university.edu")
    space = create_space(db_session, active=False)
    begins, ends = future_interval()
    params = {"space_id": space.id, "starts_at": begins.isoformat(), "ends_at": ends.isoformat()}

    response = api_client.get("/availability", params=params, headers=authorize(student))
    unauthorized = api_client.get("/availability", params=params)

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["active"] is False
    assert unauthorized.status_code == 401
