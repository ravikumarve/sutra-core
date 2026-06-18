"""
Integration Tests for Agent Communication
Tests end-to-end agent communication flows
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.coordinator import AgentCoordinator
from src.agents.liaison.liaison_agent import LiaisonAgent
from src.agents.strategist.strategist_agent import StrategistAgent
from src.agents.auditor.auditor_agent import AuditorAgent
from src.agents.messages.message_schema import (
    AgentMessage, AgentType, MessageType
)


@pytest.mark.integration
class TestAgentCommunication:
    """Test agent communication integration"""
    
    @pytest.fixture
    async def coordinator(self):
        """Create agent coordinator"""
        coordinator = AgentCoordinator()
        coordinator.redis_manager = AsyncMock()
        coordinator.redis_manager.connect = AsyncMock()
        coordinator.redis_manager.create_stream = AsyncMock(return_value=True)
        coordinator.redis_manager.create_consumer_group = AsyncMock(return_value=True)
        coordinator.redis_manager.cleanup_old_messages = AsyncMock(return_value=0)
        
        await coordinator.start()
        yield coordinator
        await coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_provision_tenant(self, coordinator):
        """Test tenant provisioning"""
        # Provision tenant
        success = await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Verify provisioning
        assert success == True
        assert "test_tenant" in coordinator.tenant_agents
        
        # Verify agents created
        tenant_agents = coordinator.tenant_agents["test_tenant"]
        assert "liaison" in tenant_agents
        assert "strategist" in tenant_agents
        assert "auditor" in tenant_agents
    
    @pytest.mark.asyncio
    async def test_deprovision_tenant(self, coordinator):
        """Test tenant deprovisioning"""
        # First provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Deprovision tenant
        success = await coordinator.deprovision_tenant("test_tenant")
        
        # Verify deprovisioning
        assert success == True
        assert "test_tenant" not in coordinator.tenant_agents
    
    @pytest.mark.asyncio
    async def test_get_tenant_status(self, coordinator):
        """Test getting tenant status"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Get status
        status = await coordinator.get_tenant_status("test_tenant")
        
        # Verify status
        assert status is not None
        assert status["tenant_id"] == "test_tenant"
        assert "agents" in status
        assert "liaison" in status["agents"]
        assert "strategist" in status["agents"]
        assert "auditor" in status["agents"]
    
    @pytest.mark.asyncio
    async def test_liaison_to_strategist_communication(self, coordinator):
        """Test communication from Liaison to Strategist"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Get agents
        tenant_agents = coordinator.tenant_agents["test_tenant"]
        liaison = tenant_agents["liaison"]
        strategist = tenant_agents["strategist"]
        
        # Create message from Liaison
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            target_agent=AgentType.STRATEGIST,
            message_type=MessageType.BUSINESS_VALIDATION,
            payload={
                "intent": "order",
                "entities": {"product": "shirt", "quantity": 2},
                "confidence": 0.9,
                "is_valid": True,
                "reason": "Intent extracted successfully"
            },
            confidence=0.9
        )
        
        # Send message
        success = await liaison.send_message(message)
        
        # Verify message sent
        assert success == True
    
    @pytest.mark.asyncio
    async def test_strategist_to_auditor_communication(self, coordinator):
        """Test communication from Strategist to Auditor"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Get agents
        tenant_agents = coordinator.tenant_agents["test_tenant"]
        strategist = tenant_agents["strategist"]
        auditor = tenant_agents["auditor"]
        
        # Create message from Strategist
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.STRATEGIST,
            target_agent=AgentType.AUDITOR,
            message_type=MessageType.ORDER_CREATED,
            payload={
                "order_id": "ORD-123",
                "items": {"product": "shirt", "quantity": 2},
                "total_amount": 200.0
            },
            confidence=1.0
        )
        
        # Send message
        success = await strategist.send_message(message)
        
        # Verify message sent
        assert success == True
    
    @pytest.mark.asyncio
    async def test_message_flow_liaison_strategist_auditor(self, coordinator):
        """Test complete message flow: Liaison -> Strategist -> Auditor"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Get agents
        tenant_agents = coordinator.tenant_agents["test_tenant"]
        liaison = tenant_agents["liaison"]
        strategist = tenant_agents["strategist"]
        auditor = tenant_agents["auditor"]
        
        # Step 1: Liaison processes WhatsApp message
        whatsapp_message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.TEXT,
            payload={
                "text": "I want to order 2 shirts",
                "phone_number": "+919876543210"
            },
            confidence=1.0
        )
        
        liaison_response = await liaison.process_message(whatsapp_message)
        
        # Verify Liaison returns INTENT_EXTRACTED (processed from raw TEXT)
        assert liaison_response is not None
        assert liaison_response.message_type == MessageType.INTENT_EXTRACTED
        
        # Step 2: Strategist processes business logic
        strategist_message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            target_agent=AgentType.STRATEGIST,
            message_type=MessageType.BUSINESS_VALIDATION,
            payload=liaison_response.payload,
            confidence=liaison_response.confidence
        )
        
        strategist_response = await strategist.process_message(strategist_message)
        
        # Verify Strategist response
        assert strategist_response is not None
        
        # Step 3: Auditor processes order
        if strategist_response.message_type == MessageType.ORDER_CREATED:
            auditor_message = AgentMessage(
                tenant_id="test_tenant",
                source_agent=AgentType.STRATEGIST,
                target_agent=AgentType.AUDITOR,
                message_type=MessageType.ORDER_CREATED,
                payload=strategist_response.payload,
                confidence=strategist_response.confidence
            )
            
            auditor_response = await auditor.process_message(auditor_message)
            
            # Verify Auditor response
            assert auditor_response is not None
            assert auditor_response.message_type == MessageType.LEDGER_ENTRY
    
    @pytest.mark.asyncio
    async def test_restart_tenant_agents(self, coordinator):
        """Test restarting tenant agents"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Restart agents
        success = await coordinator.restart_tenant_agents("test_tenant")
        
        # Verify restart
        assert success == True
        assert "test_tenant" in coordinator.tenant_agents
    
    @pytest.mark.asyncio
    async def test_get_all_tenants(self, coordinator):
        """Test getting all tenants"""
        # Provision multiple tenants
        await coordinator.provision_tenant(
            tenant_id="tenant_1",
            tenant_name="Business 1",
            industry="textiles"
        )
        await coordinator.provision_tenant(
            tenant_id="tenant_2",
            tenant_name="Business 2",
            industry="hardware"
        )
        
        # Get all tenants
        tenants = await coordinator.get_all_tenants()
        
        # Verify tenants
        assert len(tenants) == 2
        tenant_ids = [t["tenant_id"] for t in tenants]
        assert "tenant_1" in tenant_ids
        assert "tenant_2" in tenant_ids
    
    @pytest.mark.asyncio
    async def test_cleanup_old_messages(self, coordinator):
        """Test cleaning up old messages"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Cleanup old messages
        cleaned = await coordinator.cleanup_old_messages(
            tenant_id="test_tenant",
            max_age_hours=24
        )
        
        # Verify cleanup
        assert cleaned >= 0
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, coordinator):
        """Test getting system status"""
        # Provision tenant
        await coordinator.provision_tenant(
            tenant_id="test_tenant",
            tenant_name="Test Business",
            industry="textiles"
        )
        
        # Get system status
        status = await coordinator.get_system_status()
        
        # Verify status
        assert status is not None
        assert "coordinator_running" in status
        assert "total_tenants" in status
        assert "tenants" in status
        assert "redis_connected" in status


@pytest.mark.integration
class TestMessageValidation:
    """Test message validation integration"""
    
    @pytest.mark.asyncio
    async def test_message_validation_success(self):
        """Test message validation - success"""
        from src.agents.messages.message_schema import MessageValidator
        
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.TEXT,
            payload={"text": "Hello"},
            confidence=0.9
        )
        
        validator = MessageValidator()
        is_valid, error = validator.validate_message(message)
        
        assert is_valid == True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_message_validation_expired(self):
        """Test message validation - expired"""
        from src.agents.messages.message_schema import MessageValidator
        from datetime import timedelta
        
        # expires_at must be AFTER timestamp (validator), but BEFORE now (for is_expired)
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.TEXT,
            payload={"text": "Hello"},
            confidence=0.9,
            timestamp=two_hours_ago,
            expires_at=one_hour_ago  # expired since now > one_hour_ago
        )
        
        validator = MessageValidator()
        is_valid, error = validator.validate_message(message)
        
        assert is_valid == False
        assert "expired" in error.lower()
    
    @pytest.mark.asyncio
    async def test_message_validation_low_confidence(self):
        """Test message validation - low confidence"""
        from src.agents.messages.message_schema import MessageValidator
        
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.TEXT,
            payload={"text": "Hello"},
            confidence=0.1
        )
        
        validator = MessageValidator()
        is_valid, error = validator.validate_message(message)
        
        # Low confidence should still be valid
        assert is_valid == True
    
    @pytest.mark.asyncio
    async def test_message_serialization(self):
        """Test message serialization"""
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.TEXT,
            payload={"text": "Hello"},
            confidence=0.9
        )
        
        # Serialize to JSON
        json_str = message.to_json()
        
        # Deserialize from JSON
        deserialized = AgentMessage.from_json(json_str)
        
        # Verify deserialization
        assert deserialized.tenant_id == message.tenant_id
        assert deserialized.source_agent == message.source_agent
        assert deserialized.message_type == message.message_type
        assert deserialized.confidence == message.confidence