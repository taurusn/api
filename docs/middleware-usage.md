# Authentication Middleware Usage Guide

This guide shows how to use the authentication middleware in your API routes.

## 📚 **Available Middleware Functions**

### 1. **Basic Authentication**

```python
from fastapi import APIRouter, Depends
from core.middleware import get_current_user
from schemas.user import UserResponse

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Requires valid JWT token"""
    return {"message": f"Hello {current_user.full_name}", "user_id": current_user.id}
```

### 2. **Role-Based Access Control**

#### Using Pre-configured Role Checkers:
```python
from core.middleware import admin_required, company_required, student_required, get_current_user

# Admin only
@router.get("/admin/users")
async def admin_only(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(admin_required)
):
    return {"message": "Admin dashboard"}

# Company or Admin
@router.post("/internships")
async def create_internship(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(company_required)
):
    return {"message": "Internship created"}

# Student or Admin  
@router.post("/applications")
async def apply_internship(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(student_required)
):
    return {"message": "Application submitted"}
```

#### Using Custom Role Checker:
```python
from core.middleware import RoleChecker
from schemas.auth import UserRole

# Custom role requirements
multi_role_required = RoleChecker([UserRole.COMPANY, UserRole.ADMIN])

@router.get("/statistics")
async def get_statistics(
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(multi_role_required)
):
    return {"stats": "data"}
```

#### Using Role Decorator:
```python
from core.middleware import require_roles, get_current_user

@require_roles([UserRole.ADMIN, UserRole.COMPANY])
@router.delete("/internship/{internship_id}")
async def delete_internship(
    internship_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    return {"message": "Internship deleted"}
```

### 3. **Convenience Functions**

#### Extract User ID Only:
```python
from core.middleware import get_current_user_id

@router.get("/my-profile")
async def get_my_profile(user_id: int = Depends(get_current_user_id)):
    # user_id is just an integer
    return {"profile": f"Profile for user {user_id}"}
```

#### Extract User Role Only:
```python
from core.middleware import get_current_user_role

@router.get("/dashboard")
async def dashboard(user_role: UserRole = Depends(get_current_user_role)):
    if user_role == UserRole.ADMIN:
        return {"dashboard": "admin_features"}
    elif user_role == UserRole.COMPANY:
        return {"dashboard": "company_features"}
    else:
        return {"dashboard": "student_features"}
```

### 4. **Optional Authentication**

```python
from core.middleware import get_optional_user
from typing import Optional

@router.get("/public-content")
async def public_content(current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Works with or without authentication"""
    if current_user:
        return {"message": f"Hello {current_user.full_name}", "premium_content": True}
    else:
        return {"message": "Hello anonymous user", "premium_content": False}
```

### 5. **Specific Role Functions**

```python
from core.middleware import require_admin_user, require_company_user, require_student_user

# Admin required
@router.get("/system-settings")
async def system_settings(admin_user: UserResponse = Depends(require_admin_user)):
    return {"settings": "admin_settings"}

# Company required
@router.get("/company-dashboard")
async def company_dashboard(company_user: UserResponse = Depends(require_company_user)):
    return {"dashboard": "company_data"}

# Student required
@router.get("/student-portal")
async def student_portal(student_user: UserResponse = Depends(require_student_user)):
    return {"portal": "student_data"}
```

## 🏗️ **Complete Route Example**

```python
"""
Example: Internship Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_database_session
from core.middleware import (
    get_current_user, 
    company_required, 
    student_required, 
    get_current_user_id,
    get_optional_user
)
from schemas.user import UserResponse
from models.internship import Internship

router = APIRouter(prefix="/internships", tags=["internships"])

# Public endpoint - anyone can view internships
@router.get("/")
async def list_internships(
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(get_optional_user)
):
    """List all internships - enhanced view for authenticated users"""
    internships = db.query(Internship).all()
    
    if current_user:
        # Authenticated users see more details
        return {"internships": internships, "user_specific_data": True}
    else:
        # Anonymous users see basic info only
        return {"internships": [{"title": i.title, "company": i.company} for i in internships]}

# Company-only endpoint
@router.post("/")
async def create_internship(
    internship_data: dict,  # Replace with proper Pydantic model
    db: Session = Depends(get_database_session),
    current_user: UserResponse = Depends(get_current_user),
    _: None = Depends(company_required)
):
    """Create new internship - companies and admins only"""
    # Create internship logic here
    return {"message": "Internship created", "created_by": current_user.id}

# Student-only endpoint  
@router.post("/{internship_id}/apply")
async def apply_to_internship(
    internship_id: int,
    application_data: dict,  # Replace with proper Pydantic model
    user_id: int = Depends(get_current_user_id),
    _: None = Depends(student_required)
):
    """Apply to internship - students only"""
    # Application logic here
    return {"message": "Application submitted", "applicant_id": user_id}

# User-specific endpoint
@router.get("/my-internships")
async def get_my_internships(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get user's internships - behavior varies by role"""
    if current_user.role == UserRole.COMPANY:
        # Return internships created by this company
        internships = db.query(Internship).filter(Internship.company_id == current_user.id).all()
        return {"company_internships": internships}
    elif current_user.role == UserRole.STUDENT:
        # Return internships applied to by this student
        # applications = get_user_applications(current_user.id)
        return {"applied_internships": []}
    else:
        # Admin sees all
        internships = db.query(Internship).all()
        return {"all_internships": internships}
```

## ⚡ **Quick Reference**

| Function | Purpose | Usage |
|----------|---------|--------|
| `get_current_user` | Basic authentication | `Depends(get_current_user)` |
| `get_optional_user` | Optional auth | `Depends(get_optional_user)` |
| `admin_required` | Admin only | `Depends(admin_required)` |
| `company_required` | Company/Admin | `Depends(company_required)` |
| `student_required` | Student/Admin | `Depends(student_required)` |
| `get_current_user_id` | Get user ID only | `Depends(get_current_user_id)` |
| `get_current_user_role` | Get user role only | `Depends(get_current_user_role)` |

## 🚀 **Best Practices**

1. **Always use the most specific middleware** for your needs
2. **Combine multiple dependencies** when needed
3. **Use optional auth** for public endpoints with user-specific features  
4. **Extract only what you need** (use `get_current_user_id` if you only need the ID)
5. **Handle role-based logic** in your business logic, not middleware when complex

## 🔒 **Security Notes**

- All middleware functions automatically validate JWT tokens
- Invalid tokens return 401 Unauthorized
- Insufficient permissions return 403 Forbidden  
- Token expiration is handled automatically
- Use HTTPS in production for token security