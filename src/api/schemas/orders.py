"""
Order API Schemas
Pydantic models for order management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OrderItemResponse(BaseModel):
    """Order line item response"""
    id: str
    inventory_id: str
    sku: Optional[str] = None
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    gst_rate: float
    gst_amount: float
    total_amount: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response"""
    id: str
    tenant_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_number: str
    order_date: Optional[datetime] = None
    total_amount: float
    total_gst: float
    discount_amount: float
    payment_method: str
    payment_status: str
    is_credit: bool
    credit_amount: float
    status: str
    notes: Optional[str] = None
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: Optional[List[OrderItemResponse]] = None

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    """Order item creation"""
    inventory_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Optional[float] = None  # If not provided, use current selling price
    gst_rate: Optional[float] = None   # If not provided, use inventory gst_rate


class OrderCreateRequest(BaseModel):
    """Create order request"""
    customer_id: Optional[str] = None
    payment_method: str = Field(default="cash", max_length=50)
    payment_status: str = Field(default="pending", max_length=50)
    is_credit: bool = False
    discount_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None
    source: str = Field(default="manual", max_length=50)
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdateRequest(BaseModel):
    """Update order (status/payment)"""
    status: Optional[str] = Field(None, max_length=50)
    payment_status: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    discount_amount: Optional[float] = Field(None, ge=0)


class OrderListData(BaseModel):
    """Paginated order list response"""
    items: List[OrderResponse]
    total: int
    limit: int
    offset: int
