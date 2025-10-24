"""
API Routes Package
Central location for all API route definitions
"""
from .auth import auth_router
from .examples import middleware_demo_router

__all__ = ['auth_router', 'middleware_demo_router']