"""
Base Agent Class
Abstract base class for all agents in the system
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from src.agents.messages.message_schema import (
    AgentMessage, AgentType, MessageType, MessagePriority,
    MessageValidator, MessageSerializer, MessageTracer
)
from src.agents.messages.message_encryption import MessageSecurity
from src.agents.common.redis_streams import RedisStreamsManager
from src.agents.messages.message_audit import MessageAuditor, AuditAction, message_auditor
from src.config.settings import settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    Provides common functionality for message processing
    """
    
    def __init__(self, agent_type: AgentType, tenant_id: str):
        self.agent_type = agent_type
        self.tenant_id = tenant_id
        self.consumer_name = f"{agent_type.value}_{datetime.utcnow().timestamp()}"
        
        # Initialize components
        self.redis_manager = RedisStreamsManager()
        self.validator = MessageValidator()
        self.serializer = MessageSerializer()
        self.security = MessageSecurity()
        self.tracer = MessageTracer()
        self.auditor = message_auditor
        
        # Agent state
        self.is_running = False
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: List[asyncio.Task] = []
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.message_timeout = 300  # seconds
        
        logger.info(f"Initialized {agent_type.value} agent for tenant {tenant_id}")
    
    async def start(self) -> None:
        """
        Start the agent
        """
        try:
            logger.info(f"Starting {self.agent_type.value} agent...")
            
            # Connect to Redis
            await self.redis_manager.connect()
            
            # Create consumer group
            await self._setup_consumer_groups()
            
            # Start message processing
            self.is_running = True
            self.processing_tasks.append(
                asyncio.create_task(self._message_listener())
            )
            self.processing_tasks.append(
                asyncio.create_task(self._message_processor())
            )
            
            logger.info(f"{self.agent_type.value} agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the agent
        """
        try:
            logger.info(f"Stopping {self.agent_type.value} agent...")
            
            # Stop processing
            self.is_running = False
            
            # Cancel tasks
            for task in self.processing_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
            
            # Disconnect from Redis
            await self.redis_manager.disconnect()
            
            logger.info(f"{self.agent_type.value} agent stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop agent: {e}")
    
    async def _setup_consumer_groups(self) -> None:
        """
        Setup consumer groups for this agent
        """
        # Create stream for incoming messages
        await self.redis_manager.create_stream(
            tenant_id=self.tenant_id,
            stream_type=self.agent_type.value
        )
        
        # Create consumer group
        await self.redis_manager.create_consumer_group(
            tenant_id=self.tenant_id,
            stream_type=self.agent_type.value,
            agent_name=self.agent_type.value
        )
    
    async def _message_listener(self) -> None:
        """
        Listen for incoming messages
        """
        while self.is_running:
            try:
                # Read messages from stream
                messages = await self.redis_manager.read_messages(
                    tenant_id=self.tenant_id,
                    stream_type=self.agent_type.value,
                    agent_name=self.agent_type.value,
                    consumer_name=self.consumer_name,
                    count=10,
                    block=5000  # 5 second timeout
                )
                
                # Add messages to processing queue
                for message_data in messages:
                    await self.message_queue.put(message_data)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(1)
    
    async def _message_processor(self) -> None:
        """
        Process messages from queue
        """
        while self.is_running:
            try:
                # Get message from queue
                message_data = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # Process message
                await self._process_message(message_data)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processor: {e}")
                await asyncio.sleep(1)
    
    async def _deserialize_and_validate_message(
        self,
        data: Dict[str, Any]
    ) -> tuple[Optional[AgentMessage], Optional[str]]:
        """
        Deserialize and validate message from stream data
        
        Args:
            data: Raw message data from stream
            
        Returns:
            Tuple of (message, error_message) - message is None if validation fails
        """
        try:
            message = MessageSerializer.deserialize_from_stream(data)
            is_valid, error_message = self.validator.validate_message(message)
            
            if not is_valid:
                return None, error_message
                
            return message, None
        except Exception as e:
            logger.error(f"Error deserializing message: {e}")
            return None, str(e)

    async def _log_message_received(self, message: AgentMessage) -> None:
        """
        Log message received event to audit log
        
        Args:
            message: Validated message
        """
        self.tracer.trace_message(
            message=message,
            action="received",
            agent=self.agent_type
        )
        
        await self.auditor.log_message(
            action=AuditAction.MESSAGE_RECEIVED,
            message_id=message.message_id,
            tenant_id=message.tenant_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value if message.target_agent else None,
            message_type=message.message_type.value,
            payload=message.payload,
            status="received"
        )

    async def _log_message_processed(
        self,
        message: AgentMessage,
        processing_time: float
    ) -> None:
        """
        Log message processed event to audit log
        
        Args:
            message: Processed message
            processing_time: Processing time in milliseconds
        """
        await self.auditor.log_message(
            action=AuditAction.MESSAGE_PROCESSED,
            message_id=message.message_id,
            tenant_id=message.tenant_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value if message.target_agent else None,
            message_type=message.message_type.value,
            payload=message.payload,
            status="success",
            additional_info={"processing_time_ms": processing_time}
        )

    async def _log_message_failed(
        self,
        message_id: str,
        data: Dict[str, Any],
        error: str
    ) -> None:
        """
        Log message failed event to audit log
        
        Args:
            message_id: Message ID
            data: Raw message data
            error: Error message
        """
        await self.auditor.log_message(
            action=AuditAction.MESSAGE_FAILED,
            message_id=message_id,
            tenant_id=self.tenant_id,
            source_agent=self.agent_type.value,
            target_agent=None,
            message_type="unknown",
            payload=data,
            status="failed",
            error_message=error
        )

    async def _process_message(self, message_data: Dict[str, Any]) -> None:
        """
        Process a single message
        """
        message_id = message_data.get("message_id")
        stream = message_data.get("stream")
        data = message_data.get("data", {})
        
        try:
            # Deserialize and validate message
            message, error_message = await self._deserialize_and_validate_message(data)
            
            if error_message:
                logger.error(f"Invalid message: {error_message}")
                if message:
                    await self._handle_invalid_message(message, error_message)
                # Always ACK and DLQ to unblock consumer group
                await self.redis_manager.send_to_dead_letter_queue(
                    tenant_id=self.tenant_id,
                    message=data,
                    error=error_message or "deserialization_failed"
                )
                await self.redis_manager.acknowledge_message(
                    tenant_id=self.tenant_id,
                    stream_type=self.agent_type.value,
                    agent_name=self.agent_type.value,
                    message_id=message_id
                )
                return
            
            # Check expiration
            if message.is_expired():
                logger.warning(f"Message expired: {message_id}")
                await self._handle_expired_message(message)
                return
            
            # ERROR messages are terminal — don't respond with another error (would loop)
            if message.message_type == MessageType.ERROR:
                logger.warning(f"Received error message {message_id}: {message.payload.get('error', 'unknown')}")
                return
            
            # Log message received
            await self._log_message_received(message)
            
            # Process message (implemented by subclass)
            start_time = datetime.utcnow()
            response = await self.process_message(message)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Acknowledge message
            await self.redis_manager.acknowledge_message(
                tenant_id=self.tenant_id,
                stream_type=self.agent_type.value,
                agent_name=self.agent_type.value,
                message_id=message_id
            )
            
            # Log successful processing
            await self._log_message_processed(message, processing_time)
            
            # Send response if available
            if response:
                await self.send_message(response)
            
            logger.debug(f"Processed message {message_id} in {processing_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            
            # Send to dead letter queue
            await self.redis_manager.send_to_dead_letter_queue(
                tenant_id=self.tenant_id,
                message=data,
                error=str(e)
            )
            
            # Log failure
            await self._log_message_failed(message_id, data, str(e))
    
    async def _handle_invalid_message(
        self,
        message: AgentMessage,
        error_message: str
    ) -> None:
        """
        Handle invalid message
        """
        # Send error response
        error_response = message.create_error_response(
            source_agent=self.agent_type,
            error_message=error_message,
            error_code="INVALID_MESSAGE"
        )
        
        await self.send_message(error_response)
    
    async def _handle_expired_message(self, message: AgentMessage) -> None:
        """
        Handle expired message
        """
        # Log expiration
        await self.auditor.log_message(
            action=AuditAction.MESSAGE_EXPIRED,
            message_id=message.message_id,
            tenant_id=message.tenant_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value if message.target_agent else None,
            message_type=message.message_type.value,
            payload=message.payload,
            status="expired"
        )
    
    def _determine_target_stream(self, message: AgentMessage) -> str:
        """
        Determine target stream for message
        
        Args:
            message: Message to send
            
        Returns:
            Target stream name
        """
        if message.target_agent:
            return message.target_agent.value
        else:
            # Broadcast to all agents
            return "broadcast"

    async def _log_message_sent(self, message: AgentMessage, target_stream: str) -> None:
        """
        Log message sent event to audit log
        
        Args:
            message: Sent message
            target_stream: Target stream name
        """
        self.tracer.trace_message(
            message=message,
            action="sent",
            agent=self.agent_type
        )
        
        await self.auditor.log_message(
            action=AuditAction.MESSAGE_SENT,
            message_id=message.message_id,
            tenant_id=message.tenant_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value if message.target_agent else None,
            message_type=message.message_type.value,
            payload=message.payload,
            status="sent"
        )

    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send message to target agent
        """
        try:
            # Validate message
            is_valid, error_message = self.validator.validate_message(message)
            if not is_valid:
                logger.error(f"Cannot send invalid message: {error_message}")
                return False
            
            # Determine target stream
            target_stream = self._determine_target_stream(message)
            
            # Serialize message
            serialized = MessageSerializer.serialize_for_stream(message)
            
            # Publish to stream
            message_id = await self.redis_manager.publish_message(
                tenant_id=message.tenant_id,
                stream_type=target_stream,
                message=serialized
            )
            
            if message_id:
                # Log message sent
                await self._log_message_sent(message, target_stream)
                
                logger.debug(f"Sent message {message.message_id} to {target_stream}")
                return True
            else:
                logger.error(f"Failed to send message {message.message_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming message
        Must be implemented by subclass
        """
        pass
    
    async def send_heartbeat(self) -> None:
        """
        Send heartbeat message
        """
        heartbeat = AgentMessage(
            tenant_id=self.tenant_id,
            source_agent=self.agent_type,
            message_type=MessageType.HEARTBEAT,
            payload={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
        )
        
        await self.send_message(heartbeat)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get agent status
        """
        return {
            "agent_type": self.agent_type.value,
            "tenant_id": self.tenant_id,
            "is_running": self.is_running,
            "consumer_name": self.consumer_name,
            "queue_size": self.message_queue.qsize(),
            "active_tasks": len(self.processing_tasks)
        }