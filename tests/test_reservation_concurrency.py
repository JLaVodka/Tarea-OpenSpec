"""Prueba de concurrencia para evitar solicitudes propias duplicadas."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

from sqlalchemy.orm import Session

from app.reservations.models import Reservation
from app.reservations.service import ReservationConflict, create_reservation
from app.roles.policy import seed_role_permissions
from app.spaces.models import Space
from app.users.models import User
from app.users.security import hash_password


def test_simultaneous_own_overlapping_requests_create_at_most_one(db_session):
    roles = seed_role_permissions(db_session)
    student = User(email="concurrent@university.edu", password_hash=hash_password("test password"))
    student.roles.append(roles["ESTUDIANTE"])
    space = Space(
        name="Sala concurrente",
        space_type="SALA_COMPUTO",
        capacity=20,
        location="Edificio B",
        is_active=True,
    )
    db_session.add_all([student, space])
    db_session.commit()
    student_id, space_id = student.id, space.id
    begins = datetime.now(timezone.utc) + timedelta(days=5)
    ends = begins + timedelta(hours=1)
    barrier = Barrier(2)

    def submit_request():
        with Session(db_session.bind) as session:
            requester = session.get(User, student_id)
            barrier.wait()
            try:
                create_reservation(session, requester, space_id, begins, ends)
                return "created"
            except ReservationConflict:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: submit_request(), range(2)))

    assert sorted(results) == ["conflict", "created"]
    assert db_session.query(Reservation).count() == 1
