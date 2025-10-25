"""
Auto-bootstrap system for database initialization and seeding
"""
from sqlalchemy.orm import Session
from core.database import engine, SessionLocal, create_database_if_not_exists, create_all_tables, check_database_connection
from core.config import settings
from models import User, StudentProfile, CompanyProfile
import bcrypt
import logging

# Configure logging
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly - handles 72 byte limit"""
    # Truncate password to 72 bytes to avoid bcrypt ValueError
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes and ensure we don't cut in middle of UTF-8 character
        truncated_bytes = password_bytes[:72]
        # Try to decode, if it fails, keep removing bytes until it works
        while truncated_bytes:
            try:
                password = truncated_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                truncated_bytes = truncated_bytes[:-1]
        else:
            # Fallback if all fails - use first 50 characters
            password = password[:50]
    
    # Use bcrypt directly to avoid passlib initialization issues
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password using bcrypt directly"""
    # Handle the same truncation logic for verification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        truncated_bytes = password_bytes[:72]
        while truncated_bytes:
            try:
                plain_password = truncated_bytes.decode('utf-8')
                break
            except UnicodeDecodeError:
                truncated_bytes = truncated_bytes[:-1]
        else:
            plain_password = plain_password[:50]
    
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def check_admin_exists(db: Session) -> bool:
    """Check if admin user exists"""
    admin_user = db.query(User).filter(User.role == "admin").first()
    return admin_user is not None

def check_test_users_exist(db: Session) -> tuple[bool, bool]:
    """Check if test users (student and company) exist"""
    student_exists = db.query(User).filter(
        User.role == "student", 
        User.email == settings.test_user1_email
    ).first() is not None
    
    company_exists = db.query(User).filter(
        User.role == "company",
        User.email == settings.test_user2_email
    ).first() is not None
    
    return student_exists, company_exists

def create_admin_user(db: Session):
    """Create admin user"""
    try:
        admin_user = User(
            full_name="System Administrator",
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"Created admin user: {admin_user.email}")
        return admin_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise

def create_test_student(db: Session):
    """Create test student user with profile"""
    try:
        # Create user
        student_user = User(
            full_name="Test Student",
            email=settings.test_user1_email,
            password_hash=hash_password(settings.test_user1_password),
            role="student"
        )
        
        db.add(student_user)
        db.flush()  # Get the user ID
        
        # Create student profile
        student_profile = StudentProfile(
            user_id=student_user.id,
            university="Test University",
            major="Computer Science", 
            graduation_year=2025,
            bio="Test student for development purposes"
        )
        
        db.add(student_profile)
        db.commit()
        db.refresh(student_user)
        
        logger.info(f"Created test student: {student_user.email}")
        return student_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test student: {e}")
        raise

def create_test_company(db: Session):
    """Create test company user with profile"""
    try:
        # Create user
        company_user = User(
            full_name="Test Company Rep",
            email=settings.test_user2_email,
            password_hash=hash_password(settings.test_user2_password),
            role="company"
        )
        
        db.add(company_user)
        db.flush()  # Get the user ID
        
        # Create company profile
        company_profile = CompanyProfile(
            user_id=company_user.id,
            company_name="Test Corp Inc",
            website_url="https://testcorp.com",
            description="A test company for development purposes"
        )
        
        db.add(company_profile)
        db.commit()
        db.refresh(company_user)
        
        logger.info(f"Created test company: {company_user.email}")
        return company_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test company: {e}")
        raise

def seed_database():
    """Seed database with initial data"""
    db = SessionLocal()
    
    try:
        # Check and create admin user
        if not check_admin_exists(db):
            create_admin_user(db)
            logger.info("✅ Admin user created")
        else:
            logger.info("ℹ️  Admin user already exists")
        
        # Check and create test users
        student_exists, company_exists = check_test_users_exist(db)
        
        if not student_exists:
            create_test_student(db)
            logger.info("✅ Test student created")
        else:
            logger.info("ℹ️  Test student already exists")
            
        if not company_exists:
            create_test_company(db)
            logger.info("✅ Test company created")
        else:
            logger.info("ℹ️  Test company already exists")
            
        logger.info("🎉 Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during database seeding: {e}")
        raise
    finally:
        db.close()

def bootstrap_database():
    """
    Main bootstrap function - creates database, tables, and seeds data
    """
    try:
        logger.info("🚀 Starting database bootstrap...")
        
        # Step 1: Create database if it doesn't exist
        logger.info("📦 Creating database if needed...")
        create_database_if_not_exists()
        
        # Step 2: Check database connection
        logger.info("🔗 Checking database connection...")
        if not check_database_connection():
            raise Exception("Failed to connect to database")
        
        # Step 3: Create all tables
        logger.info("🏗️  Creating database tables...")
        create_all_tables()
        
        # Step 4: Seed initial data
        logger.info("🌱 Seeding initial data...")
        seed_database()
        
        logger.info("✨ Database bootstrap completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Bootstrap failed: {e}")
        raise

def should_run_bootstrap() -> bool:
    """Check if bootstrap should run based on configuration"""
    return settings.auto_bootstrap

async def async_bootstrap():
    """Async wrapper for bootstrap (for FastAPI startup)"""
    if should_run_bootstrap():
        logger.info("🔄 Auto-bootstrap enabled, starting...")
        bootstrap_database()
    else:
        logger.info("⏭️  Auto-bootstrap disabled, skipping...")