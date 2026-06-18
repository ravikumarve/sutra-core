"""
Inventory API Schemas
Pydantic models for inventory CRUD operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InventoryItemResponse(BaseModel):
    """Inventory item response"""
    id: str
    tenant_id: str
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None
    unit: str
    purchase_price: float
    selling_price: float
    gst_rate: float
    quantity: int
    min_stock_level: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InventoryCreateRequest(BaseModel):
    """Create inventory item request"""
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    hsn_code: Optional[str] = Field(None, max_length=8)
    unit: str = Field(..., max_length=50)
    purchase_price: float = Field(..., ge=0)
    selling_price: float = Field(..., ge=0)
    gst_rate: float = Field(default=0.0, ge=0, le=100)
    quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=10, ge=0)


class InventoryUpdateRequest(BaseModel):
    """Update inventory item request"""
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    hsn_code: Optional[str] = Field(None, max_length=8)
    unit: Optional[str] = Field(None, max_length=50)
    purchase_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    gst_rate: Optional[float] = Field(None, ge=0, le=100)
    quantity: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class StockAdjustRequest(BaseModel):
    """Adjust stock level request"""
    quantity_change: int = Field(..., description="Positive to add stock, negative to remove")
    reason: Optional[str] = Field(None, max_length=500)


class InventoryListResponse(BaseModel):
    """Paginated inventory list response"""
    items: List[InventoryItemResponse]
    total: int
    limit: int
    offset: int
