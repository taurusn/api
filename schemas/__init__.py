# Schemas package - Pydantic request/response models

from .user import (
    UserRole, InternshipType, ApplicationStatus,
    UserLogin, UserRegister, Token, TokenData,
    UserCreate, UserUpdate, UserResponse, UserProfile,
    StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse,
    CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse,
    InternshipCreate, InternshipUpdate, InternshipResponse, InternshipList,
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationList,
    APIResponse, ErrorResponse
)

from .common import (
    PaginationParams, PaginatedResponse,
    HealthCheck, MessageResponse
)

__all__ = [
    # Enums
    "UserRole", "InternshipType", "ApplicationStatus",
    
    # Auth schemas
    "UserLogin", "UserRegister", "Token", "TokenData",
    
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserProfile",
    
    # Student schemas
    "StudentProfileCreate", "StudentProfileUpdate", "StudentProfileResponse",
    
    # Company schemas
    "CompanyProfileCreate", "CompanyProfileUpdate", "CompanyProfileResponse",
    
    # Internship schemas
    "InternshipCreate", "InternshipUpdate", "InternshipResponse", "InternshipList",
    
    # Application schemas
    "ApplicationCreate", "ApplicationUpdate", "ApplicationResponse", "ApplicationList",
    
    # Response schemas
    "APIResponse", "ErrorResponse",
    
    # Common schemas
    "PaginationParams", "PaginatedResponse", "HealthCheck", "MessageResponse"
]