"""
Common response schemas and wrappers
"""
from pydantic import BaseModel, Field
from typing import Optional, Any


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = Field(default=True, description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    code: Optional[str] = Field(None, description="Error code")


class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    code: str = Field(..., description="Error code")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details"""
    validation_errors: list[ValidationError] = Field(..., description="List of validation errors")