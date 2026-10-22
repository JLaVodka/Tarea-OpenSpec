"""Entidades de espacios académicos y responsables asignados."""

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


space_admin_assignments = Table(
    "space_admin_assignments",
    Base.metadata,
    Column("space_id", ForeignKey("spaces.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Space(Base):
    __tablename__ = "spaces"
    __table_args__ = (CheckConstraint("capacity > 0", name="positive_capacity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    space_type: Mapped[str] = mapped_column(String(40), nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    administrators: Mapped[list["User"]] = relationship(secondary=space_admin_assignments)
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="space", passive_deletes="all"
    )
