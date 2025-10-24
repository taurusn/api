"""
Configuration management using Pydantic Settings
Loads environment variables from .env file
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str
    
    # Security
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    
    # Environment
    environment: str
    debug: bool
    
    # Auto Bootstrap
    auto_bootstrap: bool
    
    # API Settings
    api_host: str
    api_port: int
    api_reload: bool
    base_url: Optional[str] = None
    
    def get_computed_base_url(self) -> str:
        """Compute base URL from host and port if not explicitly set"""
        if self.base_url:
            return self.base_url
        
        # Use localhost for 0.0.0.0 since it's not accessible externally
        host = "localhost" if self.api_host == "0.0.0.0" else self.api_host
        return f"http://{host}:{self.api_port}"
    
    # Admin User (for seeding)
    admin_username: str
    admin_email: str
    admin_password: str
    
    # Test Users (for seeding)
    test_user1_username: str
    test_user1_email: str
    test_user1_password: str
    
    test_user2_username: str
    test_user2_email: str
    test_user2_password: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Utility functions
def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"

def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"

def get_database_url() -> str:
    """Get the database URL"""
    return settings.database_url

def get_base_url() -> str:
    """Get the base URL for the API"""
    return settings.get_computed_base_url()