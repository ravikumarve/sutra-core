"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema"""
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone_number_id', sa.String(length=255), nullable=False),
        sa.Column('gst_state_code', sa.String(length=2), nullable=False),
        sa.Column('industry', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('length(gst_state_code) = 2', name='check_gst_state_code_length'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number_id')
    )
    op.create_index('idx_tenants_phone_number_id', 'tenants', ['phone_number_id'], unique=False)
    op.create_index('idx_tenants_industry', 'tenants', ['industry'], unique=False)
    op.create_index('idx_tenants_name', 'tenants', ['name'], unique=False)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number'),
        sa.UniqueConstraint('tenant_id', 'phone_number', name='uq_user_tenant_phone')
    )
    op.create_index('idx_users_tenant_phone', 'users', ['tenant_id', 'phone_number'], unique=False)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)
    
    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('hsn_code', sa.String(length=8), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('purchase_price', sa.Float(), nullable=False),
        sa.Column('selling_price', sa.Float(), nullable=False),
        sa.Column('gst_rate', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('min_stock_level', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'sku', name='uq_inventory_tenant_sku'),
        sa.CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        sa.CheckConstraint('selling_price >= 0', name='check_selling_price_non_negative')
    )
    op.create_index('idx_inventory_tenant_sku', 'inventory', ['tenant_id', 'sku'], unique=False)
    op.create_index('idx_inventory_tenant_name', 'inventory', ['tenant_id', 'name'], unique=False)
    op.create_index('idx_inventory_category', 'inventory', ['category'], unique=False)
    op.create_index('idx_inventory_name', 'inventory', ['name'], unique=False)
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('credit_limit', sa.Float(), nullable=False),
        sa.Column('current_balance', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'phone_number', name='uq_customer_tenant_phone'),
        sa.CheckConstraint('credit_limit >= 0', name='check_credit_limit_non_negative')
    )
    op.create_index('idx_customers_tenant_phone', 'customers', ['tenant_id', 'phone_number'], unique=False)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=True),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('total_gst', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=False),
        sa.Column('is_credit', sa.Boolean(), nullable=False),
        sa.Column('credit_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.CheckConstraint('total_amount >= 0', name='check_total_amount_non_negative'),
        sa.CheckConstraint('total_gst >= 0', name='check_total_gst_non_negative')
    )
    op.create_index('idx_orders_tenant_date', 'orders', ['tenant_id', 'order_date'], unique=False)
    op.create_index('idx_orders_customer', 'orders', ['customer_id'], unique=False)
    op.create_index('idx_orders_status', 'orders', ['status'], unique=False)
    op.create_index('idx_orders_payment_status', 'orders', ['payment_status'], unique=False)
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('inventory_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('gst_rate', sa.Float(), nullable=False),
        sa.Column('gst_amount', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_quantity_positive'),
        sa.CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative')
    )
    op.create_index('idx_order_items_order', 'order_items', ['order_id'], unique=False)
    op.create_index('idx_order_items_inventory', 'order_items', ['inventory_id'], unique=False)
    
    # Create credit_ledger table
    op.create_table(
        'credit_ledger',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount != 0', name='check_amount_non_zero')
    )
    op.create_index('idx_credit_ledger_tenant_customer', 'credit_ledger', ['tenant_id', 'customer_id'], unique=False)
    op.create_index('idx_credit_ledger_tenant_date', 'credit_ledger', ['tenant_id', 'created_at'], unique=False)
    op.create_index('idx_credit_ledger_type', 'credit_ledger', ['transaction_type'], unique=False)
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_log_tenant_event', 'audit_log', ['tenant_id', 'event_type'], unique=False)
    op.create_index('idx_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'], unique=False)
    op.create_index('idx_audit_log_created_at', 'audit_log', ['created_at'], unique=False)
    op.create_index('idx_audit_log_event_type', 'audit_log', ['event_type'], unique=False)
    
    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('webhook_id', sa.String(length=255), nullable=True),
        sa.Column('message_id', sa.String(length=255), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('processing_attempts', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhook_events_tenant_status', 'webhook_events', ['tenant_id', 'processing_status'], unique=False)
    op.create_index('idx_webhook_events_message_id', 'webhook_events', ['message_id'], unique=False)
    op.create_index('idx_webhook_events_received_at', 'webhook_events', ['received_at'], unique=False)
    op.create_index('idx_webhook_events_event_type', 'webhook_events', ['event_type'], unique=False)


def downgrade() -> None:
    """Downgrade database schema"""
    
    # Drop tables in reverse order of creation
    op.drop_index('idx_webhook_events_event_type', table_name='webhook_events')
    op.drop_index('idx_webhook_events_received_at', table_name='webhook_events')
    op.drop_index('idx_webhook_events_message_id', table_name='webhook_events')
    op.drop_index('idx_webhook_events_tenant_status', table_name='webhook_events')
    op.drop_table('webhook_events')
    
    op.drop_index('idx_audit_log_created_at', table_name='audit_log')
    op.drop_index('idx_audit_log_user', table_name='audit_log')
    op.drop_index('idx_audit_log_entity', table_name='audit_log')
    op.drop_index('idx_audit_log_tenant_event', table_name='audit_log')
    op.drop_table('audit_log')
    
    op.drop_index('idx_credit_ledger_type', table_name='credit_ledger')
    op.drop_index('idx_credit_ledger_tenant_date', table_name='credit_ledger')
    op.drop_index('idx_credit_ledger_tenant_customer', table_name='credit_ledger')
    op.drop_table('credit_ledger')
    
    op.drop_index('idx_order_items_inventory', table_name='order_items')
    op.drop_index('idx_order_items_order', table_name='order_items')
    op.drop_table('order_items')
    
    op.drop_index('idx_orders_payment_status', table_name='orders')
    op.drop_index('idx_orders_status', table_name='orders')
    op.drop_index('idx_orders_customer', table_name='orders')
    op.drop_index('idx_orders_tenant_date', table_name='orders')
    op.drop_table('orders')
    
    op.drop_index('idx_customers_tenant_phone', table_name='customers')
    op.drop_table('customers')
    
    op.drop_index('idx_inventory_name', table_name='inventory')
    op.drop_index('idx_inventory_category', table_name='inventory')
    op.drop_index('idx_inventory_tenant_name', table_name='inventory')
    op.drop_index('idx_inventory_tenant_sku', table_name='inventory')
    op.drop_table('inventory')
    
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_tenant_phone', table_name='users')
    op.drop_table('users')
    
    op.drop_index('idx_tenants_name', table_name='tenants')
    op.drop_index('idx_tenants_industry', table_name='tenants')
    op.drop_index('idx_tenants_phone_number_id', table_name='tenants')
    op.drop_table('tenants')