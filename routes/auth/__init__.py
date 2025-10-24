"""
Authentication routes package
Exports authentication router
"""
from .auth import router as auth_router

__all__ = ['auth_router']