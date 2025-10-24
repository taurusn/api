# Schemas package - Pydantic request/response models

# Authentication schemas
from .auth import (
    UserRole, UserLogin, UserRegister, Token, TokenData,
    TokenRefresh, PasswordReset, PasswordResetConfirm, ChangePassword
)

# User and profile schemas
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserProfile,
    StudentProfileBase, StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse,
    CompanyProfileBase, CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse,
    BaseResponse
)

# Internship schemas
from .internship import (
    InternshipType, InternshipBase, InternshipCreate, InternshipUpdate,
    InternshipResponse, InternshipList, InternshipSearch
)

# Application schemas
from .application import (
    ApplicationStatus, ApplicationBase, ApplicationCreate, ApplicationUpdate,
    ApplicationResponse, ApplicationList, ApplicationStatusUpdate, ApplicationStats
)

# Response schemas
from .responses import (
    APIResponse, ErrorResponse, ValidationError, ValidationErrorResponse
)

# Common schemas
from .common import (
    PaginationParams, PaginatedResponse, HealthCheck, MessageResponse
)

__all__ = [
    # Enums
    "UserRole", "InternshipType", "ApplicationStatus",
    
    # Auth schemas
    "UserLogin", "UserRegister", "Token", "TokenData",
    "TokenRefresh", "PasswordReset", "PasswordResetConfirm", "ChangePassword",
    
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserProfile",
    
    # Student schemas
    "StudentProfileBase", "StudentProfileCreate", "StudentProfileUpdate", "StudentProfileResponse",
    
    # Company schemas
    "CompanyProfileBase", "CompanyProfileCreate", "CompanyProfileUpdate", "CompanyProfileResponse",
    
    # Internship schemas
    "InternshipBase", "InternshipCreate", "InternshipUpdate", "InternshipResponse", 
    "InternshipList", "InternshipSearch",
    
    # Application schemas
    "ApplicationBase", "ApplicationCreate", "ApplicationUpdate", "ApplicationResponse", 
    "ApplicationList", "ApplicationStatusUpdate", "ApplicationStats",
    
    # Response schemas
    "APIResponse", "ErrorResponse", "ValidationError", "ValidationErrorResponse",
    
    # Common schemas
    "PaginationParams", "PaginatedResponse", "HealthCheck", "MessageResponse",
    "BaseResponse"
]