"""
Authentication and Authorization Middleware
Provides reusable middleware functions for protecting API endpoints
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import functools

from core.database import get_database_session
from logic.auth.auth_service import AuthService
from schemas.user import UserResponse
from schemas.auth import UserRole


# Security scheme for Bearer token
security = HTTPBearer()

# Global auth service instance
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token
    
    Usage in route:
        @app.get("/protected-endpoint")
        async def protected_route(current_user: UserResponse = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to get current authenticated and active user
    
    Usage in route:
        @app.get("/protected-endpoint") 
        async def protected_route(current_user: UserResponse = Depends(get_current_active_user)):
            return {"user": current_user.email}
    """
    # Since we removed is_active from User model, all users are considered active
    # This function exists for future extensibility when user activation is implemented
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """
    Decorator factory to create role-based access control
    
    Usage:
        @require_roles([UserRole.ADMIN, UserRole.COMPANY])
        @app.get("/admin-endpoint")
        async def admin_only_route(current_user: UserResponse = Depends(get_current_user)):
            return {"message": "Admin access granted"}
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (injected by FastAPI dependency)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user has required role
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RoleChecker:
    """
    Dependency class for role-based access control
    
    Usage:
        admin_required = RoleChecker([UserRole.ADMIN])
        
        @app.get("/admin-endpoint")
        async def admin_route(
            current_user: UserResponse = Depends(get_current_user),
            _: None = Depends(admin_required)
        ):
            return {"message": "Admin access granted"}
    """
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in self.allowed_roles]}"
            )
        return True


# Pre-configured role checkers for common use cases
admin_required = RoleChecker([UserRole.ADMIN])
company_required = RoleChecker([UserRole.COMPANY, UserRole.ADMIN])
student_required = RoleChecker([UserRole.STUDENT, UserRole.ADMIN])
authenticated_required = RoleChecker([UserRole.STUDENT, UserRole.COMPANY, UserRole.ADMIN])


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_database_session)
) -> Optional[UserResponse]:
    """
    Dependency to optionally get current user (doesn't raise error if no token)
    Useful for endpoints that work both with and without authentication
    
    Usage:
        @app.get("/public-or-private-endpoint")
        async def flexible_route(current_user: Optional[UserResponse] = Depends(get_optional_user)):
            if current_user:
                return {"message": f"Hello {current_user.full_name}"}
            else:
                return {"message": "Hello anonymous user"}
    """
    if not credentials:
        return None
    
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user
    except Exception:
        return None


# Middleware functions for different authentication patterns
async def require_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_company_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require company or admin role"""
    if current_user.role not in [UserRole.COMPANY, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access required"
        )
    return current_user


async def require_student_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require student or admin role"""
    if current_user.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user


def get_current_user_id(current_user: UserResponse = Depends(get_current_user)) -> int:
    """
    Convenience function to extract just the user ID
    
    Usage:
        @app.get("/my-profile")
        async def get_profile(user_id: int = Depends(get_current_user_id)):
            # Use user_id directly
            return {"user_id": user_id}
    """
    return current_user.id


def get_current_user_role(current_user: UserResponse = Depends(get_current_user)) -> UserRole:
    """
    Convenience function to extract just the user role
    
    Usage:
        @app.get("/dashboard")
        async def dashboard(user_role: UserRole = Depends(get_current_user_role)):
            if user_role == UserRole.ADMIN:
                return {"dashboard": "admin_dashboard"}
            # etc.
    """
    return current_user.role