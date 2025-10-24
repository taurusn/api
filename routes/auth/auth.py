"""
Authentication API routes
FastAPI endpoints for user authentication, registration, and token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_database_session
from schemas.auth import (
    UserLogin, UserRegister, Token, TokenRefresh,
    PasswordReset, PasswordResetConfirm, ChangePassword
)
from schemas.user import UserResponse
from schemas.responses import APIResponse, ErrorResponse
from logic.auth.auth_service import AuthService

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
    }
)

# Security scheme
security = HTTPBearer()

# Initialize auth service
auth_service = AuthService()


@router.post("/register", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_database_session)
):
    """
    Register a new user account
    
    - **full_name**: User's full name
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 6 characters)
    - **role**: User role (student, company, admin)
    """
    try:
        user = await auth_service.register_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return access/refresh tokens"
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_database_session)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token and refresh token for API authentication
    """
    try:
        token = await auth_service.authenticate_user(db, credentials.email, credentials.password)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Generate new access token using refresh token"
)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: Session = Depends(get_database_session)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token
    """
    try:
        token = await auth_service.refresh_access_token(db, refresh_data.refresh_token)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout",
    response_model=APIResponse,
    summary="User logout",
    description="Revoke user's refresh token"
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
):
    """
    Logout user by revoking refresh token
    
    Requires valid access token in Authorization header
    """
    try:
        await auth_service.logout_user(db, credentials.credentials)
        return APIResponse(
            success=True,
            message="Successfully logged out"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current user's profile information"
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
):
    """
    Get current authenticated user's information
    
    Requires valid access token in Authorization header
    """
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/password/reset",
    response_model=APIResponse,
    summary="Request password reset",
    description="Send password reset email to user"
)
async def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_database_session)
):
    """
    Request password reset email
    
    - **email**: User's email address
    
    Sends password reset email if account exists
    """
    try:
        await auth_service.request_password_reset(db, reset_data.email)
        return APIResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    except Exception as e:
        # Always return success for security (don't reveal if email exists)
        return APIResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )


@router.post("/password/reset/confirm",
    response_model=APIResponse,
    summary="Confirm password reset",
    description="Reset password using reset token"
)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_database_session)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 6 characters)
    """
    try:
        await auth_service.reset_password(db, reset_data.token, reset_data.new_password)
        return APIResponse(
            success=True,
            message="Password has been successfully reset"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/password/change",
    response_model=APIResponse,
    summary="Change password",
    description="Change current user's password"
)
async def change_password(
    password_data: ChangePassword,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
):
    """
    Change current user's password
    
    - **current_password**: Current password
    - **new_password**: New password (minimum 6 characters)
    
    Requires valid access token in Authorization header
    """
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        await auth_service.change_password(
            db, user.id, password_data.current_password, password_data.new_password
        )
        return APIResponse(
            success=True,
            message="Password successfully changed"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )