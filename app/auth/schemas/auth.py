from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.users.schemas.user import UserResponseSchema
from app.utils.schemas import CamelCaseModel


class RegisterRequestSchema(CamelCaseModel):
    email: EmailStr
    # bcrypt reads at most 72 bytes of a password, so longer ones are rejected instead of silently cut.
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=60)


class LoginRequestSchema(CamelCaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class AuthenticationResponseSchema(CamelCaseModel):
    token: str
    user: UserResponseSchema


class CurrentUser(BaseModel):
    """The signed-in user as every endpoint sees it: taken from the token, checked against the database."""

    id: int
    email: str
    display_name: str
    created_at: datetime


class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
