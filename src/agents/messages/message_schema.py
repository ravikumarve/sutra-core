"""
Agent Message Schema and Validation
Canonical message format for agent communication
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import uuid


class AgentType(str, Enum):
    """Agent types in the system"""
    LIAISON = "liaison"
    STRATEGIST = "strategist"
    AUDITOR = "auditor"


class MessageType(str, Enum):
    """Message types for agent communication"""
    # Input messages
    TEXT = "text"
    
    # Liaison messages
    INTENT_EXTRACTED = "intent_extracted"
    VOICE_TRANSCRIBED = "voice_transcribed"
    SENTIMENT_ANALYZED = "sentiment_analyzed"
    
    # Strategist messages
    BUSINESS_VALIDATION = "business_validation"
    INVENTORY_CHECK = "inventory_check"
    CREDIT_SCORING = "credit_scoring"
    PRICING_CALCULATION = "pricing_calculation"
    ORDER_CREATED = "order_created"
    PAYMENT_PROCESSED = "payment_processed"
    
    # Auditor messages
    LEDGER_ENTRY = "ledger_entry"
    COMPLIANCE_CHECK = "compliance_check"
    INVOICE_GENERATED = "invoice_generated"
    GST_VALIDATION = "gst_validation"
    
    # System messages
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"
    HEARTBEAT = "heartbeat"


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    """
    Canonical AgentMessage schema
    All agent communication must use this format
    """
    
    # Core identification
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="Tenant ID for multi-tenancy")
    source_agent: AgentType = Field(..., description="Agent that created this message")
    target_agent: Optional[AgentType] = Field(None, description="Target agent (if specific)")
    
    # Message content
    message_type: MessageType = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific data")
    
    # Metadata
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="Message priority")
    requires_confirmation: bool = Field(default=False, description="Requires WhatsApp confirmation")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Message expiration time")
    
    # Tracing and debugging
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for conversation flow")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Validation
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        """Validate tenant ID format"""
        if not v or len(v) < 3:
            raise ValueError("tenant_id must be at least 3 characters")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence score"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v, values):
        """Validate expiration time"""
        if v and 'timestamp' in values:
            if v <= values['timestamp']:
                raise ValueError("expires_at must be after timestamp")
        return v
    
    @validator('correlation_id')
    def validate_correlation_id(cls, v):
        """Validate correlation ID"""
        if v and len(v) < 10:
            raise ValueError("correlation_id must be at least 10 characters")
        return v
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return self.json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(**data)
    
    def create_response(
        self,
        source_agent: AgentType,
        message_type: MessageType,
        payload: Dict[str, Any],
        confidence: float = 1.0
    ) -> 'AgentMessage':
        """
        Create a response message to this message
        Maintains correlation and parent message ID
        """
        return AgentMessage(
            tenant_id=self.tenant_id,
            source_agent=source_agent,
            target_agent=self.source_agent,
            message_type=message_type,
            payload=payload,
            confidence=confidence,
            correlation_id=self.correlation_id or self.message_id,
            parent_message_id=self.message_id
        )
    
    def create_error_response(
        self,
        source_agent: AgentType,
        error_message: str,
        error_code: Optional[str] = None
    ) -> 'AgentMessage':
        """
        Create an error response message
        """
        payload = {
            "error": error_message,
            "error_code": error_code,
            "original_message_type": self.message_type.value
        }
        
        return self.create_response(
            source_agent=source_agent,
            message_type=MessageType.ERROR,
            payload=payload,
            confidence=0.0
        )
    
    def create_acknowledgment(
        self,
        source_agent: AgentType,
        status: str = "received"
    ) -> 'AgentMessage':
        """
        Create an acknowledgment message
        """
        payload = {
            "status": status,
            "original_message_type": self.message_type.value
        }
        
        return self.create_response(
            source_agent=source_agent,
            message_type=MessageType.ACKNOWLEDGMENT,
            payload=payload,
            confidence=1.0
        )


class MessageValidator:
    """
    Validates AgentMessage objects
    Ensures message integrity and compliance
    """
    
    @staticmethod
    def validate_message(message: AgentMessage) -> tuple[bool, Optional[str]]:
        """
        Validate message
        Returns (is_valid, error_message)
        """
        try:
            # Check expiration
            if message.is_expired():
                return False, "Message has expired"
            
            # Check retry count
            if message.retry_count > 5:
                return False, "Message retry count exceeded"
            
            # Validate payload based on message type
            if not MessageValidator._validate_payload(message):
                return False, "Invalid payload for message type"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def _validate_payload(message: AgentMessage) -> bool:
        """
        Validate payload based on message type
        """
        # Define required fields for each message type
        required_fields = {
            MessageType.TEXT: ["text"],
            MessageType.INTENT_EXTRACTED: ["intent", "entities"],
            MessageType.VOICE_TRANSCRIBED: ["transcription", "language"],
            MessageType.SENTIMENT_ANALYZED: ["sentiment", "score"],
            MessageType.BUSINESS_VALIDATION: ["is_valid", "reason"],
            MessageType.INVENTORY_CHECK: ["item_id", "available"],
            MessageType.CREDIT_SCORING: ["customer_id", "score", "limit"],
            MessageType.PRICING_CALCULATION: ["item_id", "price"],
            MessageType.ORDER_CREATED: ["order_id", "items"],
            MessageType.PAYMENT_PROCESSED: ["payment_id", "amount", "status"],
            MessageType.LEDGER_ENTRY: ["entry_type", "amount"],
            MessageType.COMPLIANCE_CHECK: ["is_compliant", "issues"],
            MessageType.INVOICE_GENERATED: ["invoice_id", "amount"],
            MessageType.GST_VALIDATION: ["is_valid", "gst_number"],
            MessageType.ERROR: ["error"],
        }
        
        # Check if message type has required fields
        if message.message_type in required_fields:
            required = required_fields[message.message_type]
            for field in required:
                if field not in message.payload:
                    return False
        
        return True
    
    @staticmethod
    def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize payload to prevent injection attacks
        """
        sanitized = {}
        
        for key, value in payload.items():
            # Sanitize string values
            if isinstance(value, str):
                # Remove potential script tags
                sanitized[key] = value.replace("<script", "").replace("</script>", "")
            # Recursively sanitize nested dictionaries
            elif isinstance(value, dict):
                sanitized[key] = MessageValidator.sanitize_payload(value)
            # Keep other types as-is
            else:
                sanitized[key] = value
        
        return sanitized


class MessageSerializer:
    """
    Serializes and deserializes AgentMessage objects
    Handles encryption and compression
    """
    
    @staticmethod
    def serialize(message: AgentMessage, encrypt: bool = False) -> str:
        """
        Serialize message to JSON string
        Optionally encrypt the message
        """
        json_str = message.to_json()
        
        if encrypt:
            # TODO: Implement encryption
            pass
        
        return json_str
    
    @staticmethod
    def deserialize(json_str: str, decrypt: bool = False) -> AgentMessage:
        """
        Deserialize JSON string to AgentMessage
        Optionally decrypt the message
        """
        if decrypt:
            # TODO: Implement decryption
            pass
        
        return AgentMessage.from_json(json_str)
    
    @staticmethod
    def serialize_for_stream(message: AgentMessage) -> Dict[str, str]:
        """
        Serialize message for Redis Stream
        Returns dictionary suitable for XADD
        """
        # Convert to JSON
        json_str = message.to_json()
        
        # Split into chunks if too large (Redis max value size is 512MB)
        # For now, we'll keep it simple
        return {
            "message": json_str,
            "message_id": message.message_id,
            "source_agent": message.source_agent.value,
            "message_type": message.message_type.value,
            "tenant_id": message.tenant_id
        }
    
    @staticmethod
    def deserialize_from_stream(data: Dict[str, str]) -> AgentMessage:
        """
        Deserialize message from Redis Stream data
        """
        json_str = data.get("message", "{}")
        return AgentMessage.from_json(json_str)


class MessageTracer:
    """
    Traces message flow through the system
    Useful for debugging and monitoring
    """
    
    def __init__(self):
        self.trace_log: List[Dict[str, Any]] = []
    
    def trace_message(
        self,
        message: AgentMessage,
        action: str,
        agent: AgentType,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log message trace
        """
        trace_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message.message_id,
            "correlation_id": message.correlation_id,
            "action": action,
            "agent": agent.value,
            "message_type": message.message_type.value,
            "tenant_id": message.tenant_id,
            "additional_info": additional_info or {}
        }
        
        self.trace_log.append(trace_entry)
    
    def get_trace_history(
        self,
        message_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trace history for message
        """
        if message_id:
            return [t for t in self.trace_log if t["message_id"] == message_id]
        elif correlation_id:
            return [t for t in self.trace_log if t["correlation_id"] == correlation_id]
        else:
            return self.trace_log


# Global tracer instance
message_tracer = MessageTracer()