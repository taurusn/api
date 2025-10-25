"""
Company-specific Pydantic schemas for enhanced functionality
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .internship import InternshipResponse, InternshipType
from .application import ApplicationResponse, ApplicationStatus
from .common import PaginationParams


class InternshipStatus(str, Enum):
    """Enhanced internship status for company management"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"


class CompanyInternshipCreate(BaseModel):
    """Company internship creation with enhanced fields"""
    title: str = Field(..., min_length=5, max_length=150, description="Internship title")
    description: str = Field(..., min_length=20, description="Detailed job description")
    location: Optional[str] = Field(None, max_length=120, description="Work location")
    category: str = Field(..., max_length=80, description="Job category/field")
    type: InternshipType = Field(default=InternshipType.ONSITE, description="Work arrangement type")
    duration_weeks: int = Field(..., ge=1, le=52, description="Duration in weeks")
    requirements: Optional[str] = Field(None, description="Required skills and qualifications")
    benefits: Optional[str] = Field(None, description="Internship benefits")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary (optional)")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary (optional)")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    status: InternshipStatus = Field(default=InternshipStatus.DRAFT, description="Initial status")


class CompanyInternshipUpdate(BaseModel):
    """Company internship update schema"""
    title: Optional[str] = Field(None, min_length=5, max_length=150)
    description: Optional[str] = Field(None, min_length=20)
    location: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = Field(None, max_length=80)
    type: Optional[InternshipType] = Field(None)
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    requirements: Optional[str] = Field(None)
    benefits: Optional[str] = Field(None)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    application_deadline: Optional[datetime] = Field(None)


class CompanyInternshipResponse(BaseModel):
    """Enhanced internship response for companies"""
    id: int
    title: str
    description: str
    location: Optional[str]
    category: str
    type: InternshipType
    duration_weeks: int
    requirements: Optional[str]
    benefits: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    application_deadline: Optional[datetime]
    status: InternshipStatus
    company_id: int
    posted_at: datetime
    updated_at: Optional[datetime]
    
    # Analytics fields
    total_applications: int = Field(default=0, description="Total number of applications")
    pending_applications: int = Field(default=0, description="Pending applications count")
    views_count: int = Field(default=0, description="Number of views")


class InternshipStatusUpdate(BaseModel):
    """Schema for updating internship status"""
    status: InternshipStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class CompanyInternshipList(BaseModel):
    """Paginated company internship list"""
    items: List[CompanyInternshipResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class CompanyInternshipFilters(BaseModel):
    """Company internship filtering options"""
    status: Optional[InternshipStatus] = Field(None, description="Filter by status")
    category: Optional[str] = Field(None, description="Filter by category")
    type: Optional[InternshipType] = Field(None, description="Filter by work type")
    location: Optional[str] = Field(None, description="Filter by location")
    date_from: Optional[datetime] = Field(None, description="Posted after date")
    date_to: Optional[datetime] = Field(None, description="Posted before date")


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status by company"""
    status: ApplicationStatus = Field(..., description="New application status")
    company_notes: Optional[str] = Field(None, description="Internal company notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection (if applicable)")


class CompanyApplicationResponse(BaseModel):
    """Enhanced application response for companies"""
    id: int
    internship_id: int
    student_id: int
    cover_letter: Optional[str]
    status: ApplicationStatus
    applied_at: datetime
    updated_at: Optional[datetime]
    company_notes: Optional[str]
    rejection_reason: Optional[str]
    
    # Student information (limited for privacy)
    student_name: str
    student_email: str
    student_phone: Optional[str]
    
    # Internship title for context
    internship_title: str


class CompanyApplicationList(BaseModel):
    """Paginated company application list"""
    items: List[CompanyApplicationResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class CompanyApplicationFilters(BaseModel):
    """Company application filtering options"""
    status: Optional[ApplicationStatus] = Field(None, description="Filter by status")
    internship_id: Optional[int] = Field(None, description="Filter by specific internship")
    date_from: Optional[datetime] = Field(None, description="Applied after date")
    date_to: Optional[datetime] = Field(None, description="Applied before date")
    student_name: Optional[str] = Field(None, description="Search by student name")


class CompanyDashboardStats(BaseModel):
    """Company dashboard statistics"""
    total_internships: int
    active_internships: int
    draft_internships: int
    total_applications: int
    pending_applications: int
    accepted_applications: int
    rejected_applications: int
    
    # Recent activity
    recent_applications: List[CompanyApplicationResponse]
    top_internships: List[CompanyInternshipResponse]
    
    # Time-based metrics
    applications_this_week: int
    applications_this_month: int
    avg_applications_per_internship: float


class BulkStatusUpdate(BaseModel):
    """Schema for bulk status updates"""
    application_ids: List[int] = Field(..., description="List of application IDs")
    status: ApplicationStatus = Field(..., description="New status for all applications")
    company_notes: Optional[str] = Field(None, description="Notes applied to all applications")


class InternshipAnalytics(BaseModel):
    """Analytics for specific internship"""
    internship_id: int
    total_views: int
    total_applications: int
    conversion_rate: float  # applications/views
    status_breakdown: dict  # {status: count}
    application_timeline: List[dict]  # [{date: str, count: int}]
    top_applicant_skills: List[str]