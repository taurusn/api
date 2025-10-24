"""
FastAPI Application Entry Point - Internship Hub API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.config import settings
from core.bootstrap import async_bootstrap
from routes import auth_router, middleware_demo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - handles startup and shutdown"""
    # Startup
    await async_bootstrap()
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="Internship Hub API",
    description="Backend API for internship management platform connecting students with companies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router)
app.include_router(middleware_demo_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Internship Hub API", 
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )