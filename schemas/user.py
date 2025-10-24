"""
User-related Pydantic schemas for request/response models
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"

class InternshipType(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# Base schemas
class BaseResponse(BaseModel):
    """Base response schema with common fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime

# Authentication schemas
class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserRegister(BaseModel):
    """User registration request"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.STUDENT

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    """Base user fields"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

class UserResponse(BaseResponse, UserBase):
    """User response schema"""
    pass

class UserProfile(UserResponse):
    """Extended user profile with related data"""
    student_profile: Optional['StudentProfileResponse'] = None
    company_profile: Optional['CompanyProfileResponse'] = None

# Student profile schemas
class StudentProfileBase(BaseModel):
    """Base student profile fields"""
    university: Optional[str] = Field(None, max_length=120)
    major: Optional[str] = Field(None, max_length=120)
    graduation_year: Optional[int] = Field(None, ge=1900, le=2050)
    resume_url: Optional[str] = None
    bio: Optional[str] = None

class StudentProfileCreate(StudentProfileBase):
    """Student profile creation schema"""
    pass

class StudentProfileUpdate(StudentProfileBase):
    """Student profile update schema"""
    pass

class StudentProfileResponse(BaseResponse, StudentProfileBase):
    """Student profile response schema"""
    user_id: int

# Company profile schemas
class CompanyProfileBase(BaseModel):
    """Base company profile fields"""
    company_name: str = Field(..., min_length=2, max_length=120)
    website_url: Optional[str] = None
    description: Optional[str] = None

class CompanyProfileCreate(CompanyProfileBase):
    """Company profile creation schema"""
    pass

class CompanyProfileUpdate(BaseModel):
    """Company profile update schema"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=120)
    website_url: Optional[str] = None
    description: Optional[str] = None

class CompanyProfileResponse(BaseResponse, CompanyProfileBase):
    """Company profile response schema"""
    user_id: int

# Internship schemas
class InternshipBase(BaseModel):
    """Base internship fields"""
    title: str = Field(..., min_length=5, max_length=150)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = Field(None, max_length=80)
    type: InternshipType = InternshipType.ONSITE
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)

class InternshipCreate(InternshipBase):
    """Internship creation schema"""
    pass

class InternshipUpdate(BaseModel):
    """Internship update schema"""
    title: Optional[str] = Field(None, min_length=5, max_length=150)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = Field(None, max_length=80)
    type: Optional[InternshipType] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)

class InternshipResponse(BaseResponse, InternshipBase):
    """Internship response schema"""
    company_id: int
    posted_at: datetime
    company: CompanyProfileResponse

class InternshipList(BaseModel):
    """Paginated internship list response"""
    items: list[InternshipResponse]
    total: int
    page: int
    size: int

# Application schemas
class ApplicationBase(BaseModel):
    """Base application fields"""
    cover_letter: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    """Application creation schema"""
    internship_id: int

class ApplicationUpdate(BaseModel):
    """Application update schema"""
    cover_letter: Optional[str] = None
    status: Optional[ApplicationStatus] = None

class ApplicationResponse(BaseResponse, ApplicationBase):
    """Application response schema"""
    internship_id: int
    student_id: int
    status: ApplicationStatus
    applied_at: datetime
    internship: InternshipResponse
    student: StudentProfileResponse

class ApplicationList(BaseModel):
    """Paginated application list response"""
    items: list[ApplicationResponse]
    total: int
    page: int
    size: int

# API Response wrappers
class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    details: Optional[dict] = None

# Update forward references
UserProfile.model_rebuild()
ApplicationResponse.model_rebuild()
InternshipResponse.model_rebuild()