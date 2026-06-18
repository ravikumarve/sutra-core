"""
Database Models
Core data models with tenant isolation and audit support
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    JSON,
    Uuid,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.db.connection import Base

# Database-agnostic type aliases
# Maps to PostgreSQL UUID / SQLite BLOB or VARCHAR
UUID_TYPE = Uuid()
# Maps to PostgreSQL JSON_TYPE / SQLite TEXT
JSON_TYPE = JSON


class Tenant(Base):
    """Tenant registry for multi-tenancy"""
    
    __tablename__ = "tenants"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    phone_number_id = Column(String(255), nullable=False, unique=True)  # Meta Phone Number ID
    gst_state_code = Column(String(2), nullable=False)  # GST state code
    industry = Column(String(50), nullable=False)  # textiles, hardware, kirana, pharma
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration
    config = Column(JSON_TYPE, nullable=True)  # Tenant-specific configuration
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    credit_ledger = relationship("CreditLedger", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_tenants_phone_number_id', 'phone_number_id'),
        Index('idx_tenants_industry', 'industry'),
        CheckConstraint('length(gst_state_code) = 2', name='check_gst_state_code_length'),
    )


class User(Base):
    """Tenant users with role-based access control"""
    
    __tablename__ = "users"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, unique=True)  # WhatsApp phone number
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="shop_owner")  # shop_owner, manager, staff
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # Optional for WhatsApp-only auth
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_users_tenant_phone', 'tenant_id', 'phone_number'),
        Index('idx_users_role', 'role'),
        UniqueConstraint('tenant_id', 'phone_number', name='uq_user_tenant_phone'),
    )


class Inventory(Base):
    """Product inventory with tenant isolation"""
    
    __tablename__ = "inventory"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False)  # Stock Keeping Unit
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Product details
    category = Column(String(100), nullable=True, index=True)
    hsn_code = Column(String(8), nullable=True)  # GST HSN code
    unit = Column(String(50), nullable=False)  # pieces, kg, meters, etc.
    
    # Pricing
    purchase_price = Column(Float, nullable=False)  # Cost price
    selling_price = Column(Float, nullable=False)  # MRP/selling price
    gst_rate = Column(Float, default=0.0, nullable=False)  # GST percentage
    
    # Stock
    quantity = Column(Integer, default=0, nullable=False)  # Current stock
    min_stock_level = Column(Integer, default=10, nullable=False)  # Reorder threshold
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="inventory")
    order_items = relationship("OrderItem", back_populates="inventory", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_inventory_tenant_sku', 'tenant_id', 'sku'),
        Index('idx_inventory_tenant_name', 'tenant_id', 'name'),
        Index('idx_inventory_category', 'category'),
        UniqueConstraint('tenant_id', 'sku', name='uq_inventory_tenant_sku'),
        CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        CheckConstraint('selling_price >= 0', name='check_selling_price_non_negative'),
    )


class Customer(Base):
    """Customer information for orders and credit"""
    
    __tablename__ = "customers"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)  # WhatsApp phone number
    name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # Credit information
    credit_limit = Column(Float, default=0.0, nullable=False)  # Maximum credit allowed
    current_balance = Column(Float, default=0.0, nullable=False)  # Current outstanding
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    credit_entries = relationship("CreditLedger", back_populates="customer", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_customers_tenant_phone', 'tenant_id', 'phone_number'),
        UniqueConstraint('tenant_id', 'phone_number', name='uq_customer_tenant_phone'),
        CheckConstraint('credit_limit >= 0', name='check_credit_limit_non_negative'),
    )


class Order(Base):
    """Sales orders with financial integrity"""
    
    __tablename__ = "orders"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID_TYPE, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number = Column(String(50), nullable=False, unique=True)  # Human-readable order ID
    
    # Order details
    order_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)  # Total order value
    total_gst = Column(Float, default=0.0, nullable=False)  # Total GST
    discount_amount = Column(Float, default=0.0, nullable=False)  # Discount applied
    
    # Payment
    payment_method = Column(String(50), nullable=False)  # cash, credit, upi, etc.
    payment_status = Column(String(50), default="pending", nullable=False)  # pending, paid, partial
    
    # Credit
    is_credit = Column(Boolean, default=False, nullable=False)  # Is this a credit order
    credit_amount = Column(Float, default=0.0, nullable=False)  # Amount on credit
    
    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, confirmed, delivered, cancelled
    
    # Metadata
    notes = Column(Text, nullable=True)
    source = Column(String(50), default="whatsapp", nullable=False)  # whatsapp, manual, api
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_orders_tenant_date', 'tenant_id', 'order_date'),
        Index('idx_orders_customer', 'customer_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_payment_status', 'payment_status'),
        CheckConstraint('total_amount >= 0', name='check_total_amount_non_negative'),
        CheckConstraint('total_gst >= 0', name='check_total_gst_non_negative'),
    )


class OrderItem(Base):
    """Order line items with inventory tracking"""
    
    __tablename__ = "order_items"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(UUID_TYPE, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Item details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Price at time of order
    gst_rate = Column(Float, default=0.0, nullable=False)  # GST rate at time of order
    gst_amount = Column(Float, default=0.0, nullable=False)  # GST amount for this item
    total_amount = Column(Float, nullable=False)  # Line total
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    inventory = relationship("Inventory", back_populates="order_items")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_order_items_order', 'order_id'),
        Index('idx_order_items_inventory', 'inventory_id'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
    )


class CreditLedger(Base):
    """Immutable credit ledger for financial integrity"""
    
    __tablename__ = "credit_ledger"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID_TYPE, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID_TYPE, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # credit, debit, payment, adjustment
    amount = Column(Float, nullable=False)  # Positive for credit, negative for debit
    balance_after = Column(Float, nullable=False)  # Balance after this transaction
    
    # Reference
    reference_number = Column(String(100), nullable=True)  # External reference
    description = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(String(255), nullable=True)  # User or system that created entry
    source = Column(String(50), default="system", nullable=False)  # system, manual, api
    
    # Timestamps (immutable)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="credit_ledger")
    customer = relationship("Customer", back_populates="credit_entries")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_credit_ledger_tenant_customer', 'tenant_id', 'customer_id'),
        Index('idx_credit_ledger_tenant_date', 'tenant_id', 'created_at'),
        Index('idx_credit_ledger_type', 'transaction_type'),
        CheckConstraint('amount != 0', name='check_amount_non_zero'),
    )


class AuditLog(Base):
    """Immutable audit log for compliance and debugging"""
    
    __tablename__ = "audit_log"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # order_created, payment_received, etc.
    entity_type = Column(String(100), nullable=False)  # order, customer, inventory, etc.
    entity_id = Column(UUID_TYPE, nullable=True, index=True)
    
    # Changes
    old_values = Column(JSON_TYPE, nullable=True)  # Previous state
    new_values = Column(JSON_TYPE, nullable=True)  # New state
    changes = Column(JSON_TYPE, nullable=True)  # Diff of changes
    
    # Context
    user_id = Column(UUID_TYPE, nullable=True)  # User who made the change
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Metadata
    source = Column(String(50), default="system", nullable=False)  # system, manual, api, webhook
    description = Column(Text, nullable=True)
    
    # Timestamps (immutable)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_log_tenant_event', 'tenant_id', 'event_type'),
        Index('idx_audit_log_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_created_at', 'created_at'),
    )


class WebhookEvent(Base):
    """Webhook event log for debugging and replay"""
    
    __tablename__ = "webhook_events"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # message, status, etc.
    webhook_id = Column(String(255), nullable=True)  # Meta webhook ID
    message_id = Column(String(255), nullable=True, index=True)  # WhatsApp message ID
    
    # Payload
    payload = Column(JSON_TYPE, nullable=False)  # Full webhook payload
    
    # Processing
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processed, failed
    processing_attempts = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_events_tenant_status', 'tenant_id', 'processing_status'),
        Index('idx_webhook_events_message_id', 'message_id'),
        Index('idx_webhook_events_received_at', 'received_at'),
    )


class MessageAuditLog(Base):
    """Message audit log for compliance and debugging"""
    
    __tablename__ = "message_audit_log"
    
    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Message details
    message_id = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # message_sent, message_received, etc.
    source_agent = Column(String(100), nullable=False)
    target_agent = Column(String(100), nullable=True)
    message_type = Column(String(100), nullable=False)
    
    # Payload and status
    payload = Column(JSON_TYPE, nullable=True)
    status = Column(String(50), default="success", nullable=False)  # success, failed, pending
    error_message = Column(Text, nullable=True)
    
    # Additional info
    additional_info = Column(JSON_TYPE, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_message_audit_log_tenant_message', 'tenant_id', 'message_id'),
        Index('idx_message_audit_log_action', 'action'),
        Index('idx_message_audit_log_timestamp', 'timestamp'),
        Index('idx_message_audit_log_status', 'status'),
    )