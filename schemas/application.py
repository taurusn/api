"""
Application-related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from .user import BaseResponse


class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApplicationBase(BaseModel):
    """Base application fields"""
    cover_letter: Optional[str] = Field(None, description="Cover letter for the application")


class ApplicationCreate(ApplicationBase):
    """Application creation schema"""
    internship_id: int = Field(..., description="ID of the internship to apply for")


class ApplicationUpdate(BaseModel):
    """Application update schema (for company responses)"""
    cover_letter: Optional[str] = Field(None, description="Updated cover letter")
    status: Optional[ApplicationStatus] = Field(None, description="Updated application status")


class ApplicationResponse(BaseResponse, ApplicationBase):
    """Application response schema"""
    internship_id: int = Field(..., description="ID of the applied internship")
    student_id: int = Field(..., description="ID of the student who applied")
    status: ApplicationStatus = Field(..., description="Current application status")
    applied_at: datetime = Field(..., description="When the application was submitted")
    
    # Will be populated by relationships - using dict to avoid circular imports
    internship: Optional[dict] = Field(None, description="Internship information")
    student: Optional[dict] = Field(None, description="Student profile information")


class ApplicationList(BaseModel):
    """Paginated application list response"""
    items: list[ApplicationResponse] = Field(..., description="List of applications")
    total: int = Field(..., description="Total number of applications")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status (company action)"""
    status: ApplicationStatus = Field(..., description="New application status")
    feedback: Optional[str] = Field(None, description="Optional feedback for the applicant")


class ApplicationStats(BaseModel):
    """Application statistics schema"""
    total_applications: int = Field(..., description="Total number of applications")
    pending: int = Field(..., description="Number of pending applications")
    reviewed: int = Field(..., description="Number of reviewed applications")
    accepted: int = Field(..., description="Number of accepted applications")
    rejected: int = Field(..., description="Number of rejected applications")