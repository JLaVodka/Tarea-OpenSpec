"""Contratos públicos de identidad y administración de cuentas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)


class PublicUser(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    roles: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PublicUser


class AccountStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
