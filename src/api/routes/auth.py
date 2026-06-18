"""
Authentication Endpoints
JWT-based authentication with token management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.db.connection import get_db_session
from src.db.models import User, Tenant
from src.db.queries import QueryOptimizer, execute_optimized_query
from src.security.auth import auth_manager, input_validator
from src.security.rbac import tenant_context, Role
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
security = HTTPBearer()


# Pydantic models for request/response
class UserRegistration(BaseModel):
    """User registration request"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: Optional[str] = None  # Optional for new tenant registration
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if not input_validator.validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # Add password strength validation
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserLogin(BaseModel):
    """User login request"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1, max_length=128)
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if not input_validator.validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., min_length=1)


class PasswordReset(BaseModel):
    """Password reset request"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    new_password: str = Field(..., min_length=8, max_length=128)
    reset_token: str = Field(..., min_length=1)
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if not input_validator.validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """User response"""
    id: str
    phone_number: str
    name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime


async def _check_existing_user(phone_number: str, db: AsyncSession) -> None:
    """
    Check if user already exists with given phone number
    
    Args:
        phone_number: User's phone number
        db: Database session
        
    Raises:
        HTTPException: If user already exists
    """
    # Use optimized query with proper indexing
    query = select(User).where(User.phone_number == phone_number)
    existing_user = await execute_optimized_query(db, query)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )


async def _validate_or_create_tenant(
    tenant_id: Optional[str],
    user_name: str,
    db: AsyncSession
) -> str:
    """
    Validate existing tenant or create default tenant
    
    Args:
        tenant_id: Optional tenant ID
        user_name: User's name for default tenant creation
        db: Database session
        
    Returns:
        Valid tenant ID
        
    Raises:
        HTTPException: If tenant ID is invalid
    """
    if tenant_id:
        # Use optimized query with proper indexing
        query = QueryOptimizer.optimize_tenant_query(tenant_id)
        tenant = await execute_optimized_query(db, query)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant ID"
            )
        return tenant_id
    else:
        # For demo purposes, create a default tenant
        # In production, this would require proper tenant provisioning
        tenant = Tenant(
            name=f"{user_name}'s Business",
            phone_number_id="default_phone_id",
            gst_state_code=settings.default_gst_state_code,
            industry="retail"
        )
        db.add(tenant)
        await db.flush()
        return str(tenant.id)


async def _create_user(
    tenant_id: str,
    user_data: UserRegistration,
    password_hash: str,
    db: AsyncSession
) -> User:
    """
    Create new user in database
    
    Args:
        tenant_id: Valid tenant ID
        user_data: User registration data
        password_hash: Hashed password
        db: Database session
        
    Returns:
        Created user object
    """
    user = User(
        tenant_id=tenant_id,
        phone_number=user_data.phone_number,
        name=user_data.name,
        password_hash=password_hash,
        role="shop_owner",  # Default role for new users
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _generate_tokens(user: User, tenant_id: str) -> tuple[str, str]:
    """
    Generate access and refresh tokens for user
    
    Args:
        user: User object
        tenant_id: Tenant ID
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    token_data = {
        "user_id": str(user.id),
        "tenant_id": tenant_id,
        "phone_number": user.phone_number,
        "role": user.role
    }
    
    access_token = auth_manager.create_access_token(token_data)
    refresh_token = auth_manager.create_refresh_token(token_data)
    
    return access_token, refresh_token


def _build_token_response(
    user: User,
    tenant_id: str,
    access_token: str,
    refresh_token: str
) -> TokenResponse:
    """
    Build token response with user information
    
    Args:
        user: User object
        tenant_id: Tenant ID
        access_token: Access token
        refresh_token: Refresh token
        
    Returns:
        Token response object
    """
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user={
            "id": str(user.id),
            "phone_number": user.phone_number,
            "name": user.name,
            "role": user.role,
            "tenant_id": tenant_id,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Register a new user
    
    - **phone_number**: User's phone number (WhatsApp number)
    - **name**: User's full name
    - **password**: User's password (min 8 characters)
    - **tenant_id**: Optional tenant ID (for existing tenants)
    """
    try:
        # Check if user already exists
        await _check_existing_user(user_data.phone_number, db)
        
        # Validate tenant or create default
        tenant_id = await _validate_or_create_tenant(
            user_data.tenant_id,
            user_data.name,
            db
        )
        
        # Hash password
        password_hash = auth_manager.hash_password(user_data.password)
        
        # Create user
        user = await _create_user(tenant_id, user_data, password_hash, db)
        
        # Generate tokens
        access_token, refresh_token = _generate_tokens(user, tenant_id)
        
        logger.info(f"User registered: {user.phone_number}")
        
        # Build and return response
        return _build_token_response(user, tenant_id, access_token, refresh_token)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Login user with phone number and password
    
    - **phone_number**: User's phone number
    - **password**: User's password
    """
    try:
        # Find user by phone number using optimized query
        query = select(User).where(User.phone_number == login_data.phone_number)
        user = await execute_optimized_query(db, query)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password"
            )
        
        # Verify password
        if not auth_manager.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        # Generate tokens
        token_data = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "phone_number": user.phone_number,
            "role": user.role
        }
        
        access_token = auth_manager.create_access_token(token_data)
        refresh_token = auth_manager.create_refresh_token(token_data)
        
        logger.info(f"User logged in: {user.phone_number}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user={
                "id": str(user.id),
                "phone_number": user.phone_number,
                "name": user.name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    try:
        # Decode refresh token
        payload = auth_manager.decode_token(refresh_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Find user using optimized query
        query = select(User).where(User.id == user_id)
        user = await execute_optimized_query(db, query)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        token_data = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "phone_number": user.phone_number,
            "role": user.role
        }
        
        access_token = auth_manager.create_access_token(token_data)
        new_refresh_token = auth_manager.create_refresh_token(token_data)
        
        logger.info(f"Token refreshed for user: {user.phone_number}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user={
                "id": str(user.id),
                "phone_number": user.phone_number,
                "name": user.name,
                "role": user.role,
                "tenant_id": str(user.tenant_id),
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user (client-side token invalidation)
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. For server-side logout, implement a token blacklist.
    """
    try:
        # Decode token to log the logout
        token = credentials.credentials
        payload = auth_manager.decode_token(token)
        
        user_id = payload.get("user_id")
        phone_number = payload.get("phone_number")
        
        logger.info(f"User logged out: {phone_number} (user_id: {user_id})")
        
        return {
            "message": "Successfully logged out",
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Logout failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get current user information
    
    Requires valid JWT token
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = auth_manager.decode_token(token)
        
        # Get user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Find user using optimized query
        query = select(User).where(User.id == user_id)
        user = await execute_optimized_query(db, query)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            role=user.role,
            tenant_id=str(user.tenant_id),
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/verify-token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify if token is valid
    
    Returns token information if valid
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = auth_manager.decode_token(token)
        
        return {
            "valid": True,
            "token_type": payload.get("type"),
            "user_id": payload.get("user_id"),
            "tenant_id": payload.get("tenant_id"),
            "phone_number": payload.get("phone_number"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        return {
            "valid": False,
            "error": str(e)
        }