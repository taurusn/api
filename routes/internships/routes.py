"""
Role-Aware Internship Routes
Same endpoints, different behavior based on user role using middleware
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from core.database import get_database_session
from core.middleware import (
    get_current_user, get_current_user_role, get_current_user_id,
    require_company_user, require_student_user
)
from schemas.user import UserResponse
from schemas.auth import UserRole
from schemas.company_schemas import (
    CompanyInternshipCreate, CompanyInternshipUpdate, CompanyInternshipResponse,
    CompanyInternshipList, CompanyInternshipFilters, InternshipStatusUpdate
)
from logic.company.internship_service import company_service

router = APIRouter(prefix="/internships", tags=["internships"])


@router.post(
    "/",
    response_model=CompanyInternshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Internship",
    description="Create a new internship post. Only accessible by companies."
)
async def create_internship(
    internship_data: CompanyInternshipCreate,
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(require_company_user),
    company_id: int = Depends(get_current_user_id)
):
    """
    Create a new internship post.
    
    **Company Access Only**: This endpoint requires company authentication.
    The internship will be automatically associated with the authenticated company.
    
    **Request Body**:
    - title: Internship title (5-150 chars)
    - description: Detailed job description (min 20 chars)  
    - category: Job category/field
    - type: Work arrangement (remote/onsite/hybrid)
    - duration_weeks: Duration in weeks (1-52)
    - location: Work location (optional)
    - requirements: Skills and qualifications (optional)
    - benefits: Internship benefits (optional)
    - salary_min/max: Salary range (optional)
    - application_deadline: Application deadline (optional)
    - status: Initial status (default: draft)
    
    **Returns**: Created internship details with analytics
    """
    return await company_service.create_internship(db, internship_data, company_id)


@router.get(
    "/",
    response_model=CompanyInternshipList,
    summary="List Internships",
    description="Get internships list. Role-aware: Companies see their internships, Students see all active internships."
)
async def list_internships(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    type: Optional[str] = Query(None, description="Filter by work type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(get_current_user),
    user_role: UserRole = Depends(get_current_user_role),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get paginated internships list with role-based filtering.
    
    **Role-Aware Behavior**:
    - **Companies**: See only their own internships with detailed analytics
    - **Students**: See all active internships (public view) 
    - **Admin**: See all internships across all companies
    
    **Query Parameters**:
    - page: Page number (default: 1)
    - size: Items per page (max: 50, default: 10)
    - status: Filter by internship status
    - category: Filter by job category
    - type: Filter by work arrangement
    - location: Filter by location
    
    **Returns**: Paginated list with different data based on role
    """
    if user_role == UserRole.COMPANY:
        # Companies see their own internships with analytics
        filters = CompanyInternshipFilters(
            status=status,
            category=category,
            type=type,
            location=location
        )
        return await company_service.get_company_internships(db, user_id, page, size, filters)
    
    elif user_role == UserRole.STUDENT:
        # Students see all active internships (implement student service later)
        # For now, return empty list with TODO comment
        return CompanyInternshipList(
            items=[],
            total=0,
            page=page,
            size=size,
            has_next=False,
            has_prev=False
        )
        # TODO: Implement student_service.get_available_internships()
    
    else:  # Admin role
        # Admins see all internships (implement admin service later)
        return CompanyInternshipList(
            items=[],
            total=0,
            page=page,
            size=size,
            has_next=False,
            has_prev=False
        )
        # TODO: Implement admin_service.get_all_internships()


# Health check endpoint for internships service (must be before /{internship_id})
@router.get("/health", include_in_schema=False)
async def internships_health():
    """Health check for internships service"""
    return {"service": "internships", "status": "healthy", "timestamp": "2025-10-25"}


@router.get(
    "/{internship_id}",
    response_model=CompanyInternshipResponse,
    summary="Get Internship Details",
    description="Get specific internship details. Role-aware access control."
)
async def get_internship(
    internship_id: int,
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(get_current_user),
    user_role: UserRole = Depends(get_current_user_role),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get detailed internship information.
    
    **Role-Aware Access**:
    - **Companies**: Can access their own internships with full analytics
    - **Students**: Can access any active internship (public view)
    - **Admin**: Can access any internship
    
    **Path Parameters**:
    - internship_id: Unique internship identifier
    
    **Returns**: Internship details with role-appropriate data
    """
    if user_role == UserRole.COMPANY:
        # Companies access their own internships
        return await company_service.get_internship_by_id(db, internship_id, user_id)
    
    elif user_role == UserRole.STUDENT:
        # Students access public internship view
        # TODO: Implement student_service.get_public_internship()
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Student internship view not implemented yet"
        )
    
    else:  # Admin role
        # TODO: Implement admin_service.get_internship()
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Admin internship view not implemented yet"
        )


@router.patch(
    "/{internship_id}",
    response_model=CompanyInternshipResponse,
    summary="Update Internship",
    description="Update internship details. Company access only."
)
async def update_internship(
    internship_id: int,
    update_data: CompanyInternshipUpdate,
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(require_company_user),
    company_id: int = Depends(get_current_user_id)
):
    """
    Update internship details.
    
    **Company Access Only**: Only the company that owns the internship can update it.
    
    **Path Parameters**:
    - internship_id: Internship to update
    
    **Request Body**: Partial update data (only provided fields will be updated)
    
    **Returns**: Updated internship details
    """
    return await company_service.update_internship(db, internship_id, company_id, update_data)


@router.patch(
    "/{internship_id}/status",
    response_model=CompanyInternshipResponse,
    summary="Update Internship Status",
    description="Update internship status with validation. Company access only."
)
async def update_internship_status(
    internship_id: int,
    status_update: InternshipStatusUpdate,
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(require_company_user),
    company_id: int = Depends(get_current_user_id)
):
    """
    Update internship status with business rule validation.
    
    **Company Access Only**: Only the company that owns the internship can change status.
    
    **Path Parameters**:
    - internship_id: Internship to update
    
    **Request Body**:
    - status: New status (draft/active/paused/closed/expired)
    - reason: Optional reason for status change
    
    **Status Transitions**:
    - draft → active, closed
    - active → paused, closed
    - paused → active, closed
    - expired → active
    - closed → (no transitions)
    
    **Returns**: Updated internship with new status
    """
    return await company_service.update_internship_status(db, internship_id, company_id, status_update)


@router.delete(
    "/{internship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Internship", 
    description="Delete internship (soft delete if has applications). Company access only."
)
async def delete_internship(
    internship_id: int,
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(require_company_user),
    company_id: int = Depends(get_current_user_id)
):
    """
    Delete internship post.
    
    **Company Access Only**: Only the company that owns the internship can delete it.
    
    **Deletion Logic**:
    - If no applications: Hard delete (remove from database)
    - If has applications: Soft delete (set status to closed)
    
    **Path Parameters**:
    - internship_id: Internship to delete
    
    **Returns**: 204 No Content on success
    """
    await company_service.delete_internship(db, internship_id, company_id)


