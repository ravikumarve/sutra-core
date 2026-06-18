"""
Customer API Routes
CRUD endpoints for customer management with credit tracking
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.api.schemas.common import BaseResponse
from src.api.schemas.customers import (
    CustomerResponse,
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerListData,
)
from src.db.connection import get_db_session
from src.db.models import Customer, Order, CreditLedger
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


async def _get_customer(customer_id: str, tenant_id: str, db: AsyncSession) -> Customer:
    """Get customer by ID with tenant isolation"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

    result = await db.execute(
        select(Customer).where(
            and_(
                Customer.id == cust_uuid,
                Customer.tenant_id == uuid.UUID(tenant_id),
            )
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _customer_to_response(customer: Customer, total_orders: int = 0) -> CustomerResponse:
    """Convert ORM to response"""
    return CustomerResponse(
        id=str(customer.id),
        tenant_id=str(customer.tenant_id),
        phone_number=customer.phone_number,
        name=customer.name,
        address=customer.address,
        credit_limit=float(customer.credit_limit),
        current_balance=float(customer.current_balance),
        is_active=customer.is_active,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        total_orders=total_orders,
    )


@router.get("/", response_model=BaseResponse)
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name or phone"),
    has_balance: Optional[bool] = Query(None, description="Filter by outstanding balance"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """List customers with pagination, search, and balance filter"""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        filters = [Customer.tenant_id == tenant_uuid]
        if is_active is not None:
            filters.append(Customer.is_active == is_active)
        if has_balance is True:
            filters.append(Customer.current_balance > 0)
        elif has_balance is False:
            filters.append(Customer.current_balance == 0)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(Customer.name.ilike(term), Customer.phone_number.ilike(term))
            )

        # Count total
        count_result = await db.execute(
            select(func.count(Customer.id)).where(and_(*filters))
        )
        total = count_result.scalar() or 0

        # Fetch customers
        result = await db.execute(
            select(Customer)
            .where(and_(*filters))
            .order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        customers = result.scalars().all()

        # Fetch order counts for each customer
        items = []
        for c in customers:
            order_count = await db.execute(
                select(func.count(Order.id)).where(
                    and_(
                        Order.customer_id == c.id,
                        Order.tenant_id == tenant_uuid,
                    )
                )
            )
            total_orders = order_count.scalar() or 0
            items.append(_customer_to_response(c, total_orders))

        return BaseResponse(
            success=True,
            data={
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing customers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")


@router.get("/{customer_id}", response_model=BaseResponse)
async def get_customer(
    customer_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single customer by ID"""
    try:
        tenant_id = _get_tenant_id(credentials)
        customer = await _get_customer(customer_id, tenant_id, db)

        # Get order count
        order_count = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.customer_id == uuid.UUID(customer_id),
                    Order.tenant_id == uuid.UUID(tenant_id),
                )
            )
        )

        return BaseResponse(
            success=True,
            data={"customer": _customer_to_response(customer, order_count.scalar() or 0)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get customer")


@router.post("/", response_model=BaseResponse, status_code=201)
async def create_customer(
    request: CustomerCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new customer"""
    try:
        tenant_id = _get_tenant_id(credentials)
        tenant_uuid = uuid.UUID(tenant_id)

        # Check duplicate phone
        result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == tenant_uuid,
                    Customer.phone_number == request.phone_number,
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Customer with phone {request.phone_number} already exists",
            )

        customer = Customer(
            tenant_id=tenant_uuid,
            phone_number=request.phone_number,
            name=request.name,
            address=request.address,
            credit_limit=request.credit_limit,
            current_balance=0.0,
            is_active=True,
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        logger.info(f"Created customer: {customer.name or customer.phone_number}")

        return BaseResponse(
            success=True,
            message="Customer created",
            data={"customer": _customer_to_response(customer)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.put("/{customer_id}", response_model=BaseResponse)
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a customer"""
    try:
        tenant_id = _get_tenant_id(credentials)
        customer = await _get_customer(customer_id, tenant_id, db)

        # Check phone uniqueness if changing
        if request.phone_number is not None and request.phone_number != customer.phone_number:
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.tenant_id == uuid.UUID(tenant_id),
                        Customer.phone_number == request.phone_number,
                        Customer.id != customer.id,
                    )
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail=f"Another customer with phone {request.phone_number} already exists",
                )

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        await db.commit()
        await db.refresh(customer)

        return BaseResponse(
            success=True,
            message="Customer updated",
            data={"customer": _customer_to_response(customer)},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")


@router.delete("/{customer_id}", response_model=BaseResponse)
async def delete_customer(
    customer_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Soft-delete a customer"""
    try:
        tenant_id = _get_tenant_id(credentials)
        customer = await _get_customer(customer_id, tenant_id, db)

        customer.is_active = False
        await db.commit()

        return BaseResponse(
            success=True,
            message="Customer deactivated",
            data={"customer_id": customer_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")


@router.get("/{customer_id}/ledger", response_model=BaseResponse)
async def get_customer_ledger(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
):
    """Get credit ledger entries for a customer"""
    try:
        tenant_id = _get_tenant_id(credentials)
        # Verify customer exists
        await _get_customer(customer_id, tenant_id, db)

        cust_uuid = uuid.UUID(customer_id)
        tenant_uuid = uuid.UUID(tenant_id)

        count_result = await db.execute(
            select(func.count(CreditLedger.id)).where(
                and_(
                    CreditLedger.customer_id == cust_uuid,
                    CreditLedger.tenant_id == tenant_uuid,
                )
            )
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(CreditLedger)
            .where(
                and_(
                    CreditLedger.customer_id == cust_uuid,
                    CreditLedger.tenant_id == tenant_uuid,
                )
            )
            .order_by(CreditLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        entries = result.scalars().all()

        return BaseResponse(
            success=True,
            data={
                "entries": [
                    {
                        "id": str(e.id),
                        "transaction_type": e.transaction_type,
                        "amount": float(e.amount),
                        "balance_after": float(e.balance_after),
                        "description": e.description,
                        "reference_number": e.reference_number,
                        "source": e.source,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in entries
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ledger for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch ledger")
