"""
API Schemas
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status types"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Authentication Schemas
# ============================================

class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class RegisterRequest(BaseModel):
    """Registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================
# Agent Schemas
# ============================================

class AgentStatus(str, Enum):
    """Agent status types"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class AgentInfo(BaseModel):
    """Agent information"""
    agent_type: str
    tenant_id: str
    status: AgentStatus
    queue_size: int
    active_tasks: int
    last_heartbeat: Optional[datetime] = None


class AgentMessageRequest(BaseModel):
    """Agent message request"""
    tenant_id: str
    target_agent: str
    message_type: str
    payload: Dict[str, Any]
    priority: Optional[str] = "normal"
    requires_confirmation: Optional[bool] = False


class AgentMessageResponse(BaseModel):
    """Agent message response"""
    message_id: str
    status: str
    response: Optional[Dict[str, Any]] = None


# ============================================
# Tenant Schemas
# ============================================

class TenantCreateRequest(BaseModel):
    """Tenant creation request"""
    name: str = Field(..., min_length=3, max_length=100)
    phone_number_id: str = Field(..., min_length=10)
    gst_state_code: int = Field(..., ge=1, le=37)
    industry: Optional[str] = "general"
    contact_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=15)


class TenantUpdateRequest(BaseModel):
    """Tenant update request"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    phone_number_id: Optional[str] = Field(None, min_length=10)
    gst_state_code: Optional[int] = Field(None, ge=1, le=37)
    industry: Optional[str] = None
    contact_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    is_active: Optional[bool] = None


class TenantInfo(BaseModel):
    """Tenant information"""
    tenant_id: str
    name: str
    phone_number_id: str
    gst_state_code: int
    industry: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TenantStatus(BaseModel):
    """Tenant status"""
    tenant_id: str
    name: str
    industry: str
    created_at: datetime
    agents: Dict[str, Dict[str, Any]]


# ============================================
# Webhook Schemas
# ============================================

class WebhookEvent(BaseModel):
    """Webhook event"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]


class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload"""
    object: str
    entry: List[Dict[str, Any]]


# ============================================
# Health Schemas
# ============================================

class HealthStatus(str, Enum):
    """Health status types"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    """Component health"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    uptime: float


# ============================================
# System Schemas
# ============================================

class SystemStatus(BaseModel):
    """System status"""
    coordinator_running: bool
    total_tenants: int
    tenants: List[TenantStatus]
    redis_connected: bool
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Metrics response"""
    messages_sent: int
    messages_received: int
    messages_processed: int
    messages_failed: int
    avg_processing_time: float
    by_message_type: Dict[str, int]
    by_agent: Dict[str, int]
    timestamp: datetime