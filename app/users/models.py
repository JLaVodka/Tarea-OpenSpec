"""Entidades de usuarios."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_users_email_normalized",
            func.lower(func.trim(column("email"))),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        back_populates="users",
    )
    administered_spaces: Mapped[list["Space"]] = relationship(
        secondary="space_admin_assignments",
        primaryjoin="User.id == space_admin_assignments.c.user_id",
        secondaryjoin="Space.id == space_admin_assignments.c.space_id",
        viewonly=True,
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="requester", passive_deletes="all"
    )
