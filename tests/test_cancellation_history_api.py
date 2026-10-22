"""Pruebas de cancelación y consulta de historial auditable."""

from datetime import datetime, timedelta, timezone

import pytest

from app.reservations.models import Reservation, ReservationEvent, ReservationStatus
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space
from app.users.models import User
from app.users.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "history-test-secret-with-at-least-thirty-two-bytes")


def create_account(db_session, role_names, email):
    roles = seed_role_permissions(db_session)
    user = User(email=email, password_hash=hash_password("history test password"))
    user.roles.extend(roles[name] for name in role_names)
    db_session.add(user)
    db_session.commit()
    return user


def authorize(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def create_space(db_session):
    space = Space(
        name="Sala de cómputo",
        space_type="SALA_COMPUTO",
        capacity=30,
        location="Edificio C",
        is_active=True,
    )
    db_session.add(space)
    db_session.commit()
    return space


def assign_manager(db_session, space, email="manager@university.edu"):
    manager = create_account(db_session, ["ADMIN_ESPACIOS"], email)
    space.administrators.append(manager)
    db_session.commit()
    return manager


def create_reservation(db_session, requester, space, state=ReservationStatus.PENDIENTE):
    begins = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = Reservation(
        requester=requester,
        space=space,
        starts_at=begins,
        ends_at=begins + timedelta(hours=2),
        status=state,
    )
    db_session.add(reservation)
    db_session.commit()
    return reservation


@pytest.mark.parametrize("state", [ReservationStatus.PENDIENTE, ReservationStatus.APROBADA])
def test_requester_can_cancel_own_pending_or_approved_reservation(api_client, db_session, state):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    reservation = create_reservation(db_session, requester, space, state)

    response = api_client.post(
        f"/reservations/{reservation.id}/cancel", headers=authorize(requester)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELADA"
    event = db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).one()
    assert event.actor_user_id == requester.id
    assert event.event_type == "CANCELADA"


@pytest.mark.parametrize("state", [ReservationStatus.RECHAZADA, ReservationStatus.CANCELADA])
def test_final_reservation_cannot_be_cancelled_again(api_client, db_session, state):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    reservation = create_reservation(db_session, requester, space, state)

    response = api_client.post(
        f"/reservations/{reservation.id}/cancel", headers=authorize(requester)
    )

    assert response.status_code == 409
    assert db_session.get(Reservation, reservation.id).status == state
    assert db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).count() == 0


def test_requester_cannot_cancel_another_users_reservation(api_client, db_session):
    owner = create_account(db_session, ["ESTUDIANTE"], "owner@university.edu")
    other = create_account(db_session, ["DOCENTE"], "other@university.edu")
    space = create_space(db_session)
    reservation = create_reservation(db_session, owner, space)

    response = api_client.post(
        f"/reservations/{reservation.id}/cancel", headers=authorize(other)
    )

    assert response.status_code == 403
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE


def test_assigned_manager_must_cancel_with_nonblank_reason(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space)

    missing = api_client.post(
        f"/reservations/{reservation.id}/cancel", headers=authorize(manager)
    )
    blank = api_client.post(
        f"/reservations/{reservation.id}/cancel",
        json={"reason": "   "},
        headers=authorize(manager),
    )
    assert missing.status_code == blank.status_code == 422
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE

    cancelled = api_client.post(
        f"/reservations/{reservation.id}/cancel",
        json={"reason": "  Solicitud duplicada  "},
        headers=authorize(manager),
    )
    assert cancelled.status_code == 200
    event = db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).one()
    assert event.actor_user_id == manager.id
    assert event.details["reason"] == "Solicitud duplicada"
    assert "decided_at" in event.details


def test_manager_outside_scope_and_system_admin_cannot_cancel(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    manager = create_account(db_session, ["ADMIN_ESPACIOS"], "outside@university.edu")
    system_admin = create_account(db_session, ["ADMIN_SISTEMA"], "system@university.edu")
    space = create_space(db_session)
    reservation = create_reservation(db_session, requester, space)

    outside = api_client.post(
        f"/reservations/{reservation.id}/cancel",
        json={"reason": "Cancelación forzada"},
        headers=authorize(manager),
    )
    system = api_client.post(
        f"/reservations/{reservation.id}/cancel",
        json={"reason": "Cancelación técnica"},
        headers=authorize(system_admin),
    )

    assert outside.status_code == system.status_code == 403
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE


def test_reservation_creation_is_audited_and_requester_can_read_history(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    starts_at = datetime.now(timezone.utc) + timedelta(days=40)
    created = api_client.post(
        "/reservations",
        json={
            "space_id": space.id,
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        },
        headers=authorize(requester),
    )
    reservation_id = created.json()["id"]

    response = api_client.get(
        f"/reservations/{reservation_id}/history", headers=authorize(requester)
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert [event["event_type"] for event in response.json()] == ["SOLICITADA"]
    assert response.json()[0]["actor_user_id"] == requester.id


def test_history_returns_creation_approval_and_cancellation_in_order(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    starts_at = datetime.now(timezone.utc) + timedelta(days=41)
    created = api_client.post(
        "/reservations",
        json={
            "space_id": space.id,
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        },
        headers=authorize(requester),
    )
    reservation_id = created.json()["id"]
    approved = api_client.post(
        f"/reservations/{reservation_id}/approve", headers=authorize(manager)
    )
    cancelled = api_client.post(
        f"/reservations/{reservation_id}/cancel", headers=authorize(requester)
    )

    history = api_client.get(
        f"/reservations/{reservation_id}/history", headers=authorize(requester)
    )

    assert approved.status_code == cancelled.status_code == history.status_code == 200
    events = history.json()
    assert [event["event_type"] for event in events] == ["SOLICITADA", "APROBADA", "CANCELADA"]
    assert [event["occurred_at"] for event in events] == sorted(
        event["occurred_at"] for event in events
    )


def test_assigned_manager_can_read_history_but_unassigned_and_system_cannot(
    api_client, db_session
):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    outside = create_account(db_session, ["ADMIN_ESPACIOS"], "outside@university.edu")
    system_admin = create_account(db_session, ["ADMIN_SISTEMA"], "system@university.edu")
    reservation = create_reservation(db_session, requester, space)
    db_session.add(
        ReservationEvent(
            reservation_id=reservation.id,
            actor_user_id=requester.id,
            event_type="SOLICITADA",
            details={},
        )
    )
    db_session.commit()

    visible = api_client.get(
        f"/reservations/{reservation.id}/history", headers=authorize(manager)
    )
    outside_response = api_client.get(
        f"/reservations/{reservation.id}/history", headers=authorize(outside)
    )
    system_response = api_client.get(
        f"/reservations/{reservation.id}/history", headers=authorize(system_admin)
    )

    assert visible.status_code == 200
    assert outside_response.status_code == system_response.status_code == 403


def test_history_events_cannot_be_modified_through_api(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    reservation = create_reservation(db_session, requester, space)
    event = ReservationEvent(
        reservation_id=reservation.id,
        actor_user_id=requester.id,
        event_type="SOLICITADA",
        details={"source": "test"},
    )
    db_session.add(event)
    db_session.commit()

    update_response = api_client.put(
        f"/reservation-events/{event.id}",
        json={"details": {"source": "altered"}},
        headers=authorize(requester),
    )
    delete_response = api_client.delete(
        f"/reservation-events/{event.id}", headers=authorize(requester)
    )

    assert update_response.status_code in {404, 405}
    assert delete_response.status_code in {404, 405}
    assert db_session.get(ReservationEvent, event.id).details == {"source": "test"}
