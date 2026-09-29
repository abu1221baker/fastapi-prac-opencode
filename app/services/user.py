"""User service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, ConflictError, AuthorizationError
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdateMe,
    UserResponse,
    UserListResponse,
)
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password


class UserService:
    """User service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def create(self, user_data: UserCreate, is_admin: bool = False) -> UserResponse:
        """Create a new user."""
        # Check email uniqueness
        existing = await self.repo.get_by_email(user_data.email)
        if existing:
            raise ConflictError("Email already registered")

        # Only admins can create admin users
        if user_data.role != UserRole.USER and not is_admin:
            raise AuthorizationError("Only admins can create admin users")

        from app.schemas.user import UserCreateInternal
        user_in = UserCreateInternal(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_verified=False,
        )
        user = await self.repo.create(user_in)
        return UserResponse.model_validate(user)

    async def get(self, user_id: int, current_user_id: Optional[int] = None, is_admin: bool = False) -> UserResponse:
        """Get user by ID."""
        # Users can only view their own profile unless admin
        if not is_admin and current_user_id and current_user_id != user_id:
            raise AuthorizationError("Not authorized to view this profile")

        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return UserResponse.model_validate(user)

    async def get_me(self, user_id: int) -> UserResponse:
        """Get current user profile."""
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)

    async def update(
        self,
        user_id: int,
        user_data: UserUpdate,
        current_user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> UserResponse:
        """Update a user."""
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        # Permission checks
        if not is_admin:
            if current_user_id != user_id:
                raise AuthorizationError("Not authorized to update this user")
            # Non-admins cannot change role or is_active
            if user_data.role is not None or user_data.is_active is not None:
                raise AuthorizationError("Cannot change role or active status")

        # Check email uniqueness if changing
        if user_data.email and user_data.email != user.email:
            existing = await self.repo.get_by_email(user_data.email)
            if existing:
                raise ConflictError("Email already in use")

        updated = await self.repo.update(user, user_data)
        return UserResponse.model_validate(updated)

    async def update_me(self, user_id: int, user_data: UserUpdateMe) -> UserResponse:
        """Update current user's profile."""
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        update_data = user_data.model_dump(exclude_unset=True)

        # If changing email, check uniqueness
        if "email" in update_data:
            existing = await self.repo.get_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise ConflictError("Email already in use")

        # If changing password, verify current password
        if "new_password" in update_data:
            if not update_data.get("current_password"):
                raise ValidationError("Current password required to change password")
            if not verify_password(update_data["current_password"], user.hashed_password):
                raise ValidationError("Current password is incorrect")
            update_data["hashed_password"] = get_password_hash(update_data["new_password"])

        # Remove password fields from update data
        update_data.pop("current_password", None)
        update_data.pop("new_password", None)

        updated = await self.repo.update(user, update_data)
        return UserResponse.model_validate(updated)

    async def delete(self, user_id: int, current_user_id: Optional[int] = None, is_admin: bool = False) -> bool:
        """Delete a user (soft delete by deactivating)."""
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not is_admin:
            if current_user_id != user_id:
                raise AuthorizationError("Not authorized to delete this user")

        # Soft delete
        user.is_active = False
        await self.db.flush()
        return True

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        is_active: Optional[bool] = None,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_admin: bool = False,
    ) -> UserListResponse:
        """List users (admin only)."""
        if not is_admin:
            raise AuthorizationError("Admin access required")

        skip = (page - 1) * size
        items = await self.repo.list_users(skip, size, is_active, role, search)
        total = await self.repo.count_users(is_active, role, search)

        return UserListResponse(
            items=[UserResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def activate(self, user_id: int, is_admin: bool = False) -> UserResponse:
        """Activate a user (admin only)."""
        if not is_admin:
            raise AuthorizationError("Admin access required")

        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        user.is_active = True
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    async def deactivate(self, user_id: int, is_admin: bool = False) -> UserResponse:
        """Deactivate a user (admin only)."""
        if not is_admin:
            raise AuthorizationError("Admin access required")

        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)