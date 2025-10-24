"""
User and authentication models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel


class User(BaseModel):
    """
    Users table - Base user model for students, companies, and admin
    """
    __tablename__ = "users"
    
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default='student')  # student, company, admin
    
    # Relationships
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class UserToken(BaseModel):
    """
    JWT token management table
    """
    __tablename__ = "user_tokens"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_tokens_user_id', 'user_id'),
        Index('idx_user_tokens_expires_at', 'expires_at'),
    )


class StudentProfile(BaseModel):
    """
    Student profile information
    """
    __tablename__ = "student_profiles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    university = Column(String(120))
    major = Column(String(120))
    graduation_year = Column(Integer)
    resume_url = Column(Text)
    bio = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")


class CompanyProfile(BaseModel):
    """
    Company profile information
    """
    __tablename__ = "company_profiles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(120), nullable=False)
    website_url = Column(Text)
    description = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="company_profile")
    internships = relationship("Internship", back_populates="company", cascade="all, delete-orphan")


class Internship(BaseModel):
    """
    Internship posts by companies
    """
    __tablename__ = "internships"
    
    company_id = Column(Integer, ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    location = Column(String(120))
    category = Column(String(80))
    type = Column(String(40), default='onsite', nullable=False)  # remote, onsite, hybrid
    duration_weeks = Column(Integer)
    posted_at = Column(DateTime(timezone=True), server_default=BaseModel.created_at.default)
    
    # Relationships
    company = relationship("CompanyProfile", back_populates="internships")
    applications = relationship("Application", back_populates="internship", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_internships_company_id', 'company_id'),
    )


class Application(BaseModel):
    """
    Student applications to internships
    """
    __tablename__ = "applications"
    
    internship_id = Column(Integer, ForeignKey("internships.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    cover_letter = Column(Text)
    status = Column(String(30), default='pending', nullable=False)  # pending, reviewed, accepted, rejected
    applied_at = Column(DateTime(timezone=True), server_default=BaseModel.created_at.default)
    
    # Relationships
    internship = relationship("Internship", back_populates="applications")
    student = relationship("StudentProfile", back_populates="applications")
    
    # Constraints and Indexes
    __table_args__ = (
        Index('idx_applications_student_id', 'student_id'),
        Index('idx_applications_status', 'status'),
        # Unique constraint handled at database level
    )


class ActivityLog(BaseModel):
    """
    Activity logging for audit trail
    """
    __tablename__ = "activity_log"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100))
    entity = Column(String(100))
    entity_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=BaseModel.created_at.default)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_log_user_id', 'user_id'),
    )