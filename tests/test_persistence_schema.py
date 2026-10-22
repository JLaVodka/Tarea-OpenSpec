"""Restricciones estructurales de las entidades persistidas."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base


def test_isolated_database_creates_all_domain_tables(db_session):
    table_names = set(inspect(db_session.bind).get_table_names())

    assert {
        "users",
        "roles",
        "permissions",
        "user_roles",
        "role_permissions",
        "spaces",
        "space_admin_assignments",
        "reservations",
        "reservation_events",
    } <= table_names


def test_sqlite_enforces_foreign_keys(db_session):
    assert db_session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_email_is_unique_after_trim_and_case_normalization(db_session):
    from app.users.models import User

    db_session.add_all(
        [
            User(email=" Student@Uni.edu ", password_hash="hash-a"),
            User(email="student@uni.edu", password_hash="hash-b"),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_distinct_email_addresses_are_allowed(db_session):
    from app.users.models import User

    db_session.add_all(
        [
            User(email="first@university.edu", password_hash="hash-a"),
            User(email="second@university.edu", password_hash="hash-b"),
        ]
    )

    db_session.commit()

    assert db_session.query(User).count() == 2


def test_space_capacity_must_be_positive(db_session):
    from app.spaces.models import Space

    db_session.add(
        Space(name="Lab", space_type="LABORATORIO", capacity=0, location="Edificio A")
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_reservation_interval_must_have_positive_duration(db_session):
    from datetime import datetime, timezone

    from app.reservations.models import Reservation, ReservationStatus
    from app.roles.models import Role
    from app.spaces.models import Space
    from app.users.models import User

    user = User(email="student@uni.edu", password_hash="hash")
    role = Role(name="ESTUDIANTE")
    space = Space(name="Lab", space_type="LABORATORIO", capacity=10, location="Edificio A")
    db_session.add_all([user, role, space])
    db_session.flush()
    db_session.add(
        Reservation(
            requester=user,
            space=space,
            starts_at=datetime(2026, 10, 22, 10, tzinfo=timezone.utc),
            ends_at=datetime(2026, 10, 22, 10, tzinfo=timezone.utc),
            status=ReservationStatus.PENDIENTE,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_reservation_status_is_limited_to_specified_values(db_session):
    from datetime import datetime, timezone

    from app.reservations.models import Reservation
    from app.spaces.models import Space
    from app.users.models import User

    user = User(email="student@uni.edu", password_hash="hash")
    space = Space(name="Lab", space_type="LABORATORIO", capacity=10, location="Edificio A")
    db_session.add_all([user, space])
    db_session.flush()
    db_session.add(
        Reservation(
            requester=user,
            space=space,
            starts_at=datetime(2026, 10, 22, 10, tzinfo=timezone.utc),
            ends_at=datetime(2026, 10, 22, 11, tzinfo=timezone.utc),
            status="NO_VALIDO",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_space_with_reservations_cannot_be_deleted(db_session):
    from datetime import datetime, timezone

    from app.reservations.models import Reservation, ReservationStatus
    from app.spaces.models import Space
    from app.users.models import User

    user = User(email="student@uni.edu", password_hash="hash")
    space = Space(name="Lab", space_type="LABORATORIO", capacity=10, location="Edificio A")
    db_session.add_all([user, space])
    db_session.flush()
    db_session.add(
        Reservation(
            requester=user,
            space=space,
            starts_at=datetime(2026, 10, 22, 10, tzinfo=timezone.utc),
            ends_at=datetime(2026, 10, 22, 11, tzinfo=timezone.utc),
            status=ReservationStatus.PENDIENTE,
        )
    )
    db_session.commit()
    db_session.delete(space)

    with pytest.raises(IntegrityError):
        db_session.commit()
