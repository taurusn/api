"""
Authentication Service
Business logic for user authentication, registration, and token management
"""
import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.config import settings
from models.user import User, UserToken
from schemas.auth import UserRegister, Token
from schemas.user import UserResponse


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt directly"""
        try:
            # Convert strings to bytes for bcrypt
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
            
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            # Fallback verification for non-bcrypt hashes
            if not hashed_password.startswith('$2b$') and not hashed_password.startswith('$2a$'):
                # Try legacy PBKDF2 hash comparison
                import hashlib
                salt = "internship_hub_salt"
                expected_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000).hex()
                return expected_hash == hashed_password
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash using bcrypt directly"""
        try:
            # Convert password to bytes and generate salt
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string
            return hashed.decode('utf-8')
        except Exception:
            # Fallback: use PBKDF2 if bcrypt fails
            import hashlib
            salt = "internship_hub_salt"  # In production, use random salt
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self) -> str:
        """Create secure refresh token"""
        return secrets.token_urlsafe(32)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()
    
    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    async def register_user(self, db: Session, user_data: UserRegister) -> UserResponse:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Validate password strength
        if len(user_data.password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Create new user
        try:
            hashed_password = self.get_password_hash(user_data.password)
        except Exception as e:
            raise ValueError(f"Password hashing failed: {str(e)}")
            
        db_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            full_name=db_user.full_name,
            email=db_user.email,
            role=db_user.role,
            created_at=db_user.created_at
        )
    
    async def authenticate_user(self, db: Session, email: str, password: str) -> Token:
        """Authenticate user and return tokens"""
        # Get user by email
        user = await self.get_user_by_email(db, email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Create tokens
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token()
        
        # Store refresh token in database
        refresh_token_expires = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Remove existing refresh tokens for this user
        db.query(UserToken).filter(UserToken.user_id == user.id).delete()
        
        # Create new refresh token record
        db_token = UserToken(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=refresh_token_expires,
            issued_at=datetime.utcnow()
        )
        
        db.add(db_token)
        db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    async def refresh_access_token(self, db: Session, refresh_token: str) -> Token:
        """Create new access token using refresh token"""
        # Find refresh token in database
        db_token = db.query(UserToken).filter(
            and_(
                UserToken.refresh_token == refresh_token,
                UserToken.expires_at > datetime.utcnow(),
                UserToken.is_revoked == False
            )
        ).first()
        
        if not db_token:
            raise ValueError("Invalid or expired refresh token")
        
        # Get user
        user = await self.get_user_by_id(db, db_token.user_id)
        if not user:
            raise ValueError("User not found")
        
        # Create new access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = self.create_refresh_token()
        
        # Update refresh token in database
        db_token.token = new_refresh_token
        db_token.expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    async def get_current_user(self, db: Session, token: str) -> UserResponse:
        """Get current user from access token (optimized - uses JWT payload directly)"""
        payload = self.verify_token(token)
        if not payload:
            raise ValueError("Invalid or expired token")
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if not user_id or not email or not role:
            raise ValueError("Invalid token payload - missing required fields")
        
        # Optional: Verify user still exists (can be disabled for performance)
        if settings.verify_user_exists_on_auth:
            user = await self.get_user_by_id(db, int(user_id))
            if not user:
                raise ValueError("User not found")
            
            # Use JWT data for response (faster) but verify against database
            return UserResponse(
                id=int(user_id),
                full_name=user.full_name,  # From database for latest data
                email=email,              # From JWT (should match)
                role=role,               # From JWT (trusted source)
                created_at=user.created_at
            )
        else:
            # Fast path: Use only JWT data (recommended for production)
            # For now, we'll fetch user data to get full_name (can be optimized later by storing in JWT)
            user = await self.get_user_by_id(db, int(user_id))
            if not user:
                raise ValueError("User not found")
            
            return UserResponse(
                id=int(user_id),
                full_name=user.full_name,  # From database
                email=email,               # From JWT
                role=role,                # From JWT (trusted)
                created_at=user.created_at
            )
    
    async def logout_user(self, db: Session, access_token: str):
        """Logout user by revoking refresh token"""
        payload = self.verify_token(access_token)
        if not payload:
            raise ValueError("Invalid or expired token")
        
        user_id: str = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Remove all refresh tokens for this user
        db.query(UserToken).filter(UserToken.user_id == int(user_id)).delete()
        db.commit()
    
    async def request_password_reset(self, db: Session, email: str):
        """Request password reset token"""
        user = await self.get_user_by_email(db, email)
        if not user:
            # Don't reveal if email exists
            return
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        # TODO: Implement proper password reset token storage
        # For now, we'll just generate the token and log it
        # In production, this would be sent via email and stored in a dedicated table
        print(f"Password reset token for {email}: {reset_token}")
        print(f"Reset token expires at: {reset_token_expires}")
        
        # Return success - don't store in UserToken table as it's only for refresh tokens
    
    async def reset_password(self, db: Session, reset_token: str, new_password: str):
        """Reset password using reset token"""
        # TODO: Implement proper password reset token validation
        # For now, this is a placeholder that requires proper token storage system
        raise ValueError("Password reset functionality requires proper token storage - not yet implemented")
        
        db.commit()
    
    async def change_password(self, db: Session, user_id: int, current_password: str, new_password: str):
        """Change user's password"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")
        
        # Update password
        user.password_hash = self.get_password_hash(new_password)
        
        # Remove all refresh tokens (force re-login on all devices)
        db.query(UserToken).filter(UserToken.user_id == user.id).delete()
        
        db.commit()