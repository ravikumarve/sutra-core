"""
Unit Tests for Liaison Agent
Tests intent extraction and message processing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.liaison.liaison_agent import LiaisonAgent
from src.agents.messages.message_schema import (
    AgentMessage, AgentType, MessageType, MessagePriority
)


@pytest.mark.unit
class TestLiaisonAgent:
    """Test Liaison Agent functionality"""
    
    @pytest.fixture
    async def liaison_agent(self):
        """Create Liaison agent instance"""
        agent = LiaisonAgent(tenant_id="test_tenant")
        # Mock Redis manager
        agent.redis_manager = AsyncMock()
        agent.redis_manager.connect = AsyncMock()
        agent.redis_manager.create_stream = AsyncMock(return_value=True)
        agent.redis_manager.create_consumer_group = AsyncMock(return_value=True)
        agent.redis_manager.read_messages = AsyncMock(return_value=[])
        agent.redis_manager.acknowledge_message = AsyncMock(return_value=True)
        agent.redis_manager.publish_message = AsyncMock(return_value="msg_123")
        agent.redis_manager.send_to_dead_letter_queue = AsyncMock(return_value=True)
        return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, liaison_agent):
        """Test agent initialization"""
        assert liaison_agent.agent_type == AgentType.LIAISON
        assert liaison_agent.tenant_id == "test_tenant"
        assert liaison_agent.is_running == False
        assert len(liaison_agent.supported_intents) > 0
    
    @pytest.mark.asyncio
    async def test_agent_start_stop(self, liaison_agent):
        """Test agent start and stop"""
        # Start agent
        await liaison_agent.start()
        assert liaison_agent.is_running == True
        
        # Stop agent
        await liaison_agent.stop()
        assert liaison_agent.is_running == False
    
    @pytest.mark.asyncio
    async def test_process_text_message(self, liaison_agent):
        """Test text message processing"""
        # Create test message
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.INTENT_EXTRACTED,
            payload={
                "text": "I want to order 2 shirts",
                "phone_number": "+919876543210"
            },
            confidence=1.0
        )
        
        # Process message
        response = await liaison_agent.process_message(message)
        
        # Verify response
        assert response is not None
        assert response.message_type == MessageType.INTENT_EXTRACTED
        assert "intent" in response.payload
        assert "entities" in response.payload
        assert "sentiment" in response.payload
    
    @pytest.mark.asyncio
    async def test_extract_intent_order(self, liaison_agent):
        """Test intent extraction for order"""
        text = "I want to order 5 shirts"
        result = await liaison_agent._extract_intent(text)
        
        assert result["intent"] == "order"
        assert result["confidence"] > 0.0
        assert "language" in result
    
    @pytest.mark.asyncio
    async def test_extract_intent_inquiry(self, liaison_agent):
        """Test intent extraction for inquiry"""
        text = "What is the price of this item?"
        result = await liaison_agent._extract_intent(text)
        
        assert result["intent"] == "inquiry"
        assert result["confidence"] > 0.0
    
    @pytest.mark.asyncio
    async def test_extract_intent_payment(self, liaison_agent):
        """Test intent extraction for payment"""
        text = "I want to pay my bill"
        result = await liaison_agent._extract_intent(text)
        
        assert result["intent"] == "payment"
        assert result["confidence"] > 0.0
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, liaison_agent):
        """Test entity extraction"""
        text = "I want to order 5 shirts"
        intent = "order"
        
        entities = await liaison_agent._extract_entities(text, intent)
        
        assert "numbers" in entities
        assert "potential_products" in entities
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, liaison_agent):
        """Test positive sentiment analysis"""
        text = "I love your products, they are great!"
        result = await liaison_agent._analyze_sentiment(text)
        
        assert result["sentiment"] == "positive"
        assert result["score"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, liaison_agent):
        """Test negative sentiment analysis"""
        text = "I hate this product, it's terrible"
        result = await liaison_agent._analyze_sentiment(text)
        
        assert result["sentiment"] == "negative"
        assert result["score"] < 0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, liaison_agent):
        """Test neutral sentiment analysis"""
        text = "I want to know about your products"
        result = await liaison_agent._analyze_sentiment(text)
        
        assert result["sentiment"] == "neutral"
        assert -0.1 <= result["score"] <= 0.1
    
    @pytest.mark.asyncio
    async def test_handle_whatsapp_webhook_text(self, liaison_agent):
        """Test WhatsApp webhook handling for text message"""
        webhook_data = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123456"},
                                "messages": [
                                    {
                                        "id": "msg_123",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                        "timestamp": "1700000000"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        message = await liaison_agent.handle_whatsapp_webhook(webhook_data)
        
        assert message is not None
        assert message.message_type == MessageType.INTENT_EXTRACTED
        assert message.payload["text"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_handle_whatsapp_webhook_audio(self, liaison_agent):
        """Test WhatsApp webhook handling for audio message"""
        webhook_data = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123456"},
                                "messages": [
                                    {
                                        "id": "msg_123",
                                        "type": "audio",
                                        "audio": {"id": "audio_123"},
                                        "timestamp": "1700000000"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        message = await liaison_agent.handle_whatsapp_webhook(webhook_data)
        
        assert message is not None
        assert message.message_type == MessageType.VOICE_TRANSCRIBED
        assert message.payload["audio_id"] == "audio_123"
    
    @pytest.mark.asyncio
    async def test_create_error_response(self, liaison_agent):
        """Test error response creation"""
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.INTENT_EXTRACTED,
            payload={},
            confidence=1.0
        )
        
        error_response = message.create_error_response(
            source_agent=AgentType.LIAISON,
            error_message="Test error",
            error_code="TEST_ERROR"
        )
        
        assert error_response.message_type == MessageType.ERROR
        assert error_response.payload["error"] == "Test error"
        assert error_response.payload["error_code"] == "TEST_ERROR"
    
    @pytest.mark.asyncio
    async def test_create_acknowledgment(self, liaison_agent):
        """Test acknowledgment creation"""
        message = AgentMessage(
            tenant_id="test_tenant",
            source_agent=AgentType.LIAISON,
            message_type=MessageType.INTENT_EXTRACTED,
            payload={},
            confidence=1.0
        )
        
        ack = message.create_acknowledgment(
            source_agent=AgentType.LIAISON,
            status="received"
        )
        
        assert ack.message_type == MessageType.ACKNOWLEDGMENT
        assert ack.payload["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, liaison_agent):
        """Test getting agent status"""
        status = await liaison_agent.get_status()
        
        assert status["agent_type"] == "liaison"
        assert status["tenant_id"] == "test_tenant"
        assert "is_running" in status
        assert "queue_size" in status