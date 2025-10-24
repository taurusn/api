"""
User and Profile-related Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .auth import UserRole

# Base schemas
class BaseResponse(BaseModel):
    """Base response schema with common fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime

# User schemas
class UserBase(BaseModel):
    """Base user fields"""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Valid email address")
    role: UserRole = Field(..., description="User role")

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, description="Password for the user")

class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Updated full name")
    email: Optional[EmailStr] = Field(None, description="Updated email address")

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
    university: Optional[str] = Field(None, max_length=120, description="University name")
    major: Optional[str] = Field(None, max_length=120, description="Field of study")
    graduation_year: Optional[int] = Field(None, ge=1900, le=2050, description="Expected graduation year")
    resume_url: Optional[str] = Field(None, description="URL to resume file")
    bio: Optional[str] = Field(None, description="Student biography")

class StudentProfileCreate(StudentProfileBase):
    """Student profile creation schema"""
    pass

class StudentProfileUpdate(StudentProfileBase):
    """Student profile update schema"""
    pass

class StudentProfileResponse(BaseResponse, StudentProfileBase):
    """Student profile response schema"""
    user_id: int = Field(..., description="ID of the associated user")

# Company profile schemas
class CompanyProfileBase(BaseModel):
    """Base company profile fields"""
    company_name: str = Field(..., min_length=2, max_length=120, description="Company name")
    website_url: Optional[str] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description")

class CompanyProfileCreate(CompanyProfileBase):
    """Company profile creation schema"""
    pass

class CompanyProfileUpdate(BaseModel):
    """Company profile update schema"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=120, description="Updated company name")
    website_url: Optional[str] = Field(None, description="Updated website URL")
    description: Optional[str] = Field(None, description="Updated company description")

class CompanyProfileResponse(BaseResponse, CompanyProfileBase):
    """Company profile response schema"""
    user_id: int = Field(..., description="ID of the associated user")

# Update forward references for relationships
UserProfile.model_rebuild()