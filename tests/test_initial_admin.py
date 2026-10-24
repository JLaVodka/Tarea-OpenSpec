"""Provisión local del primer administrador del sistema."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.roles.models import Role
from app.users.models import User
from app.users.security import verify_password


def test_initial_admin_is_created_with_hashed_password(db_session):
    from app.users.bootstrap_admin import create_initial_admin

    with db_session.begin():
        admin = create_initial_admin(
            db_session, "  Admin@University.edu ", "UnaClaveSegura123"
        )

    stored = db_session.scalar(select(User).where(User.id == admin.id))
    assert stored.email == "admin@university.edu"
    assert [role.name for role in stored.roles] == ["ADMIN_SISTEMA"]
    assert stored.password_hash != "UnaClaveSegura123"
    assert verify_password("UnaClaveSegura123", stored.password_hash)


def test_initial_admin_refuses_to_replace_existing_admin(db_session):
    from app.users.bootstrap_admin import AdminAlreadyExists, create_initial_admin

    with db_session.begin():
        create_initial_admin(db_session, "first@university.edu", "first-password")

    with pytest.raises(AdminAlreadyExists):
        with db_session.begin():
            create_initial_admin(db_session, "second@university.edu", "second-password")

    assert db_session.scalar(select(User).where(User.email == "first@university.edu"))
    assert db_session.scalar(select(User).where(User.email == "second@university.edu")) is None
    assert db_session.scalar(select(User).join(User.roles).where(Role.name == "ADMIN_SISTEMA")).email == "first@university.edu"


@pytest.mark.parametrize(
    ("email", "password"),
    [("not-an-email", "some-password"), ("valid@university.edu", "")],
)
def test_initial_admin_rejects_invalid_credentials(db_session, email, password):
    from app.users.bootstrap_admin import InvalidProvisionCredentials, create_initial_admin

    with pytest.raises(InvalidProvisionCredentials):
        with db_session.begin():
            create_initial_admin(db_session, email, password)

    assert db_session.scalar(select(User).limit(1)) is None


def test_cli_hides_password_and_does_not_print_it(db_session, monkeypatch, capsys):
    from app.users import bootstrap_admin

    factory = sessionmaker(bind=db_session.get_bind(), expire_on_commit=False)
    monkeypatch.setattr(bootstrap_admin, "SessionLocal", factory)
    monkeypatch.setattr("builtins.input", lambda _prompt: "admin@university.edu")
    monkeypatch.setattr("getpass.getpass", lambda _prompt: "never-print-this-password")

    bootstrap_admin.main()

    output = capsys.readouterr().out
    assert "Administrador inicial creado" in output
    assert "never-print-this-password" not in output
    assert db_session.scalar(select(User).where(User.email == "admin@university.edu"))
