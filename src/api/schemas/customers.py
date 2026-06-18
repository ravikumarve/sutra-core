"""
Customer API Schemas
Pydantic models for customer management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CustomerResponse(BaseModel):
    """Customer response"""
    id: str
    tenant_id: str
    phone_number: str
    name: Optional[str] = None
    address: Optional[str] = None
    credit_limit: float
    current_balance: float
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_orders: Optional[int] = None

    class Config:
        from_attributes = True


class CustomerCreateRequest(BaseModel):
    """Create customer request"""
    phone_number: str = Field(..., min_length=10, max_length=20)
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    credit_limit: float = Field(default=0.0, ge=0)


class CustomerUpdateRequest(BaseModel):
    """Update customer request"""
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    current_balance: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CustomerListData(BaseModel):
    """Paginated customer list response"""
    items: List[CustomerResponse]
    total: int
    limit: int
    offset: int
