"""User repository."""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.user import User, UserRole
from app.schemas.user import UserCreateInternal, UserUpdate


class UserRepository(BaseRepository[User, UserCreateInternal, UserUpdate]):
    """User repository with custom queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_email_with_relations(self, email: str) -> Optional[User]:
        """Get user by email with relationships loaded."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.refresh_tokens))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_user(self, user_id: int) -> Optional[User]:
        """Get active user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """List users with filters."""
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if role is not None:
            query = query.where(User.role == role)
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )

        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_users(
        self,
        is_active: Optional[bool] = None,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
    ) -> int:
        """Count users with filters."""
        query = select(func.count(User.id))

        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if role is not None:
            query = query.where(User.role == role)
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime, timezone
        await self.db.execute(
            select(User).where(User.id == user_id)
        )
        # Note: Add last_login column to User model if needed