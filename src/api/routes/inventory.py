"""
Inventory API Routes
CRUD endpoints for inventory management
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.common import BaseResponse
from src.api.schemas.inventory import (
    InventoryItemResponse,
    InventoryCreateRequest,
    InventoryUpdateRequest,
    StockAdjustRequest,
    InventoryListResponse,
)
from src.db.connection import get_db_session
from src.db.models import Inventory
from src.security.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def _get_tenant_id(credentials: HTTPAuthorizationCredentials) -> str:
    """Verify token and return tenant_id (sync — verify_token is sync)"""
    user = verify_token(credentials.credentials)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: no tenant_id")
    return tenant_id


async def _get_inventory_item(
    item_id: str, tenant_id: str, db: AsyncSession
) -> Inventory:
    """Get inventory item by ID with tenant isolation"""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")

    result = await db.execute(
        select(Inventory).where(
            and_(
                Inventory.id == item_uuid,
                Inventory.tenant_id == uuid.UUID(tenant_id),
            )
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


def _item_to_response(item: Inventory) -> InventoryItemResponse:
    """Convert ORM model to response schema"""
    return InventoryItemResponse(
        id=str(item.id),
        tenant_id=str(item.tenant_id),
        sku=item.sku,
        name=item.name,
        description=item.description,
        category=item.category,
        hsn_code=item.hsn_code,
        unit=item.unit,
        purchase_price=float(item.purchase_price),
        selling_price=float(item.selling_price),
        gst_rate=float(item.gst_rate),
        quantity=item.quantity,
        min_stock_level=item.min_stock_level,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/", response_model=BaseResponse)
async def list_inventory(
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock_only: bool = Query(False, description="Show only low-stock items"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List inventory items with pagination and filtering.
    Supports category filter, low-stock filter, and text search.
    """
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        # Build filters
        filters = [Inventory.tenant_id == tenant_uuid]

        if is_active is not None:
            filters.append(Inventory.is_active == is_active)

        if category:
            filters.append(Inventory.category == category)

        if low_stock_only:
            filters.append(Inventory.quantity < Inventory.min_stock_level)

        if search:
            search_term = f"%{search}%"
            filters.append(
                Inventory.name.ilike(search_term) | Inventory.sku.ilike(search_term)
            )

        # Get total count
        count_result = await db.execute(
            select(func.count(Inventory.id)).where(and_(*filters))
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            select(Inventory)
            .where(and_(*filters))
            .order_by(Inventory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = result.scalars().all()

        return BaseResponse(
            success=True,
            data={
                "items": [_item_to_response(item) for item in items],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing inventory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list inventory: {str(e)}")


@router.get("/categories", response_model=BaseResponse)
async def list_categories(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Get distinct inventory categories for this tenant"""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        result = await db.execute(
            select(Inventory.category)
            .where(
                and_(
                    Inventory.tenant_id == tenant_uuid,
                    Inventory.is_active == True,
                    Inventory.category.isnot(None),
                )
            )
            .distinct()
            .order_by(Inventory.category)
        )
        categories = [row[0] for row in result if row[0]]

        return BaseResponse(success=True, data={"categories": categories})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list categories")


@router.get("/{item_id}", response_model=BaseResponse)
async def get_inventory_item(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single inventory item by ID"""
    try:
        tenant_id = _get_tenant_id(credentials)
        item = await _get_inventory_item(item_id, tenant_id, db)

        return BaseResponse(success=True, data={"item": _item_to_response(item)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get inventory item")


@router.post("/", response_model=BaseResponse, status_code=201)
async def create_inventory_item(
    request: InventoryCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new inventory item"""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        # Check for duplicate SKU within tenant
        result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.tenant_id == tenant_uuid,
                    Inventory.sku == request.sku,
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Item with SKU '{request.sku}' already exists for this tenant",
            )

        item = Inventory(
            tenant_id=tenant_uuid,
            sku=request.sku,
            name=request.name,
            description=request.description,
            category=request.category,
            hsn_code=request.hsn_code,
            unit=request.unit,
            purchase_price=request.purchase_price,
            selling_price=request.selling_price,
            gst_rate=request.gst_rate,
            quantity=request.quantity,
            min_stock_level=request.min_stock_level,
            is_active=True,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)

        logger.info(f"Created inventory item: {item.sku} for tenant {tenant_id}")

        return BaseResponse(
            success=True,
            message="Inventory item created",
            data={"item": _item_to_response(item)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating inventory item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create item: {str(e)}")


@router.put("/{item_id}", response_model=BaseResponse)
async def update_inventory_item(
    item_id: str,
    request: InventoryUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an inventory item"""
    try:
        tenant_id = _get_tenant_id(credentials)
        item = await _get_inventory_item(item_id, tenant_id, db)

        # If SKU is changing, check for duplicates
        if request.sku is not None and request.sku != item.sku:
            result = await db.execute(
                select(Inventory).where(
                    and_(
                        Inventory.tenant_id == uuid.UUID(tenant_id),
                        Inventory.sku == request.sku,
                        Inventory.id != item.id,
                    )
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail=f"Another item with SKU '{request.sku}' already exists",
                )

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        await db.commit()
        await db.refresh(item)

        logger.info(f"Updated inventory item: {item.sku}")

        return BaseResponse(
            success=True,
            message="Inventory item updated",
            data={"item": _item_to_response(item)},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating inventory item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@router.delete("/{item_id}", response_model=BaseResponse)
async def delete_inventory_item(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Soft-delete (deactivate) an inventory item"""
    try:
        tenant_id = _get_tenant_id(credentials)
        item = await _get_inventory_item(item_id, tenant_id, db)

        # Soft delete - set inactive
        item.is_active = False
        await db.commit()

        logger.info(f"Deactivated inventory item: {item.sku}")

        return BaseResponse(
            success=True,
            message="Inventory item deactivated",
            data={"item_id": item_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting inventory item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")


@router.patch("/{item_id}/stock", response_model=BaseResponse)
async def adjust_stock(
    item_id: str,
    request: StockAdjustRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Adjust stock level (positive to add, negative to remove)"""
    try:
        tenant_id = _get_tenant_id(credentials)
        item = await _get_inventory_item(item_id, tenant_id, db)

        new_quantity = item.quantity + request.quantity_change
        if new_quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Current: {item.quantity}, requested change: {request.quantity_change}",
            )

        item.quantity = new_quantity
        await db.commit()
        await db.refresh(item)

        logger.info(
            f"Adjusted stock for {item.sku}: {request.quantity_change:+d} → {item.quantity} "
            f"({request.reason or 'no reason given'})"
        )

        return BaseResponse(
            success=True,
            message="Stock adjusted",
            data={
                "item": _item_to_response(item),
                "previous_quantity": new_quantity - request.quantity_change,
                "quantity_change": request.quantity_change,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adjusting stock for {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to adjust stock: {str(e)}")
