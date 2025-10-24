"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Base from models
from models.base import Base

# Create engine based on database URL
def create_db_engine():
    """Create PostgreSQL database engine with optimized configuration"""
    database_url = settings.database_url
    
    # PostgreSQL optimized configuration
    engine = create_engine(
        database_url,
        pool_pre_ping=True,           # Verify connections before use
        pool_size=10,                 # Connection pool size
        max_overflow=20,              # Additional connections if needed
        pool_recycle=3600,            # Recycle connections after 1 hour
        echo=settings.debug           # SQL logging in debug mode
    )
    
    return engine

# Create engine instance
engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_session():
    """
    Dependency to get database session
    Use this in FastAPI route dependencies
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_if_not_exists():
    """
    Create PostgreSQL database if it doesn't exist
    """
    database_url = settings.database_url
    
    # Extract database name and connection details
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    db_name = parsed.path[1:]  # Remove leading slash
    
    # Connect to default 'postgres' database to create target database
    default_db_url = database_url.replace(f"/{db_name}", "/postgres")
    temp_engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
    
    try:
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"✅ Created PostgreSQL database: {db_name}")
            else:
                logger.info(f"ℹ️  PostgreSQL database already exists: {db_name}")
    
    except Exception as e:
        logger.error(f"❌ Error creating PostgreSQL database: {e}")
        raise
    finally:
        temp_engine.dispose()

def create_all_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def check_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False