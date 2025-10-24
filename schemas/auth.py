"""
Authentication-related Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class UserRegister(BaseModel):
    """User registration request schema"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: UserRole = Field(default=UserRole.STUDENT, description="User role")


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data schema"""
    email: Optional[str] = Field(None, description="User email from token")
    user_id: Optional[int] = Field(None, description="User ID from token")
    role: Optional[str] = Field(None, description="User role from token")


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password")


class ChangePassword(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")