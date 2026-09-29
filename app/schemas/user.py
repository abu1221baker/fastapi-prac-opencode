"""User schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

from app.schemas.base import BaseSchema, TimestampMixin
from app.models.user import UserRole


class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserCreateInternal(UserCreate):
    """Internal schema for creating a user (with hashed password)."""
    hashed_password: str
    is_verified: bool = False


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None


class UserUpdateMe(BaseSchema):
    """Schema for users updating their own profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(None, min_length=8, max_length=128)
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseSchema):
    """Schema for paginated user list."""
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserWithToken(BaseSchema):
    """User response with access token."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"