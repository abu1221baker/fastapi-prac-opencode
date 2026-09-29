"""Refresh token repository."""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, delete, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.token import RefreshToken
from app.schemas.auth import RefreshTokenRequest


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshToken, RefreshToken]):
    """Refresh token repository."""

    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def get_valid_token(self, token: str) -> Optional[RefreshToken]:
        """Get valid (not expired, not revoked) refresh token."""
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token == token,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_tokens(self, user_id: int) -> List[RefreshToken]:
        """Get all tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(is_revoked=True)
        )
        return result.rowcount > 0

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(and_(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False))
            .values(is_revoked=True)
        )
        return result.rowcount

    async def delete_expired_tokens(self) -> int:
        """Delete all expired tokens."""
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc))
        )
        return result.rowcount

    async def create_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token."""
        refresh_token = RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(refresh_token)
        await self.db.flush()
        await self.db.refresh(refresh_token)
        return refresh_token