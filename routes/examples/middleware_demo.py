"""
Example Routes using Authentication Middleware
This demonstrates how to use the middleware in real routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_database_session
from core.middleware import (
    get_current_user,
    get_optional_user, 
    admin_required,
    company_required,
    student_required,
    get_current_user_id,
    get_current_user_role
)
from schemas.user import UserResponse
from schemas.auth import UserRole
from schemas.common import APIResponse

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/public")
async def public_endpoint():
    """Public endpoint - no authentication required"""
    return APIResponse(
        success=True,
        message="This is a public endpoint",
        data={"access": "public"}
    )


@router.get("/protected")
async def protected_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Protected endpoint - requires valid JWT token"""
    return APIResponse(
        success=True,
        message=f"Hello {current_user.full_name}",
        data={
            "user_id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        }
    )


@router.get("/admin-only")
async def admin_only_endpoint(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(admin_required)
):
    """Admin only endpoint"""
    return APIResponse(
        success=True,
        message="Admin access granted",
        data={"admin_user": current_user.full_name}
    )


@router.get("/company-dashboard")
async def company_dashboard(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(company_required)
):
    """Company dashboard - companies and admins only"""
    return APIResponse(
        success=True,
        message="Company dashboard access",
        data={
            "user": current_user.full_name,
            "role": current_user.role,
            "dashboard_type": "company"
        }
    )


@router.get("/student-portal")
async def student_portal(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(student_required)
):
    """Student portal - students and admins only"""
    return APIResponse(
        success=True,
        message="Student portal access",
        data={
            "user": current_user.full_name,
            "role": current_user.role,
            "portal_type": "student"
        }
    )


@router.get("/flexible")
async def flexible_endpoint(current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Flexible endpoint - works with or without authentication"""
    if current_user:
        return APIResponse(
            success=True,
            message=f"Welcome back {current_user.full_name}",
            data={
                "authenticated": True,
                "user_id": current_user.id,
                "premium_features": True
            }
        )
    else:
        return APIResponse(
            success=True,
            message="Welcome guest user",
            data={
                "authenticated": False,
                "premium_features": False,
                "suggestion": "Login for more features"
            }
        )


@router.get("/user-id-only")
async def user_id_only_endpoint(user_id: int = Depends(get_current_user_id)):
    """Example using only user ID - more efficient when full user data isn't needed"""
    return APIResponse(
        success=True,
        message="User ID extracted",
        data={"user_id": user_id}
    )


@router.get("/role-based-content")
async def role_based_content(user_role: UserRole = Depends(get_current_user_role)):
    """Different content based on user role"""
    content = {
        UserRole.ADMIN: {
            "dashboard": "admin_dashboard",
            "features": ["user_management", "system_settings", "analytics"],
            "permissions": "full_access"
        },
        UserRole.COMPANY: {
            "dashboard": "company_dashboard", 
            "features": ["post_internships", "manage_applications", "company_profile"],
            "permissions": "company_access"
        },
        UserRole.STUDENT: {
            "dashboard": "student_dashboard",
            "features": ["browse_internships", "apply", "track_applications"],
            "permissions": "student_access"
        }
    }
    
    return APIResponse(
        success=True,
        message=f"Content for {user_role.value} role",
        data=content.get(user_role, {"error": "Unknown role"})
    )


@router.post("/user-specific-action")
async def user_specific_action(
    action_data: dict,  # In real app, use proper Pydantic model
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Example of user-specific business logic"""
    
    # Different logic based on user role
    if current_user.role == UserRole.ADMIN:
        # Admins can perform actions on behalf of others
        result = f"Admin {current_user.full_name} performed system action"
        
    elif current_user.role == UserRole.COMPANY:
        # Companies can only manage their own data
        result = f"Company {current_user.full_name} updated company data"
        
    elif current_user.role == UserRole.STUDENT:
        # Students can only manage their own profile/applications
        result = f"Student {current_user.full_name} updated profile"
        
    else:
        raise HTTPException(status_code=403, detail="Unknown role")
    
    return APIResponse(
        success=True,
        message="Action completed successfully",
        data={
            "action": result,
            "performed_by": current_user.id,
            "role": current_user.role
        }
    )


@router.get("/complex-permissions")
async def complex_permissions_example(current_user: UserResponse = Depends(get_current_user)):
    """Example of complex permission logic"""
    
    # Check multiple conditions
    can_view_analytics = current_user.role == UserRole.ADMIN
    can_manage_internships = current_user.role in [UserRole.ADMIN, UserRole.COMPANY]
    can_apply_internships = current_user.role in [UserRole.ADMIN, UserRole.STUDENT]
    
    permissions = {
        "view_analytics": can_view_analytics,
        "manage_internships": can_manage_internships,
        "apply_to_internships": can_apply_internships,
        "view_all_users": current_user.role == UserRole.ADMIN,
        "edit_own_profile": True  # Everyone can edit their own profile
    }
    
    return APIResponse(
        success=True,
        message="User permissions calculated",
        data={
            "user": current_user.email,
            "role": current_user.role,
            "permissions": permissions
        }
    )