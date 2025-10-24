"""
API Routes Package
Central location for all API route definitions
"""
from .auth import auth_router

__all__ = ['auth_router']