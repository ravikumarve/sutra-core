"""
Dashboard API Routes
Analytics endpoints for the SUTRA Core frontend dashboard
"""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.common import BaseResponse
from src.db.connection import get_db_session
from src.db.models import Order, Inventory, Customer, OrderItem
from src.security.auth import auth_manager

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.get("/kpi", response_model=BaseResponse)
async def get_dashboard_kpi(
    tenant_id: str = Query(..., description="Tenant ID"),
    days: int = Query(30, description="Lookback period in days"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Dashboard KPI aggregation.
    Returns total_orders, revenue_mtd, udhaar_outstanding, low_stock_count,
    recent_orders, low_stock_items, and top_movers.
    """
    try:
        # Verify token
        user = auth_manager.verify_token(credentials.credentials, "access")
        if user.get("tenant_id") != tenant_id and user.get("role") not in ("admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Tenant access denied")

        # Convert tenant_id to UUID for SQLAlchemy compatibility
        tenant_uuid = uuid.UUID(tenant_id)

        now = datetime.utcnow()
        cut_date = now - timedelta(days=days)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # ── 1. Total Orders ──
        result = await db.execute(
            select(func.count(Order.id)).where(
                and_(Order.tenant_id == tenant_uuid, Order.created_at >= cut_date)
            )
        )
        total_orders = result.scalar() or 0

        # ── 2. Revenue MTD ──
        result = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                and_(
                    Order.tenant_id == tenant_uuid,
                    Order.created_at >= month_start,
                    Order.status.in_(["confirmed", "delivered"]),
                )
            )
        )
        revenue_mtd = float(result.scalar() or 0)

        # ── 3. Udhaar Outstanding ──
        result = await db.execute(
            select(func.coalesce(func.sum(Customer.current_balance), 0)).where(
                and_(Customer.tenant_id == tenant_uuid, Customer.is_active == True)
            )
        )
        udhaar_outstanding = float(result.scalar() or 0)

        # Customers with outstanding balance
        result = await db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.tenant_id == tenant_uuid,
                    Customer.current_balance > 0,
                    Customer.is_active == True,
                )
            )
        )
        customers_with_debt = result.scalar() or 0

        # ── 4. Low Stock Count ──
        result = await db.execute(
            select(func.count(Inventory.id)).where(
                and_(
                    Inventory.tenant_id == tenant_uuid,
                    Inventory.is_active == True,
                    Inventory.quantity < Inventory.min_stock_level,
                )
            )
        )
        low_stock_count = result.scalar() or 0

        # Total active SKUs
        result = await db.execute(
            select(func.count(Inventory.id)).where(
                and_(Inventory.tenant_id == tenant_uuid, Inventory.is_active == True)
            )
        )
        total_skus = result.scalar() or 0

        # ── 5. Recent Orders ──
        result = await db.execute(
            select(
                Order.id,
                Order.order_number,
                Order.total_amount,
                Order.status,
                Order.created_at,
                Customer.name,
            )
            .outerjoin(Customer, Order.customer_id == Customer.id)
            .where(Order.tenant_id == tenant_uuid)
            .order_by(Order.created_at.desc())
            .limit(5)
        )
        recent_orders = [
            {
                "id": str(row.id),
                "order_number": row.order_number,
                "customer_name": row.name or "Walk-in",
                "total_amount": float(row.total_amount),
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in result
        ]

        # ── 6. Low Stock Items ──
        result = await db.execute(
            select(
                Inventory.sku,
                Inventory.name,
                Inventory.quantity,
                Inventory.min_stock_level,
                Inventory.unit,
            )
            .where(
                and_(
                    Inventory.tenant_id == tenant_uuid,
                    Inventory.is_active == True,
                    Inventory.quantity < Inventory.min_stock_level,
                )
            )
            .order_by(Inventory.quantity.asc())
            .limit(10)
        )
        low_stock_items = [
            {
                "sku": row.sku,
                "name": row.name,
                "remaining": row.quantity,
                "threshold": row.min_stock_level,
                "unit": row.unit,
            }
            for row in result
        ]

        # ── 7. Top Movers (last 90 days) ──
        result = await db.execute(
            select(
                Inventory.sku,
                Inventory.name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("total_sold"),
                func.coalesce(func.sum(OrderItem.total_amount), 0).label("total_revenue"),
            )
            .join(OrderItem, Inventory.id == OrderItem.inventory_id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                and_(
                    Inventory.tenant_id == tenant_uuid,
                    Order.tenant_id == tenant_uuid,
                    Order.status.in_(["confirmed", "delivered"]),
                    Order.created_at >= (now - timedelta(days=90)),
                )
            )
            .group_by(Inventory.id, Inventory.sku, Inventory.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        )
        top_movers = [
            {
                "sku": row.sku,
                "name": row.name,
                "total_sold": int(row.total_sold),
                "total_revenue": round(float(row.total_revenue), 2),
            }
            for row in result
        ]

        # ── 8. Previous period comparison ──
        prev_cut_date = cut_date - timedelta(days=days)

        result = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.tenant_id == tenant_uuid,
                    Order.created_at >= prev_cut_date,
                    Order.created_at < cut_date,
                )
            )
        )
        prev_orders = result.scalar() or 0

        result = await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                and_(
                    Order.tenant_id == tenant_uuid,
                    Order.created_at >= prev_cut_date,
                    Order.created_at < cut_date,
                    Order.status.in_(["confirmed", "delivered"]),
                )
            )
        )
        prev_revenue = float(result.scalar() or 0)

        orders_growth = (
            round(((total_orders - prev_orders) / prev_orders) * 100, 1)
            if prev_orders > 0
            else 0
        )
        revenue_growth = (
            round(((revenue_mtd - prev_revenue) / prev_revenue) * 100, 1)
            if prev_revenue > 0
            else 0
        )

        return BaseResponse(
            success=True,
            data={
                "kpi": {
                    "total_orders": {
                        "value": total_orders,
                        "change": f"{orders_growth:+.1f}%",
                        "trend": "up" if orders_growth >= 0 else "down",
                    },
                    "revenue_mtd": {
                        "value": round(revenue_mtd, 2),
                        "change": f"{revenue_growth:+.1f}%",
                        "trend": "up" if revenue_growth >= 0 else "down",
                    },
                    "udhaar_outstanding": {
                        "value": round(udhaar_outstanding, 2),
                        "customers_with_debt": customers_with_debt,
                    },
                    "low_stock_count": {
                        "value": low_stock_count,
                        "total_skus": total_skus,
                    },
                },
                "recent_orders": recent_orders,
                "low_stock_items": low_stock_items,
                "top_movers": top_movers,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard KPI failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}",
        )
