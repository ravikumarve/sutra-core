"""
Seed Demo Data for SUTRA Core Development
Creates a demo tenant + user so the login flow works out of the box.

Usage:
    ./venv/bin/python scripts/seed_demo.py
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.connection import db_manager, Base
from src.db.models import Tenant, User, Customer, Inventory
from src.security.auth import auth_manager
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

DEMO_TENANT_NAME = "Demo Business"
DEMO_PHONE = "+919876543210"
DEMO_PASSWORD = "password123"
DEMO_NAME = "Demo User"


async def seed():
    # Initialize engine
    db_manager.create_engine(test_mode=False)

    # Create all tables
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("✅ Database tables ready")

    async with db_manager.get_session() as session:
        # Check if demo tenant exists
        result = await session.execute(
            select(Tenant).where(Tenant.name == DEMO_TENANT_NAME)
        )
        tenant = result.scalar_one_or_none()

        if tenant:
            log.info(f"ℹ️  Tenant '{DEMO_TENANT_NAME}' already exists (id={tenant.id})")
        else:
            tenant = Tenant(
                name=DEMO_TENANT_NAME,
                phone_number_id="demo_phone_id",
                gst_state_code="27",
                industry="general",
                is_active=True,
            )
            session.add(tenant)
            await session.flush()
            log.info(f"✅ Created tenant: {DEMO_TENANT_NAME} (id={tenant.id})")

        # Check if demo user exists
        result = await session.execute(
            select(User).where(User.phone_number == DEMO_PHONE)
        )
        user = result.scalar_one_or_none()

        if user:
            log.info(f"ℹ️  User '{DEMO_PHONE}' already exists (id={user.id})")
        else:
            password_hash = auth_manager.hash_password(DEMO_PASSWORD)
            user = User(
                tenant_id=tenant.id,
                phone_number=DEMO_PHONE,
                name=DEMO_NAME,
                role="admin",
                password_hash=password_hash,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            log.info(f"✅ Created user: {DEMO_PHONE} / {DEMO_PASSWORD}")

        # Seed sample customers
        sample_customers = [
            {"name": "Sharma Textiles", "phone": "+919876543211", "balance": 25000.0},
            {"name": "Gupta Kirana Store", "phone": "+919876543212", "balance": 0.0},
            {"name": "Patel Hardware", "phone": "+919876543213", "balance": 12500.0},
        ]

        for c in sample_customers:
            result = await session.execute(
                select(Customer).where(
                    Customer.tenant_id == tenant.id,
                    Customer.phone_number == c["phone"],
                )
            )
            if not result.scalar_one_or_none():
                session.add(
                    Customer(
                        tenant_id=tenant.id,
                        name=c["name"],
                        phone_number=c["phone"],
                        current_balance=c["balance"],
                        credit_limit=100000.0,
                        is_active=True,
                    )
                )
        log.info(f"✅ Seeded {len(sample_customers)} sample customers")

        # Seed inventory items
        sample_items = [
            {"sku": "SILK_RED", "name": "Silk Saree (Red)", "qty": 12, "min_stock": 20, "unit": "pieces", "price": 2490.0},
            {"sku": "COT_BLUE_M", "name": "Cotton Fabric (Blue)", "qty": 85, "min_stock": 30, "unit": "meter", "price": 300.0},
            {"sku": "PVC_1INCH", "name": "PVC Pipe 1inch", "qty": 45, "min_stock": 50, "unit": "pieces", "price": 82.0},
            {"sku": "LED_12W", "name": "LED Bulb 12W", "qty": 200, "min_stock": 25, "unit": "pieces", "price": 450.0},
            {"sku": "BAS_RICE_25", "name": "Basmati Rice 25kg", "qty": 3, "min_stock": 10, "unit": "bags", "price": 2250.0},
        ]

        for item in sample_items:
            result = await session.execute(
                select(Inventory).where(
                    Inventory.tenant_id == tenant.id,
                    Inventory.sku == item["sku"],
                )
            )
            if not result.scalar_one_or_none():
                session.add(
                    Inventory(
                        tenant_id=tenant.id,
                        sku=item["sku"],
                        name=item["name"],
                        quantity=item["qty"],
                        min_stock_level=item["min_stock"],
                        unit=item["unit"],
                        purchase_price=item["price"] * 0.6,
                        selling_price=item["price"],
                        gst_rate=12.0,
                        is_active=True,
                    )
                )
        log.info(f"✅ Seeded {len(sample_items)} sample inventory items")

        await session.commit()

    log.info("\n🎉 Seed complete! Login with:")
    log.info(f"   Phone: {DEMO_PHONE}")
    log.info(f"   Password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
