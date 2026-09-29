"""User API endpoints."""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional

from app.api.deps import (
    get_user_service,
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
)
from app.services.user import UserService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdateMe,
    UserResponse,
    UserListResponse,
)
from app.models.user import User, UserRole

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new user (admin only)."""
    return await user_service.create(user_data, is_admin=True)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user's profile."""
    return await user_service.get_me(current_user.id)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdateMe,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user's profile."""
    return await user_service.update_me(current_user.id, user_data)


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
):
    """List users (admin only)."""
    return await user_service.list(page, size, is_active, role, search, is_admin=True)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get user by ID."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    return await user_service.get(user_id, current_user.id, is_admin)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update a user."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    return await user_service.update(user_id, user_data, current_user.id, is_admin)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    """Delete (deactivate) a user."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    await user_service.delete(user_id, current_user.id, is_admin)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Activate a user (admin only)."""
    return await user_service.activate(user_id, is_admin=True)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Deactivate a user (admin only)."""
    return await user_service.deactivate(user_id, is_admin=True)