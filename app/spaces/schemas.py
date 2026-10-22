"""Esquemas de entrada y salida para espacios académicos."""

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    space_type: str = Field(min_length=1, max_length=40)
    capacity: int = Field(gt=0)
    location: str = Field(min_length=1, max_length=255)


class SpaceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    space_type: str | None = Field(default=None, min_length=1, max_length=40)
    capacity: int | None = Field(default=None, gt=0)
    location: str | None = Field(default=None, min_length=1, max_length=255)


class SpaceStatusUpdate(BaseModel):
    is_active: bool


class SpacePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    space_type: str
    capacity: int
    location: str
    is_active: bool
