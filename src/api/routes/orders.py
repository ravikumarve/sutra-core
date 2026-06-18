"""
Order API Routes
CRUD endpoints for order management with inventory integration
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas.common import BaseResponse
from src.api.schemas.orders import (
    OrderResponse,
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderItemResponse,
    OrderListData,
)
from src.db.connection import get_db_session
from src.db.models import Order, OrderItem, Inventory, Customer
from src.security.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def _get_tenant_id(credentials: HTTPAuthorizationCredentials) -> str:
    """Verify token and return tenant_id"""
    user = verify_token(credentials.credentials)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: no tenant_id")
    return tenant_id


async def _get_order(order_id: str, tenant_id: str, db: AsyncSession) -> Order:
    """Get order by ID with tenant isolation, eagerly load items"""
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.inventory),
            selectinload(Order.customer),
        )
        .where(
            and_(
                Order.id == order_uuid,
                Order.tenant_id == uuid.UUID(tenant_id),
            )
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _order_to_list_response(order: Order) -> OrderResponse:
    """Convert ORM order to response for list views (no items — avoids lazy-load)"""
    return OrderResponse(
        id=str(order.id),
        tenant_id=str(order.tenant_id),
        customer_id=str(order.customer_id) if order.customer_id else None,
        customer_name=order.customer.name if order.customer else None,
        customer_phone=order.customer.phone_number if order.customer else None,
        order_number=order.order_number,
        order_date=order.order_date,
        total_amount=float(order.total_amount),
        total_gst=float(order.total_gst),
        discount_amount=float(order.discount_amount),
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        is_credit=order.is_credit,
        credit_amount=float(order.credit_amount),
        status=order.status,
        notes=order.notes,
        source=order.source,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=None,
    )


def _order_to_response(order: Order) -> OrderResponse:
    """Convert ORM order to response WITH items (caller must eager-load)"""
    resp = _order_to_list_response(order)
    if order.items:
        resp.items = [
            OrderItemResponse(
                id=str(item.id),
                inventory_id=str(item.inventory_id),
                sku=item.inventory.sku if item.inventory else None,
                product_name=item.inventory.name if item.inventory else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                gst_rate=float(item.gst_rate),
                gst_amount=float(item.gst_amount),
                total_amount=float(item.total_amount),
            )
            for item in order.items
        ]
    return resp


async def _generate_order_number(tenant_id: str, db: AsyncSession) -> str:
    """Generate a human-readable order number"""
    tenant_uuid = uuid.UUID(tenant_id)
    # Count existing orders for this tenant
    result = await db.execute(
        select(func.count(Order.id)).where(Order.tenant_id == tenant_uuid)
    )
    count = (result.scalar() or 0) + 1
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"ORD-{today}-{count:04d}"


@router.get("/", response_model=BaseResponse)
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    search: Optional[str] = Query(None, description="Search by order number"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """List orders with pagination and filtering"""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        filters = [Order.tenant_id == tenant_uuid]

        if status:
            filters.append(Order.status == status)
        if payment_status:
            filters.append(Order.payment_status == payment_status)
        if customer_id:
            try:
                filters.append(Order.customer_id == uuid.UUID(customer_id))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid customer_id format")
        if search:
            filters.append(Order.order_number.ilike(f"%{search}%"))
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from)
                filters.append(Order.order_date >= dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                filters.append(Order.order_date <= dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")

        # Count
        count_result = await db.execute(
            select(func.count(Order.id)).where(and_(*filters))
        )
        total = count_result.scalar() or 0

        # Fetch orders with customer relationship
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.customer))
            .where(and_(*filters))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orders = result.scalars().all()

        return BaseResponse(
            success=True,
            data={
                "items": [_order_to_list_response(o) for o in orders],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list orders: {str(e)}")


@router.get("/{order_id}", response_model=BaseResponse)
async def get_order(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single order with items"""
    try:
        tenant_id = _get_tenant_id(credentials)
        order = await _get_order(order_id, tenant_id, db)

        return BaseResponse(
            success=True,
            data={"order": _order_to_response(order)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get order")


@router.post("/", response_model=BaseResponse, status_code=201)
async def create_order(
    request: OrderCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new order with items. Deducts inventory."""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        # Verify customer if provided
        customer = None
        if request.customer_id:
            try:
                cust_uuid = uuid.UUID(request.customer_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid customer_id")
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.id == cust_uuid,
                        Customer.tenant_id == tenant_uuid,
                        Customer.is_active == True,
                    )
                )
            )
            customer = result.scalar_one_or_none()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

        # Validate and fetch inventory items
        order_items_data = []
        total_amount = 0.0
        total_gst = 0.0

        for i, item_data in enumerate(request.items):
            result = await db.execute(
                select(Inventory).where(
                    and_(
                        Inventory.id == uuid.UUID(item_data.inventory_id),
                        Inventory.tenant_id == tenant_uuid,
                        Inventory.is_active == True,
                    )
                )
            )
            inv = result.scalar_one_or_none()
            if not inv:
                raise HTTPException(
                    status_code=404,
                    detail=f"Inventory item {item_data.inventory_id} not found",
                )

            # Check stock
            if inv.quantity < item_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {inv.name} ({inv.sku}): "
                    f"requested {item_data.quantity}, available {inv.quantity}",
                )

            unit_price = item_data.unit_price or inv.selling_price
            gst_rate = item_data.gst_rate or inv.gst_rate
            line_total = unit_price * item_data.quantity
            gst_amount = line_total * (gst_rate / 100)

            order_items_data.append({
                "inventory": inv,
                "quantity": item_data.quantity,
                "unit_price": unit_price,
                "gst_rate": gst_rate,
                "gst_amount": gst_amount,
                "total_amount": line_total + gst_amount,
            })

            total_amount += line_total
            total_gst += gst_amount

        # Generate order number
        order_number = await _generate_order_number(tenant_id, db)

        # Create order
        order = Order(
            tenant_id=tenant_uuid,
            customer_id=uuid.UUID(request.customer_id) if request.customer_id else None,
            order_number=order_number,
            total_amount=total_amount - request.discount_amount + total_gst,
            total_gst=total_gst,
            discount_amount=request.discount_amount,
            payment_method=request.payment_method,
            payment_status=request.payment_status,
            is_credit=request.is_credit,
            credit_amount=total_amount if request.is_credit else 0.0,
            status="pending",
            notes=request.notes,
            source=request.source,
        )
        db.add(order)
        await db.flush()

        # Create order items and deduct inventory
        for item_data in order_items_data:
            inv = item_data["inventory"]
            order_item = OrderItem(
                order_id=order.id,
                inventory_id=inv.id,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                gst_rate=item_data["gst_rate"],
                gst_amount=item_data["gst_amount"],
                total_amount=item_data["total_amount"],
            )
            db.add(order_item)

            # Deduct inventory
            inv.quantity -= item_data["quantity"]

        # If credit order, update customer balance
        if request.is_credit and customer:
            customer.current_balance += total_amount

        await db.commit()

        # Reload with relationships
        order = await _get_order(str(order.id), tenant_id, db)

        logger.info(
            f"Created order {order_number}: ₹{order.total_amount:.2f} "
            f"({len(request.items)} items)"
        )

        return BaseResponse(
            success=True,
            message="Order created",
            data={"order": _order_to_response(order)},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.put("/{order_id}", response_model=BaseResponse)
async def update_order(
    order_id: str,
    request: OrderUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Update order status, payment, or notes"""
    try:
        tenant_id = _get_tenant_id(credentials)
        order = await _get_order(order_id, tenant_id, db)

        # Snapshot ALL response fields BEFORE commit (avoids lazy-load after commit)
        response_data = dict(
            id=str(order.id),
            tenant_id=str(order.tenant_id),
            customer_id=str(order.customer_id) if order.customer_id else None,
            customer_name=order.customer.name if order.customer else None,
            customer_phone=order.customer.phone_number if order.customer else None,
            order_number=order.order_number,
            order_date=order.order_date,
            total_amount=float(order.total_amount),
            total_gst=float(order.total_gst),
            discount_amount=float(order.discount_amount),
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            is_credit=order.is_credit,
            credit_amount=float(order.credit_amount),
            status=order.status,
            notes=order.notes,
            source=order.source,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
            # Also update snapshot
            if field in response_data:
                response_data[field] = value

        await db.commit()

        response_data["updated_at"] = datetime.utcnow()

        return BaseResponse(
            success=True,
            message="Order updated",
            data={"order": OrderResponse(**response_data)},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")


@router.delete("/{order_id}", response_model=BaseResponse)
async def delete_order(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel an order (sets status to cancelled, restores inventory)"""
    try:
        tenant_id = _get_tenant_id(credentials)
        order = await _get_order(order_id, tenant_id, db)

        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        # Restore inventory
        for item in order.items:
            if item.inventory:
                item.inventory.quantity += item.quantity

        # Reverse credit if applicable
        if order.is_credit and order.customer:
            order.customer.current_balance -= order.total_amount
            if order.customer.current_balance < 0:
                order.customer.current_balance = 0

        order.status = "cancelled"
        await db.commit()

        return BaseResponse(
            success=True,
            message="Order cancelled, inventory restored",
            data={"order_id": order_id, "status": "cancelled"},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error cancelling order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")
