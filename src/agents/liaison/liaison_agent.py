"""
Liaison Agent
Handles intent extraction from WhatsApp text/voice messages
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from src.agents.common.base_agent import BaseAgent
from src.agents.messages.message_schema import (
    AgentMessage, AgentType, MessageType, MessagePriority
)
from src.agents.messages.message_audit import AuditAction

logger = logging.getLogger(__name__)


class LiaisonAgent(BaseAgent):
    """
    Liaison Agent - Extracts intent from WhatsApp messages
    Handles text and voice input, sentiment analysis
    """
    
    def __init__(self, tenant_id: str):
        super().__init__(AgentType.LIAISON, tenant_id)
        
        # Liaison-specific configuration
        self.supported_intents = [
            "order",
            "inquiry",
            "payment",
            "credit",
            "complaint",
            "support"
        ]
        
        logger.info(f"Liaison agent initialized for tenant {tenant_id}")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming message
        Extract intent and entities from message
        """
        try:
            # Handle different message types
            if message.message_type == MessageType.VOICE_TRANSCRIBED:
                return await self._process_voice_message(message)
            elif message.message_type == MessageType.INTENT_EXTRACTED:
                return await self._process_intent_message(message)
            else:
                # Handle generic text message
                return await self._process_text_message(message)
                
        except Exception as e:
            logger.error(f"Error processing message in Liaison agent: {e}")
            return message.create_error_response(
                source_agent=self.agent_type,
                error_message=str(e),
                error_code="PROCESSING_ERROR"
            )
    
    async def _process_text_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process text message
        Extract intent and entities
        """
        try:
            # Get text from payload
            text = message.payload.get("text", "")
            
            if not text:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message="No text provided",
                    error_code="NO_TEXT"
                )
            
            # Extract intent
            intent_result = await self._extract_intent(text)
            
            # Extract entities
            entities = await self._extract_entities(text, intent_result["intent"])
            
            # Analyze sentiment
            sentiment_result = await self._analyze_sentiment(text)
            
            # Create response message with target_agent=STRATEGIST for pipeline forwarding
            response = message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.INTENT_EXTRACTED,
                payload={
                    "intent": intent_result["intent"],
                    "confidence": intent_result["confidence"],
                    "entities": entities,
                    "sentiment": sentiment_result["sentiment"],
                    "sentiment_score": sentiment_result["score"],
                    "original_text": text,
                    "language": intent_result.get("language", "en")
                },
                confidence=intent_result["confidence"]
            )
            response.target_agent = AgentType.STRATEGIST  # forward to strategist
            
            # Set priority based on sentiment
            if sentiment_result["sentiment"] == "negative":
                response.priority = MessagePriority.HIGH
            
            logger.info(f"Extracted intent: {intent_result['intent']} with confidence {intent_result['confidence']} — forwarding to strategist")
            return response
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            raise
    
    async def _process_voice_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process voice message
        Handle transcription and intent extraction
        """
        try:
            # Get transcription from payload
            transcription = message.payload.get("transcription", "")
            language = message.payload.get("language", "en")
            
            if not transcription:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message="No transcription provided",
                    error_code="NO_TRANSCRIPTION"
                )
            
            # Extract intent from transcription
            intent_result = await self._extract_intent(transcription)
            
            # Extract entities
            entities = await self._extract_entities(transcription, intent_result["intent"])
            
            # Analyze sentiment
            sentiment_result = await self._analyze_sentiment(transcription)
            
            # Create response message
            response = message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.INTENT_EXTRACTED,
                payload={
                    "intent": intent_result["intent"],
                    "confidence": intent_result["confidence"],
                    "entities": entities,
                    "sentiment": sentiment_result["sentiment"],
                    "sentiment_score": sentiment_result["score"],
                    "original_text": transcription,
                    "language": language,
                    "is_voice": True
                },
                confidence=intent_result["confidence"]
            )
            
            logger.info(f"Processed voice message with intent: {intent_result['intent']}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            raise
    
    async def _process_intent_message(self, message: AgentMessage) -> AgentMessage:
        """
        Process already extracted intent
        Forward to Strategist for business logic
        """
        try:
            # Create business validation message for Strategist
            business_message = AgentMessage(
                tenant_id=self.tenant_id,
                source_agent=self.agent_type,
                target_agent=AgentType.STRATEGIST,
                message_type=MessageType.BUSINESS_VALIDATION,
                payload={
                    "intent": message.payload.get("intent"),
                    "entities": message.payload.get("entities", {}),
                    "confidence": message.payload.get("confidence", 0.0),
                    "sentiment": message.payload.get("sentiment"),
                    "original_text": message.payload.get("original_text", ""),
                    "is_valid": True,
                    "reason": "Intent extracted successfully"
                },
                confidence=message.payload.get("confidence", 0.0)
            )
            
            # Send to Strategist
            await self.send_message(business_message)
            
            # Acknowledge receipt
            return message.create_acknowledgment(
                source_agent=self.agent_type,
                status="forwarded_to_strategist"
            )
            
        except Exception as e:
            logger.error(f"Error processing intent message: {e}")
            raise
    
    async def _extract_intent(self, text: str) -> Dict[str, Any]:
        """
        Extract intent from text
        Returns intent and confidence score
        """
        # TODO: Implement actual NLP intent extraction
        # For now, use simple keyword matching
        
        text_lower = text.lower()
        
        # Define intent keywords
        intent_keywords = {
            "order": ["order", "buy", "purchase", "want", "need", "get"],
            "inquiry": ["what", "how", "where", "when", "price", "cost"],
            "payment": ["pay", "payment", "due", "amount", "bill"],
            "credit": ["credit", "udhaar", "loan", "borrow", "advance"],
            "complaint": ["complaint", "issue", "problem", "wrong", "bad"],
            "support": ["help", "support", "assist", "question"]
        }
        
        # Find best matching intent
        best_intent = "inquiry"
        best_score = 0.0
        
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Calculate confidence
        confidence = min(best_score / 3.0, 1.0)  # Normalize to 0-1
        
        # Detect language (simple check)
        is_hindi = any(char in text for char in "अआइईउऊऋऌएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह")
        language = "hi" if is_hindi else "en"
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "language": language
        }
    
    async def _extract_entities(
        self,
        text: str,
        intent: str
    ) -> Dict[str, Any]:
        """
        Extract entities from text based on intent
        Returns extracted entities
        """
        # TODO: Implement actual NLP entity extraction
        # For now, use simple pattern matching
        
        entities = {}
        
        # Extract numbers (quantities, prices)
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]
        
        # Extract product names (simple heuristic)
        words = text.split()
        entities["potential_products"] = [word for word in words if len(word) > 3]
        
        # Intent-specific entity extraction
        if intent == "order":
            # Extract order details
            entities["order_type"] = "new"
        elif intent == "payment":
            # Extract payment amount
            if numbers:
                entities["amount"] = max(numbers)
        elif intent == "credit":
            # Extract credit amount
            if numbers:
                entities["credit_amount"] = max(numbers)
        
        return entities
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        Returns sentiment and score
        """
        # TODO: Implement actual sentiment analysis
        # For now, use simple keyword matching
        
        text_lower = text.lower()
        
        # Positive keywords
        positive_keywords = [
            "good", "great", "excellent", "happy", "satisfied",
            "thanks", "thank you", "appreciate", "love", "like"
        ]
        
        # Negative keywords
        negative_keywords = [
            "bad", "terrible", "awful", "hate", "dislike",
            "angry", "frustrated", "disappointed", "problem", "issue"
        ]
        
        # Count positive and negative words
        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
        
        # Calculate sentiment score
        total_words = len(text.split())
        if total_words == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / total_words
        
        # Determine sentiment
        if score > 0.1:
            sentiment = "positive"
        elif score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": score
        }
    
    async def handle_whatsapp_webhook(self, webhook_data: Dict[str, Any]) -> Optional[AgentMessage]:
        """
        Handle incoming WhatsApp webhook
        Create message from webhook data
        """
        try:
            # Extract message data from webhook
            message_data = webhook_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
            
            # Get phone number
            phone_number = message_data.get("metadata", {}).get("phone_number_id", "")
            
            # Get message
            messages = message_data.get("messages", [])
            if not messages:
                logger.warning("No messages in webhook")
                return None
            
            message = messages[0]
            
            # Check if text message
            if message.get("type") == "text":
                text = message.get("text", {}).get("body", "")
                
                # Create message for processing
                agent_message = AgentMessage(
                    tenant_id=self.tenant_id,
                    source_agent=AgentType.LIAISON,
                    message_type=MessageType.INTENT_EXTRACTED,
                    payload={
                        "text": text,
                        "phone_number": phone_number,
                        "message_id": message.get("id"),
                        "timestamp": message.get("timestamp")
                    }
                )
                
                return agent_message
            
            # Check if voice message
            elif message.get("type") == "audio":
                audio_id = message.get("audio", {}).get("id", "")
                
                # TODO: Download and transcribe audio
                # For now, create placeholder message
                agent_message = AgentMessage(
                    tenant_id=self.tenant_id,
                    source_agent=AgentType.LIAISON,
                    message_type=MessageType.VOICE_TRANSCRIBED,
                    payload={
                        "audio_id": audio_id,
                        "phone_number": phone_number,
                        "message_id": message.get("id"),
                        "timestamp": message.get("timestamp"),
                        "transcription": "",  # Will be filled after transcription
                        "language": "en"
                    }
                )
                
                return agent_message
            
            else:
                logger.warning(f"Unsupported message type: {message.get('type')}")
                return None
                
        except Exception as e:
            logger.error(f"Error handling WhatsApp webhook: {e}")
            return None