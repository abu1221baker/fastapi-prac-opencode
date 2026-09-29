"""Authentication service."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    get_token_subject,
)
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.repositories.user import UserRepository
from app.repositories.token import RefreshTokenRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, PasswordChangeRequest
from app.schemas.user import UserCreate, UserCreateInternal, UserResponse


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def register(self, user_data: UserCreate) -> UserResponse:
        """Register a new user."""
        # Check if email exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already registered")

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user_in = UserCreateInternal(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            is_verified=False,
        )
        user = await self.user_repo.create(user_in)

        return UserResponse.model_validate(user)

    async def login(
        self,
        login_data: LoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Authenticate user and return tokens."""
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        if not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        return await self._create_tokens(user, login_data.remember_me, user_agent, ip_address)

    async def refresh_access_token(
        self,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Refresh access token using refresh token."""
        # Validate refresh token
        token_record = await self.token_repo.get_valid_token(refresh_token)
        if not token_record:
            raise TokenInvalidError()

        # Get user
        user = await self.user_repo.get_active_user(token_record.user_id)
        if not user:
            raise AuthenticationError("User not found or inactive")

        # Revoke old refresh token (rotation)
        await self.token_repo.revoke_token(refresh_token)

        # Create new tokens
        return await self._create_tokens(user, True, user_agent, ip_address)

    async def logout(self, refresh_token: str) -> bool:
        """Revoke refresh token (logout)."""
        return await self.token_repo.revoke_token(refresh_token)

    async def logout_all_devices(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        return await self.token_repo.revoke_all_user_tokens(user_id)

    async def change_password(self, user_id: int, password_data: PasswordChangeRequest) -> bool:
        """Change user password."""
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValidationError("User not found")

        if not verify_password(password_data.current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")

        user.hashed_password = get_password_hash(password_data.new_password)
        await self.db.flush()

        # Revoke all tokens to force re-login
        await self.token_repo.revoke_all_user_tokens(user_id)
        return True

    async def verify_token(self, token: str) -> User:
        """Verify access token and return user."""
        try:
            payload = decode_token(token)
        except ValueError:
            raise TokenInvalidError()

        if not verify_token_type(payload, "access"):
            raise TokenInvalidError()

        subject = get_token_subject(payload)
        if not subject:
            raise TokenInvalidError()

        user = await self.user_repo.get_active_user(int(subject))
        if not user:
            raise AuthenticationError("User not found")

        return user

    async def _create_tokens(
        self,
        user: User,
        remember_me: bool,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Create access and refresh tokens."""
        # Access token
        access_expire = timedelta(minutes=30) if remember_me else timedelta(minutes=15)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_expire,
            additional_claims={"role": user.role.value, "email": user.email},
        )

        # Refresh token
        refresh_expire = timedelta(days=30) if remember_me else timedelta(days=7)
        refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=refresh_expire,
        )

        # Store refresh token
        expires_at = datetime.now(timezone.utc) + refresh_expire
        await self.token_repo.create_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expire.total_seconds()),
        )