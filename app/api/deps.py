"""FastAPI dependencies."""
from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, db_manager
from app.core.security import decode_token, verify_token_type, get_token_subject
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.repositories.user import UserRepository
from app.models.user import User, UserRole
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.product import ProductService
from app.services.order import OrderService


# Database dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with db_manager.session() as session:
        yield session


# Repository dependencies
async def get_user_repo(db: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(db)


# Service dependencies
async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(db)


async def get_product_service(db: AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(db)


async def get_order_service(db: AsyncSession = Depends(get_db_session)) -> OrderService:
    return OrderService(db)


# Authentication dependencies
async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Get current authenticated user from JWT token."""
    if not authorization:
        raise AuthenticationError("Authorization header missing")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("Invalid authentication scheme")
    except ValueError:
        raise AuthenticationError("Invalid authorization header format")

    return await auth_service.verify_token(token)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise AuthorizationError("Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current admin user."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise AuthorizationError("Admin access required")
    return current_user


async def get_current_superadmin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current superadmin user."""
    if current_user.role != UserRole.SUPERADMIN:
        raise AuthorizationError("Superadmin access required")
    return current_user


# Optional authentication (for public endpoints that can benefit from auth)
async def get_optional_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return await auth_service.verify_token(token)
    except Exception:
        return None


# Rate limiting dependency (placeholder - implement with Redis in production)
async def rate_limiter(request: Request) -> None:
    """Rate limiting dependency."""
    # TODO: Implement with Redis
    pass