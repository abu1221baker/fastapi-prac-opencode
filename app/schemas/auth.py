"""Authentication schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class TokenBase(BaseModel):
    """Base token schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class Token(TokenBase):
    """Token response schema."""
    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str
    exp: int
    iat: int
    type: str


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Extend token expiry")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Token response with user info."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation."""
    token: str