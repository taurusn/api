"""
Internship-related Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from .user import BaseResponse


class InternshipType(str, Enum):
    """Internship work type enumeration"""
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class InternshipBase(BaseModel):
    """Base internship fields"""
    title: str = Field(..., min_length=5, max_length=150, description="Internship title")
    description: Optional[str] = Field(None, description="Detailed job description")
    location: Optional[str] = Field(None, max_length=120, description="Work location")
    category: Optional[str] = Field(None, max_length=80, description="Job category/field")
    type: InternshipType = Field(default=InternshipType.ONSITE, description="Work arrangement type")
    duration_weeks: Optional[int] = Field(None, ge=1, le=52, description="Duration in weeks")


class InternshipCreate(InternshipBase):
    """Internship creation schema"""
    pass


class InternshipUpdate(BaseModel):
    """Internship update schema"""
    title: Optional[str] = Field(None, min_length=5, max_length=150, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    location: Optional[str] = Field(None, max_length=120, description="Updated location")
    category: Optional[str] = Field(None, max_length=80, description="Updated category")
    type: Optional[InternshipType] = Field(None, description="Updated work type")
    duration_weeks: Optional[int] = Field(None, ge=1, le=52, description="Updated duration")


class InternshipResponse(BaseResponse, InternshipBase):
    """Internship response schema"""
    company_id: int = Field(..., description="Company that posted the internship")
    posted_at: datetime = Field(..., description="When the internship was posted")
    
    # Will be populated by relationship - using TYPE_CHECKING to avoid circular imports
    company: Optional[dict] = Field(None, description="Company profile information")


class InternshipList(BaseModel):
    """Paginated internship list response"""
    items: list[InternshipResponse] = Field(..., description="List of internships")
    total: int = Field(..., description="Total number of internships")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")


class InternshipSearch(BaseModel):
    """Internship search filters"""
    title: Optional[str] = Field(None, description="Search by title")
    location: Optional[str] = Field(None, description="Filter by location")
    category: Optional[str] = Field(None, description="Filter by category")
    type: Optional[InternshipType] = Field(None, description="Filter by work type")
    company_name: Optional[str] = Field(None, description="Filter by company name")