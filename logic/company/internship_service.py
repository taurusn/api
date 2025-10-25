"""
Company Service - Business logic for company-related operations
Integrates with authentication middleware for secure operations
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from models.user import Internship, Application, User
from schemas.company_schemas import (
    CompanyInternshipCreate, CompanyInternshipUpdate, CompanyInternshipResponse,
    CompanyInternshipList, CompanyInternshipFilters, InternshipStatus,
    InternshipStatusUpdate, CompanyApplicationResponse, CompanyApplicationList,
    CompanyApplicationFilters, ApplicationStatusUpdate, CompanyDashboardStats,
    BulkStatusUpdate, InternshipAnalytics
)
from schemas.application import ApplicationStatus
from core.database import get_database_session


class CompanyService:
    """Service class for company-specific business logic"""
    
    def __init__(self):
        pass
    
    # ==================== INTERNSHIP MANAGEMENT ====================
    
    async def create_internship(
        self, 
        db: Session, 
        internship_data: CompanyInternshipCreate, 
        company_id: int
    ) -> CompanyInternshipResponse:
        """
        Create a new internship post for a company
        
        Args:
            db: Database session
            internship_data: Internship creation data
            company_id: ID of the company creating the internship (from middleware)
        
        Returns:
            Created internship response
        """
        try:
            # Validate salary range
            if (internship_data.salary_min and internship_data.salary_max and 
                internship_data.salary_min > internship_data.salary_max):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Minimum salary cannot be greater than maximum salary"
                )
            
            # Create internship instance
            current_time = datetime.utcnow()
            db_internship = Internship(
                **internship_data.model_dump(),
                company_id=company_id,
                posted_at=current_time,
                updated_at=current_time
            )
            
            db.add(db_internship)
            db.commit()
            db.refresh(db_internship)
            
            return self._internship_to_response(db_internship)
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create internship: {str(e)}"
            )
    
    async def get_company_internships(
        self,
        db: Session,
        company_id: int,
        page: int = 1,
        size: int = 10,
        filters: Optional[CompanyInternshipFilters] = None
    ) -> CompanyInternshipList:
        """
        Get paginated list of company's internships with filters
        
        Args:
            db: Database session
            company_id: Company ID (from middleware)
            page: Page number
            size: Items per page
            filters: Optional filters
        
        Returns:
            Paginated internship list
        """
        try:
            query = db.query(Internship).filter(Internship.company_id == company_id)
            
            # Apply filters
            if filters:
                if filters.status:
                    query = query.filter(Internship.status == filters.status)
                if filters.category:
                    query = query.filter(Internship.category.ilike(f"%{filters.category}%"))
                if filters.type:
                    query = query.filter(Internship.type == filters.type)
                if filters.location:
                    query = query.filter(Internship.location.ilike(f"%{filters.location}%"))
                if filters.date_from:
                    query = query.filter(Internship.posted_at >= filters.date_from)
                if filters.date_to:
                    query = query.filter(Internship.posted_at <= filters.date_to)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * size
            internships = (
                query.order_by(desc(Internship.posted_at))
                .offset(offset)
                .limit(size)
                .all()
            )
            
            # Convert to response format with analytics
            items = []
            for internship in internships:
                response = self._internship_to_response(internship)
                # Add analytics data
                response.total_applications = self._get_internship_applications_count(db, internship.id)
                response.pending_applications = self._get_internship_pending_count(db, internship.id)
                items.append(response)
            
            return CompanyInternshipList(
                items=items,
                total=total,
                page=page,
                size=size,
                has_next=page * size < total,
                has_prev=page > 1
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve internships: {str(e)}"
            )
    
    async def get_internship_by_id(
        self,
        db: Session,
        internship_id: int,
        company_id: int
    ) -> CompanyInternshipResponse:
        """
        Get specific internship by ID (with ownership verification)
        
        Args:
            db: Database session
            internship_id: Internship ID
            company_id: Company ID (from middleware)
        
        Returns:
            Internship details
        """
        internship = db.query(Internship).filter(
            and_(Internship.id == internship_id, Internship.company_id == company_id)
        ).first()
        
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Internship not found or access denied"
            )
        
        response = self._internship_to_response(internship)
        
        # Add analytics
        response.total_applications = self._get_internship_applications_count(db, internship.id)
        response.pending_applications = self._get_internship_pending_count(db, internship.id)
        
        return response
    
    async def update_internship(
        self,
        db: Session,
        internship_id: int,
        company_id: int,
        update_data: CompanyInternshipUpdate
    ) -> CompanyInternshipResponse:
        """
        Update internship details (with ownership verification)
        
        Args:
            db: Database session
            internship_id: Internship ID
            company_id: Company ID (from middleware)
            update_data: Update data
        
        Returns:
            Updated internship
        """
        try:
            internship = db.query(Internship).filter(
                and_(Internship.id == internship_id, Internship.company_id == company_id)
            ).first()
            
            if not internship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Internship not found or access denied"
                )
            
            # Validate salary range if provided
            salary_min = update_data.salary_min or internship.salary_min
            salary_max = update_data.salary_max or internship.salary_max
            
            if salary_min and salary_max and salary_min > salary_max:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Minimum salary cannot be greater than maximum salary"
                )
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(internship, field, value)
            
            internship.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(internship)
            
            return self._internship_to_response(internship)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update internship: {str(e)}"
            )
    
    async def update_internship_status(
        self,
        db: Session,
        internship_id: int,
        company_id: int,
        status_update: InternshipStatusUpdate
    ) -> CompanyInternshipResponse:
        """
        Update internship status with validation
        
        Args:
            db: Database session
            internship_id: Internship ID
            company_id: Company ID (from middleware)
            status_update: Status update data
        
        Returns:
            Updated internship
        """
        try:
            internship = db.query(Internship).filter(
                and_(Internship.id == internship_id, Internship.company_id == company_id)
            ).first()
            
            if not internship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Internship not found or access denied"
                )
            
            # Validate status transition
            if not self._is_valid_status_transition(internship.status, status_update.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from {internship.status} to {status_update.status}"
                )
            
            old_status = internship.status
            internship.status = status_update.status
            internship.updated_at = datetime.utcnow()
            
            # Log status change (could be enhanced with audit table)
            # For now, just update the internship
            
            db.commit()
            db.refresh(internship)
            
            return self._internship_to_response(internship)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update internship status: {str(e)}"
            )
    
    async def delete_internship(
        self,
        db: Session,
        internship_id: int,
        company_id: int
    ) -> bool:
        """
        Soft delete internship (set status to closed)
        
        Args:
            db: Database session
            internship_id: Internship ID
            company_id: Company ID (from middleware)
        
        Returns:
            Success status
        """
        try:
            internship = db.query(Internship).filter(
                and_(Internship.id == internship_id, Internship.company_id == company_id)
            ).first()
            
            if not internship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Internship not found or access denied"
                )
            
            # Check if internship has applications
            has_applications = db.query(Application).filter(
                Application.internship_id == internship_id
            ).count() > 0
            
            if has_applications:
                # Soft delete - set to closed status
                internship.status = InternshipStatus.CLOSED
                internship.updated_at = datetime.utcnow()
            else:
                # Hard delete if no applications
                db.delete(internship)
            
            db.commit()
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete internship: {str(e)}"
            )
    
    # ==================== HELPER METHODS ====================
    
    def _internship_to_response(self, internship: Internship) -> CompanyInternshipResponse:
        """Convert internship model to response schema"""
        return CompanyInternshipResponse(
            id=internship.id,
            title=internship.title,
            description=internship.description,
            location=internship.location,
            category=internship.category,
            type=internship.type,
            duration_weeks=internship.duration_weeks,
            requirements=getattr(internship, 'requirements', None),
            benefits=getattr(internship, 'benefits', None),
            salary_min=getattr(internship, 'salary_min', None),
            salary_max=getattr(internship, 'salary_max', None),
            application_deadline=getattr(internship, 'application_deadline', None),
            status=getattr(internship, 'status', InternshipStatus.DRAFT),
            company_id=internship.company_id,
            posted_at=internship.posted_at,
            updated_at=getattr(internship, 'updated_at', internship.posted_at)
        )
    
    def _get_internship_applications_count(self, db: Session, internship_id: int) -> int:
        """Get total applications count for internship"""
        return db.query(Application).filter(Application.internship_id == internship_id).count()
    
    def _get_internship_pending_count(self, db: Session, internship_id: int) -> int:
        """Get pending applications count for internship"""
        return db.query(Application).filter(
            and_(
                Application.internship_id == internship_id,
                Application.status == ApplicationStatus.PENDING
            )
        ).count()
    
    def _is_valid_status_transition(self, current_status: InternshipStatus, new_status: InternshipStatus) -> bool:
        """Validate status transition rules"""
        valid_transitions = {
            InternshipStatus.DRAFT: [InternshipStatus.ACTIVE, InternshipStatus.CLOSED],
            InternshipStatus.ACTIVE: [InternshipStatus.PAUSED, InternshipStatus.CLOSED],
            InternshipStatus.PAUSED: [InternshipStatus.ACTIVE, InternshipStatus.CLOSED],
            InternshipStatus.CLOSED: [],  # Cannot transition from closed
            InternshipStatus.EXPIRED: [InternshipStatus.ACTIVE],  # Can reactivate expired
        }
        
        return new_status in valid_transitions.get(current_status, [])


# Global service instance
company_service = CompanyService()