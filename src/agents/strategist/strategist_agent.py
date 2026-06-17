"""
Strategist Agent
Handles business logic validation and execution
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


class StrategistAgent(BaseAgent):
    """
    Strategist Agent - Validates and executes business logic
    Handles inventory, credit scoring, pricing, order creation
    """
    
    def __init__(self, tenant_id: str):
        super().__init__(AgentType.STRATEGIST, tenant_id)
        
        # Strategist-specific configuration
        self.supported_intents = [
            "order",
            "inquiry",
            "payment",
            "credit",
            "complaint",
            "support"
        ]
        
        logger.info(f"Strategist agent initialized for tenant {tenant_id}")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming message
        Execute business logic based on intent
        """
        try:
            # Handle different message types
            if message.message_type == MessageType.BUSINESS_VALIDATION:
                return await self._process_business_validation(message)
            elif message.message_type == MessageType.INVENTORY_CHECK:
                return await self._process_inventory_check(message)
            elif message.message_type == MessageType.CREDIT_SCORING:
                return await self._process_credit_scoring(message)
            elif message.message_type == MessageType.PRICING_CALCULATION:
                return await self._process_pricing_calculation(message)
            elif message.message_type == MessageType.ORDER_CREATED:
                return await self._process_order_created(message)
            elif message.message_type == MessageType.PAYMENT_PROCESSED:
                return await self._process_payment_processed(message)
            else:
                # Handle unknown message type
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Unknown message type: {message.message_type.value}",
                    error_code="UNKNOWN_MESSAGE_TYPE"
                )
                
        except Exception as e:
            logger.error(f"Error processing message in Strategist agent: {e}")
            return message.create_error_response(
                source_agent=self.agent_type,
                error_message=str(e),
                error_code="PROCESSING_ERROR"
            )
    
    async def _process_business_validation(self, message: AgentMessage) -> AgentMessage:
        """
        Process business validation request
        Validate intent and route to appropriate handler
        """
        try:
            # Get intent from payload
            intent = message.payload.get("intent")
            entities = message.payload.get("entities", {})
            confidence = message.payload.get("confidence", 0.0)
            
            if not intent:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message="No intent provided",
                    error_code="NO_INTENT"
                )
            
            # Validate intent
            if intent not in self.supported_intents:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Unsupported intent: {intent}",
                    error_code="UNSUPPORTED_INTENT"
                )
            
            # Check confidence threshold
            if confidence < 0.5:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Low confidence: {confidence}",
                    error_code="LOW_CONFIDENCE"
                )
            
            # Route to appropriate handler
            if intent == "order":
                return await self._handle_order_intent(message, entities)
            elif intent == "inquiry":
                return await self._handle_inquiry_intent(message, entities)
            elif intent == "payment":
                return await self._handle_payment_intent(message, entities)
            elif intent == "credit":
                return await self._handle_credit_intent(message, entities)
            elif intent == "complaint":
                return await self._handle_complaint_intent(message, entities)
            elif intent == "support":
                return await self._handle_support_intent(message, entities)
            else:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Unhandled intent: {intent}",
                    error_code="UNHANDLED_INTENT"
                )
                
        except Exception as e:
            logger.error(f"Error processing business validation: {e}")
            raise
    
    async def _handle_order_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle order intent
        Check inventory and create order
        """
        try:
            # TODO: Implement actual order processing
            # For now, create placeholder response
            
            # Check inventory
            inventory_check = await self._check_inventory(entities)
            
            if not inventory_check["available"]:
                return message.create_response(
                    source_agent=self.agent_type,
                    message_type=MessageType.INVENTORY_CHECK,
                    payload={
                        "is_valid": False,
                        "reason": "Insufficient inventory",
                        "available_items": inventory_check["available_items"],
                        "requested_items": entities
                    },
                    confidence=0.0
                )
            
            # Create order
            order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create order message for Auditor
            order_message = AgentMessage(
                tenant_id=self.tenant_id,
                source_agent=self.agent_type,
                target_agent=AgentType.AUDITOR,
                message_type=MessageType.ORDER_CREATED,
                payload={
                    "order_id": order_id,
                    "items": entities,
                    "total_amount": inventory_check["total_amount"],
                    "customer_id": entities.get("customer_id", "unknown"),
                    "status": "pending"
                },
                confidence=1.0
            )
            
            # Send to Auditor
            await self.send_message(order_message)
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.ORDER_CREATED,
                payload={
                    "is_valid": True,
                    "reason": "Order created successfully",
                    "order_id": order_id,
                    "total_amount": inventory_check["total_amount"],
                    "estimated_delivery": "2-3 business days"
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error handling order intent: {e}")
            raise
    
    async def _handle_inquiry_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle inquiry intent
        Provide information about products/services
        """
        try:
            # TODO: Implement actual inquiry handling
            # For now, create placeholder response
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.BUSINESS_VALIDATION,
                payload={
                    "is_valid": True,
                    "reason": "Inquiry received",
                    "response": "Thank you for your inquiry. Our team will get back to you shortly.",
                    "inquiry_type": entities.get("inquiry_type", "general")
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error handling inquiry intent: {e}")
            raise
    
    async def _handle_payment_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle payment intent
        Process payment and update ledger
        """
        try:
            # TODO: Implement actual payment processing
            # For now, create placeholder response
            
            amount = entities.get("amount", 0)
            
            # Create payment message for Auditor
            payment_message = AgentMessage(
                tenant_id=self.tenant_id,
                source_agent=self.agent_type,
                target_agent=AgentType.AUDITOR,
                message_type=MessageType.PAYMENT_PROCESSED,
                payload={
                    "payment_id": f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "amount": amount,
                    "customer_id": entities.get("customer_id", "unknown"),
                    "payment_method": entities.get("payment_method", "cash"),
                    "status": "completed"
                },
                confidence=1.0
            )
            
            # Send to Auditor
            await self.send_message(payment_message)
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.PAYMENT_PROCESSED,
                payload={
                    "is_valid": True,
                    "reason": "Payment processed successfully",
                    "amount": amount,
                    "payment_id": payment_message.payload["payment_id"]
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error handling payment intent: {e}")
            raise
    
    async def _handle_credit_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle credit intent
        Check credit score and process credit request
        """
        try:
            # TODO: Implement actual credit processing
            # For now, create placeholder response
            
            customer_id = entities.get("customer_id", "unknown")
            credit_amount = entities.get("credit_amount", 0)
            
            # Check credit score
            credit_score = await self._calculate_credit_score(customer_id)
            
            # Determine if credit is approved
            is_approved = credit_score["score"] >= 50 and credit_amount <= credit_score["limit"]
            
            if is_approved:
                # Create credit entry message for Auditor
                credit_message = AgentMessage(
                    tenant_id=self.tenant_id,
                    source_agent=self.agent_type,
                    target_agent=AgentType.AUDITOR,
                    message_type=MessageType.CREDIT_SCORING,
                    payload={
                        "credit_id": f"CRD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        "customer_id": customer_id,
                        "amount": credit_amount,
                        "score": credit_score["score"],
                        "limit": credit_score["limit"],
                        "status": "approved"
                    },
                    confidence=credit_score["score"] / 100.0
                )
                
                # Send to Auditor
                await self.send_message(credit_message)
                
                # Return response
                return message.create_response(
                    source_agent=self.agent_type,
                    message_type=MessageType.CREDIT_SCORING,
                    payload={
                        "is_valid": True,
                        "reason": "Credit approved",
                        "credit_id": credit_message.payload["credit_id"],
                        "amount": credit_amount,
                        "score": credit_score["score"],
                        "limit": credit_score["limit"]
                    },
                    confidence=credit_score["score"] / 100.0
                )
            else:
                # Credit denied
                return message.create_response(
                    source_agent=self.agent_type,
                    message_type=MessageType.CREDIT_SCORING,
                    payload={
                        "is_valid": False,
                        "reason": "Credit denied",
                        "score": credit_score["score"],
                        "limit": credit_score["limit"],
                        "requested_amount": credit_amount
                    },
                    confidence=0.0
                )
            
        except Exception as e:
            logger.error(f"Error handling credit intent: {e}")
            raise
    
    async def _handle_complaint_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle complaint intent
        Log complaint and create support ticket
        """
        try:
            # TODO: Implement actual complaint handling
            # For now, create placeholder response
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.BUSINESS_VALIDATION,
                payload={
                    "is_valid": True,
                    "reason": "Complaint received",
                    "ticket_id": f"TCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "status": "open",
                    "response": "Thank you for your feedback. We will address your concern shortly."
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error handling complaint intent: {e}")
            raise
    
    async def _handle_support_intent(self, message: AgentMessage, entities: Dict[str, Any]) -> AgentMessage:
        """
        Handle support intent
        Provide support and assistance
        """
        try:
            # TODO: Implement actual support handling
            # For now, create placeholder response
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.BUSINESS_VALIDATION,
                payload={
                    "is_valid": True,
                    "reason": "Support request received",
                    "ticket_id": f"TCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "status": "open",
                    "response": "Our support team will assist you shortly."
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error handling support intent: {e}")
            raise
    
    async def _process_inventory_check(self, message: AgentMessage) -> AgentMessage:
        """
        Process inventory check request
        """
        try:
            entities = message.payload.get("entities", {})
            
            # Check inventory
            inventory_check = await self._check_inventory(entities)
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.INVENTORY_CHECK,
                payload={
                    "available": inventory_check["available"],
                    "available_items": inventory_check["available_items"],
                    "total_amount": inventory_check["total_amount"]
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing inventory check: {e}")
            raise
    
    async def _process_credit_scoring(self, message: AgentMessage) -> AgentMessage:
        """
        Process credit scoring request
        """
        try:
            customer_id = message.payload.get("customer_id", "unknown")
            
            # Calculate credit score
            credit_score = await self._calculate_credit_score(customer_id)
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.CREDIT_SCORING,
                payload={
                    "score": credit_score["score"],
                    "limit": credit_score["limit"],
                    "history": credit_score["history"]
                },
                confidence=credit_score["score"] / 100.0
            )
            
        except Exception as e:
            logger.error(f"Error processing credit scoring: {e}")
            raise
    
    async def _process_pricing_calculation(self, message: AgentMessage) -> AgentMessage:
        """
        Process pricing calculation request
        """
        try:
            item_id = message.payload.get("item_id")
            quantity = message.payload.get("quantity", 1)
            
            # Calculate price
            price = await self._calculate_price(item_id, quantity)
            
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.PRICING_CALCULATION,
                payload={
                    "item_id": item_id,
                    "quantity": quantity,
                    "unit_price": price["unit_price"],
                    "total_price": price["total_price"],
                    "discount": price.get("discount", 0)
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing pricing calculation: {e}")
            raise
    
    async def _process_order_created(self, message: AgentMessage) -> AgentMessage:
        """
        Process order created notification
        """
        try:
            # Log order creation
            logger.info(f"Order created: {message.payload.get('order_id')}")
            
            # Acknowledge order creation
            return message.create_acknowledgment(
                source_agent=self.agent_type,
                status="order_created_acknowledged"
            )
            
        except Exception as e:
            logger.error(f"Error processing order created: {e}")
            raise
    
    async def _process_payment_processed(self, message: AgentMessage) -> AgentMessage:
        """
        Process payment processed notification
        """
        try:
            # Log payment processing
            logger.info(f"Payment processed: {message.payload.get('payment_id')}")
            
            # Acknowledge payment processing
            return message.create_acknowledgment(
                source_agent=self.agent_type,
                status="payment_processed_acknowledged"
            )
            
        except Exception as e:
            logger.error(f"Error processing payment processed: {e}")
            raise
    
    async def _check_inventory(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check inventory availability
        Returns inventory status
        """
        # TODO: Implement actual inventory check
        # For now, return placeholder data
        
        return {
            "available": True,
            "available_items": entities,
            "total_amount": 1000.0
        }
    
    async def _calculate_credit_score(self, customer_id: str) -> Dict[str, Any]:
        """
        Calculate credit score for customer
        Returns credit score and limit
        """
        # TODO: Implement actual credit scoring
        # For now, return placeholder data
        
        return {
            "score": 75,
            "limit": 50000.0,
            "history": {
                "total_orders": 10,
                "total_amount": 25000.0,
                "on_time_payments": 9,
                "late_payments": 1
            }
        }
    
    async def _calculate_price(self, item_id: str, quantity: int) -> Dict[str, Any]:
        """
        Calculate price for item
        Returns pricing details
        """
        # TODO: Implement actual price calculation
        # For now, return placeholder data
        
        unit_price = 100.0
        total_price = unit_price * quantity
        
        return {
            "unit_price": unit_price,
            "total_price": total_price,
            "discount": 0.0
        }