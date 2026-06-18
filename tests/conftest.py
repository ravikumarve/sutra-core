"""
Pytest Configuration
Test configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.config.settings import settings
from src.db.connection import get_db_session
from src.agents.coordinator import agent_coordinator
from src.agents.messages.message_schema import AgentMessage, AgentType, MessageType


# ============================================
# Test Configuration
# ============================================

pytest_plugins = ["pytest_asyncio"]


# ============================================
# Fixtures
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """
    Create test database session
    """
    from src.db.connection import db_manager, Base
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Create test database engine
    test_engine = db_manager.create_engine(test_mode=True)
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup: Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Dispose engine
    await test_engine.dispose()


@pytest.fixture
async def mock_redis():
    """
    Mock Redis client
    """
    redis = AsyncMock()
    yield redis


@pytest.fixture
async def mock_coordinator():
    """
    Mock agent coordinator
    """
    coordinator = Mock(spec=agent_coordinator)
    coordinator.is_running = True
    coordinator.tenant_agents = {}
    yield coordinator


@pytest.fixture
def sample_agent_message():
    """
    Sample agent message for testing
    """
    return AgentMessage(
        tenant_id="test_tenant",
        source_agent=AgentType.LIAISON,
        message_type=MessageType.INTENT_EXTRACTED,
        payload={
            "intent": "order",
            "entities": {"product": "shirt", "quantity": 2},
            "confidence": 0.9
        },
        confidence=0.9
    )


@pytest.fixture
def sample_webhook_payload():
    """
    Sample WhatsApp webhook payload
    """
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": "987654321",
                                "display_phone_number": "+919876543210"
                            },
                            "messages": [
                                {
                                    "id": "msg_123",
                                    "from": "919876543210",
                                    "type": "text",
                                    "timestamp": "1700000000",
                                    "text": {
                                        "body": "Hello, I want to order 2 shirts"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_tenant_data():
    """
    Sample tenant data for testing
    """
    return {
        "name": "Test Business",
        "phone_number_id": "987654321",
        "gst_state_code": 24,
        "industry": "textiles",
        "contact_email": "test@example.com",
        "contact_phone": "+919876543210"
    }


@pytest.fixture
def mock_http_client():
    """
    Mock HTTP client for API testing
    """
    client = Mock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def auth_headers():
    """
    Sample authentication headers
    """
    return {
        "Authorization": "Bearer test_token_12345",
        "Content-Type": "application/json"
    }


# ============================================
# Test Helpers
# ============================================

class TestHelpers:
    """Helper functions for testing"""
    
    @staticmethod
    def create_test_message(
        tenant_id: str = "test_tenant",
        agent_type: AgentType = AgentType.LIAISON,
        message_type: MessageType = MessageType.INTENT_EXTRACTED,
        payload: dict = None
    ) -> AgentMessage:
        """Create test agent message"""
        return AgentMessage(
            tenant_id=tenant_id,
            source_agent=agent_type,
            message_type=message_type,
            payload=payload or {},
            confidence=1.0
        )
    
    @staticmethod
    async def wait_for_condition(
        condition,
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for condition to be true"""
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            if await condition():
                return True
            await asyncio.sleep(interval)
        return False


@pytest.fixture
def test_helpers():
    """Test helpers fixture"""
    return TestHelpers


# ============================================
# Test Configuration
# ============================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


# ============================================
# Test Hooks
# ============================================

@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """
    Setup test environment before all tests
    """
    from src.db.connection import init_database, close_database
    import os
    
    # Set test environment variables (SQLite for dev/CI, no PostgreSQL required)
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///./test_sutra.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["TEST_MODE"] = "true"
    os.environ["AUDIT_LOGGING_ENABLED"] = "false"
    
    # Initialize test database
    await init_database(test_mode=True)
    
    yield
    
    # Cleanup test environment
    await close_database()


@pytest.fixture(autouse=True)
async def reset_state():
    """
    Reset state before each test
    """
    from src.db.connection import db_manager
    from sqlalchemy import text
    
    # Reset database state
    async with db_manager.get_session() as session:
        # Truncate all tables (works for both SQLite and PostgreSQL)
        import sqlalchemy as sa
        conn = await session.connection()
        dialect = conn.dialect.name
        if dialect == "postgresql":
            await session.execute(text("SELECT setval('tenants_id_seq', 1, false)"))
            await session.execute(text("SELECT setval('users_id_seq', 1, false)"))
            await session.execute(text("SELECT setval('inventory_id_seq', 1, false)"))
            await session.execute(text("SELECT setval('customers_id_seq', 1, false)"))
            await session.execute(text("SELECT setval('orders_id_seq', 1, false)"))
            await session.execute(text("SELECT setval('credit_ledger_id_seq', 1, false)"))
        await session.commit()
    
    # Reset Redis state (if Redis is available)
    try:
        import redis.asyncio as redis
        redis_client = await redis.from_url("redis://localhost:6379/1")
        await redis_client.flushdb()
        await redis_client.close()
    except Exception:
        # Redis not available, skip
        pass
    
    # Reset agent coordinator state
    if hasattr(agent_coordinator, 'tenant_agents'):
        agent_coordinator.tenant_agents.clear()
    
    yield
    
    # Cleanup after test
    # Additional cleanup if needed