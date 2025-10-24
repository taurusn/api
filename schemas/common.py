"""
Common schemas and utilities
"""
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar
from datetime import datetime

# Generic type for pagination
T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int):
        """Create paginated response"""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    environment: str
    debug: bool
    timestamp: datetime
    version: str = "1.0.0"

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[list[str]] = None
    
    @classmethod
    def success_response(cls, message: str, data: Optional[dict] = None):
        """Create success response"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str, errors: Optional[list[str]] = None):
        """Create error response"""
        return cls(success=False, message=message, errors=errors)