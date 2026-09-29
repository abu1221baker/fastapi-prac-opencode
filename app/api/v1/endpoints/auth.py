"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import (
    get_auth_service,
    get_current_user,
    get_current_active_user,
)
from app.services.auth import AuthService
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    EmailVerificationConfirm,
    MessageResponse,
)
from app.schemas.user import UserResponse, UserCreate
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    return await auth_service.register(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login and get access/refresh tokens."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    return await auth_service.login(login_data, user_agent, ip_address)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    return await auth_service.refresh_access_token(
        refresh_data.refresh_token,
        user_agent,
        ip_address,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout (revoke refresh token)."""
    await auth_service.logout(refresh_data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout from all devices (revoke all refresh tokens)."""
    count = await auth_service.logout_all_devices(current_user.id)
    return MessageResponse(message=f"Logged out from {count} devices")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change user password."""
    await auth_service.change_password(current_user.id, password_data)
    return MessageResponse(message="Password changed successfully. Please login again.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Request password reset (placeholder - implement email sending)."""
    # TODO: Implement email sending with reset token
    # For security, always return success even if email doesn't exist
    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset password with token (placeholder)."""
    # TODO: Implement token verification and password reset
    return MessageResponse(message="Password reset successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verify_data: EmailVerificationConfirm,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify email with token (placeholder)."""
    # TODO: Implement email verification
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    verify_data: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Resend email verification (placeholder)."""
    # TODO: Implement email sending
    return MessageResponse(message="If the email exists, a verification link has been sent")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)