"""Pruebas de aprobación y rechazo de solicitudes pendientes."""

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy.orm import Session

from app.reservations.models import Reservation, ReservationEvent, ReservationStatus
from app.reservations.service import ReservationConflict, decide_reservation
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space
from app.users.models import User
from app.users.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "approval-test-secret-with-at-least-thirty-two-bytes")


def create_account(db_session, roles_to_assign, email):
    roles = seed_role_permissions(db_session)
    user = User(email=email, password_hash=hash_password("approval test password"))
    user.roles.extend(roles[name] for name in roles_to_assign)
    db_session.add(user)
    db_session.commit()
    return user


def authorize(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def create_space(db_session, *, active=True):
    space = Space(
        name="Auditorio",
        space_type="AUDITORIO",
        capacity=150,
        location="Edificio A",
        is_active=active,
    )
    db_session.add(space)
    db_session.commit()
    return space


def assign_manager(db_session, space, *, roles=("ADMIN_ESPACIOS",), email="manager@university.edu"):
    manager = create_account(db_session, list(roles), email)
    space.administrators.append(manager)
    db_session.commit()
    return manager


def create_reservation(db_session, requester, space, *, begins=None, duration=timedelta(hours=1), state=ReservationStatus.PENDIENTE):
    begins = begins or datetime.now(timezone.utc) + timedelta(days=10)
    reservation = Reservation(
        requester=requester,
        space=space,
        starts_at=begins,
        ends_at=begins + duration,
        status=state,
    )
    db_session.add(reservation)
    db_session.commit()
    return reservation


def test_assigned_manager_approves_pending_and_audits_actor(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space)

    response = api_client.post(
        f"/reservations/{reservation.id}/approve", headers=authorize(manager)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APROBADA"
    event = db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).one()
    assert event.actor_user_id == manager.id
    assert event.event_type == "APROBADA"
    assert "decided_at" in event.details


@pytest.mark.parametrize("state", [ReservationStatus.APROBADA, ReservationStatus.RECHAZADA, ReservationStatus.CANCELADA])
def test_only_pending_reservation_can_be_approved(api_client, db_session, state):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space, state=state)

    response = api_client.post(
        f"/reservations/{reservation.id}/approve", headers=authorize(manager)
    )

    assert response.status_code == 409
    assert db_session.get(Reservation, reservation.id).status == state


def test_inactive_space_cannot_be_approved(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session, active=False)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space)

    response = api_client.post(
        f"/reservations/{reservation.id}/approve", headers=authorize(manager)
    )

    assert response.status_code == 409
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE


def test_unassigned_manager_and_system_admin_cannot_approve(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    outside_manager = create_account(db_session, ["ADMIN_ESPACIOS"], "outside@university.edu")
    system_admin = create_account(db_session, ["ADMIN_SISTEMA"], "system@university.edu")
    reservation = create_reservation(db_session, requester, space)

    outside = api_client.post(
        f"/reservations/{reservation.id}/approve", headers=authorize(outside_manager)
    )
    system = api_client.post(
        f"/reservations/{reservation.id}/approve", headers=authorize(system_admin)
    )

    assert outside.status_code == system.status_code == 403
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE


@pytest.mark.parametrize("offset_minutes", [0, 30])
def test_approval_conflicts_with_exact_or_partial_approved_interval(
    api_client, db_session, offset_minutes
):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    begins = datetime.now(timezone.utc) + timedelta(days=12)
    existing = create_reservation(
        db_session, requester, space, begins=begins, state=ReservationStatus.APROBADA
    )
    candidate = create_reservation(
        db_session, requester, space, begins=begins + timedelta(minutes=offset_minutes)
    )

    response = api_client.post(
        f"/reservations/{candidate.id}/approve", headers=authorize(manager)
    )

    assert response.status_code == 409
    assert db_session.get(Reservation, existing.id).status == ReservationStatus.APROBADA
    assert db_session.get(Reservation, candidate.id).status == ReservationStatus.PENDIENTE


def test_approval_allows_adjacency_other_space_and_cancelled_conflict(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    begins = datetime.now(timezone.utc) + timedelta(days=14)
    existing = create_reservation(
        db_session, requester, space, begins=begins, state=ReservationStatus.APROBADA
    )
    adjacent = create_reservation(db_session, requester, space, begins=existing.ends_at)

    adjacent_response = api_client.post(
        f"/reservations/{adjacent.id}/approve", headers=authorize(manager)
    )
    assert adjacent_response.status_code == 200

    other_space = create_space(db_session)
    other_manager = assign_manager(
        db_session, other_space, email="other-manager@university.edu"
    )
    different = create_reservation(db_session, requester, other_space, begins=begins)
    different_response = api_client.post(
        f"/reservations/{different.id}/approve", headers=authorize(other_manager)
    )
    assert different_response.status_code == 200

    db_session.get(Reservation, existing.id).status = ReservationStatus.CANCELADA
    db_session.commit()
    after_cancel = create_reservation(db_session, requester, space, begins=begins)
    cancelled_response = api_client.post(
        f"/reservations/{after_cancel.id}/approve", headers=authorize(manager)
    )
    assert cancelled_response.status_code == 200


@pytest.mark.parametrize("payload", [{}, {"reason": "   "}])
def test_rejection_requires_nonblank_reason(api_client, db_session, payload):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space)

    response = api_client.post(
        f"/reservations/{reservation.id}/reject", json=payload, headers=authorize(manager)
    )

    assert response.status_code == 422
    assert db_session.get(Reservation, reservation.id).status == ReservationStatus.PENDIENTE


def test_rejection_records_trimmed_reason_actor_and_decision_time(api_client, db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    reservation = create_reservation(db_session, requester, space)

    response = api_client.post(
        f"/reservations/{reservation.id}/reject",
        json={"reason": "  Equipo en mantenimiento  "},
        headers=authorize(manager),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RECHAZADA"
    event = db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).one()
    assert event.actor_user_id == manager.id
    assert event.event_type == "RECHAZADA"
    assert event.details["reason"] == "Equipo en mantenimiento"
    assert "decided_at" in event.details
    repeated = api_client.post(
        f"/reservations/{reservation.id}/reject",
        json={"reason": "Decisión repetida"},
        headers=authorize(manager),
    )
    assert repeated.status_code == 409
    assert db_session.query(ReservationEvent).filter_by(reservation_id=reservation.id).count() == 1


def test_two_concurrent_overlapping_approvals_allow_only_one(db_session):
    requester = create_account(db_session, ["ESTUDIANTE"], "student@university.edu")
    space = create_space(db_session)
    manager = assign_manager(db_session, space)
    begins = datetime.now(timezone.utc) + timedelta(days=20)
    first = create_reservation(db_session, requester, space, begins=begins)
    second = create_reservation(db_session, requester, space, begins=begins)
    reservation_ids = [first.id, second.id]
    manager_id, space_id = manager.id, space.id
    barrier = Barrier(2)

    def approve(reservation_id):
        with Session(db_session.bind) as session:
            actor = session.get(User, manager_id)
            barrier.wait()
            try:
                decide_reservation(session, reservation_id, actor, approve=True)
                return "approved"
            except ReservationConflict:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(approve, reservation_ids))

    assert sorted(results) == ["approved", "conflict"]
    db_session.expire_all()
    assert db_session.query(Reservation).filter_by(
        space_id=space_id, status=ReservationStatus.APROBADA
    ).count() == 1
