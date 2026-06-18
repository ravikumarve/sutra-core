"""
Auditor Agent
Handles immutable ledger and compliance
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


class AuditorAgent(BaseAgent):
    """
    Auditor Agent - Maintains immutable ledger and compliance
    Handles PDF generation, GST validation, ledger entries
    """
    
    def __init__(self, tenant_id: str):
        super().__init__(AgentType.AUDITOR, tenant_id)
        
        # Auditor-specific configuration
        self.ledger_entries: Dict[str, Any] = {}
        self.compliance_rules = {
            "gst_required": True,
            "invoice_required": True,
            "ledger_required": True
        }
        
        logger.info(f"Auditor agent initialized for tenant {tenant_id}")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming message
        Handle ledger entries, compliance checks, invoice generation
        """
        try:
            # Handle different message types
            if message.message_type == MessageType.ORDER_CREATED:
                return await self._process_order_created(message)
            elif message.message_type == MessageType.BUSINESS_VALIDATION:
                return await self._process_business_validation(message)
            elif message.message_type == MessageType.PAYMENT_PROCESSED:
                return await self._process_payment_processed(message)
            elif message.message_type == MessageType.CREDIT_SCORING:
                return await self._process_credit_scoring(message)
            elif message.message_type == MessageType.LEDGER_ENTRY:
                return await self._process_ledger_entry(message)
            elif message.message_type == MessageType.COMPLIANCE_CHECK:
                return await self._process_compliance_check(message)
            elif message.message_type == MessageType.INVOICE_GENERATED:
                return await self._process_invoice_generated(message)
            elif message.message_type == MessageType.GST_VALIDATION:
                return await self._process_gst_validation(message)
            else:
                # Handle unknown message type
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Unknown message type: {message.message_type.value}",
                    error_code="UNKNOWN_MESSAGE_TYPE"
                )
                
        except Exception as e:
            logger.error(f"Error processing message in Auditor agent: {e}")
            return message.create_error_response(
                source_agent=self.agent_type,
                error_message=str(e),
                error_code="PROCESSING_ERROR"
            )
    
    async def _process_business_validation(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process business validation audit
        Log audit trail and respond with confirmation
        """
        try:
            is_valid = message.payload.get("is_valid", False)
            reason = message.payload.get("reason", "No reason provided")

            if is_valid:
                logger.info(f"Business validation passed for tenant {self.tenant_id}: {reason}")
                # Terminal — return None to end the pipeline
                return None
            else:
                return message.create_error_response(
                    source_agent=self.agent_type,
                    error_message=f"Business validation failed: {reason}",
                    error_code="VALIDATION_FAILED"
                )

        except Exception as e:
            logger.error(f"Error processing business validation: {e}")
            raise

    async def _process_order_compliance(
        self,
        order_id: str,
        items: Dict[str, Any],
        total_amount: float,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Process order compliance checks and generate required documents
        
        Args:
            order_id: Order ID
            items: Order items
            total_amount: Total order amount
            customer_id: Customer ID
            
        Returns:
            Dictionary with compliance results
        """
        # Validate compliance
        compliance_check = await self._validate_compliance(
            entry_type="order",
            data={"order_id": order_id, "items": items, "total_amount": total_amount}
        )
        
        # Generate invoice
        invoice_id = await self._generate_invoice(
            order_id=order_id,
            items=items,
            total_amount=total_amount,
            customer_id=customer_id
        )
        
        # Validate GST
        gst_validation = await self._validate_gst(
            customer_id=customer_id,
            amount=total_amount
        )
        
        return {
            "compliance_check": compliance_check,
            "invoice_id": invoice_id,
            "gst_validation": gst_validation
        }

    async def _process_order_created(self, message: AgentMessage) -> AgentMessage:
        """
        Process order created notification
        Create ledger entry and validate compliance
        """
        try:
            # Get order details
            order_id = message.payload.get("order_id")
            items = message.payload.get("items", {})
            total_amount = message.payload.get("total_amount", 0)
            customer_id = message.payload.get("customer_id", "unknown")
            
            # Create ledger entry
            ledger_entry = await self._create_ledger_entry(
                entry_type="order",
                amount=total_amount,
                reference_id=order_id,
                customer_id=customer_id,
                details=items
            )
            
            # Process compliance checks
            compliance_results = await self._process_order_compliance(
                order_id, items, total_amount, customer_id
            )
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.LEDGER_ENTRY,
                payload={
                    "ledger_entry_id": ledger_entry["entry_id"],
                    "compliance_status": compliance_results["compliance_check"]["status"],
                    "compliance_issues": compliance_results["compliance_check"].get("issues", []),
                    "invoice_id": compliance_results["invoice_id"],
                    "gst_valid": compliance_results["gst_validation"]["is_valid"],
                    "gst_number": compliance_results["gst_validation"].get("gst_number", ""),
                    "status": "completed"
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing order created: {e}")
            raise
    
    async def _process_payment_processed(self, message: AgentMessage) -> AgentMessage:
        """
        Process payment processed notification
        Create ledger entry and update balance
        """
        try:
            # Get payment details
            payment_id = message.payload.get("payment_id")
            amount = message.payload.get("amount", 0)
            customer_id = message.payload.get("customer_id", "unknown")
            payment_method = message.payload.get("payment_method", "cash")
            
            # Create ledger entry
            ledger_entry = await self._create_ledger_entry(
                entry_type="payment",
                amount=amount,
                reference_id=payment_id,
                customer_id=customer_id,
                details={"payment_method": payment_method}
            )
            
            # Update customer balance
            balance_update = await self._update_customer_balance(
                customer_id=customer_id,
                amount=amount,
                transaction_type="credit"
            )
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.LEDGER_ENTRY,
                payload={
                    "ledger_entry_id": ledger_entry["entry_id"],
                    "balance": balance_update["balance"],
                    "status": "completed"
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing payment processed: {e}")
            raise
    
    async def _process_approved_credit(
        self,
        credit_id: str,
        amount: float,
        customer_id: str,
        score: float,
        limit: float
    ) -> Dict[str, Any]:
        """
        Process approved credit transaction
        
        Args:
            credit_id: Credit ID
            amount: Credit amount
            customer_id: Customer ID
            score: Credit score
            limit: Credit limit
            
        Returns:
            Dictionary with ledger entry and balance update
        """
        # Create ledger entry for credit
        ledger_entry = await self._create_ledger_entry(
            entry_type="credit",
            amount=amount,
            reference_id=credit_id,
            customer_id=customer_id,
            details={
                "score": score,
                "limit": limit,
                "status": "approved"
            }
        )
        
        # Update customer balance
        balance_update = await self._update_customer_balance(
            customer_id=customer_id,
            amount=amount,
            transaction_type="debit"
        )
        
        return {
            "ledger_entry": ledger_entry,
            "balance_update": balance_update
        }

    async def _process_credit_scoring(self, message: AgentMessage) -> AgentMessage:
        """
        Process credit scoring notification
        Create ledger entry for credit
        """
        try:
            # Get credit details
            credit_id = message.payload.get("credit_id")
            amount = message.payload.get("amount", 0)
            customer_id = message.payload.get("customer_id", "unknown")
            score = message.payload.get("score", 0)
            limit = message.payload.get("limit", 0)
            status = message.payload.get("status", "pending")
            
            if status == "approved":
                # Process approved credit
                credit_results = await self._process_approved_credit(
                    credit_id, amount, customer_id, score, limit
                )
                
                # Return response
                return message.create_response(
                    source_agent=self.agent_type,
                    message_type=MessageType.LEDGER_ENTRY,
                    payload={
                        "ledger_entry_id": credit_results["ledger_entry"]["entry_id"],
                        "balance": credit_results["balance_update"]["balance"],
                        "status": "completed"
                    },
                    confidence=score / 100.0
                )
            else:
                # Credit denied
                return message.create_response(
                    source_agent=self.agent_type,
                    message_type=MessageType.LEDGER_ENTRY,
                    payload={
                        "status": "denied",
                        "reason": "Credit not approved"
                    },
                    confidence=0.0
                )
            
        except Exception as e:
            logger.error(f"Error processing credit scoring: {e}")
            raise
    
    async def _process_ledger_entry(self, message: AgentMessage) -> AgentMessage:
        """
        Process ledger entry request
        """
        try:
            # Get entry details
            entry_type = message.payload.get("entry_type")
            amount = message.payload.get("amount", 0)
            reference_id = message.payload.get("reference_id")
            customer_id = message.payload.get("customer_id", "unknown")
            details = message.payload.get("details", {})
            
            # Create ledger entry
            ledger_entry = await self._create_ledger_entry(
                entry_type=entry_type,
                amount=amount,
                reference_id=reference_id,
                customer_id=customer_id,
                details=details
            )
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.LEDGER_ENTRY,
                payload={
                    "ledger_entry_id": ledger_entry["entry_id"],
                    "entry_type": entry_type,
                    "amount": amount,
                    "timestamp": ledger_entry["timestamp"],
                    "status": "created"
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing ledger entry: {e}")
            raise
    
    async def _process_compliance_check(self, message: AgentMessage) -> AgentMessage:
        """
        Process compliance check request
        """
        try:
            # Get compliance check details
            entry_type = message.payload.get("entry_type")
            data = message.payload.get("data", {})
            
            # Validate compliance
            compliance_check = await self._validate_compliance(
                entry_type=entry_type,
                data=data
            )
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.COMPLIANCE_CHECK,
                payload={
                    "is_compliant": compliance_check["status"] == "compliant",
                    "status": compliance_check["status"],
                    "issues": compliance_check.get("issues", []),
                    "warnings": compliance_check.get("warnings", [])
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing compliance check: {e}")
            raise
    
    async def _process_invoice_generated(self, message: AgentMessage) -> AgentMessage:
        """
        Process invoice generated notification
        """
        try:
            # Get invoice details
            invoice_id = message.payload.get("invoice_id")
            
            # Log invoice generation
            logger.info(f"Invoice generated: {invoice_id}")
            
            # Acknowledge invoice generation
            return message.create_acknowledgment(
                source_agent=self.agent_type,
                status="invoice_generated_acknowledged"
            )
            
        except Exception as e:
            logger.error(f"Error processing invoice generated: {e}")
            raise
    
    async def _process_gst_validation(self, message: AgentMessage) -> AgentMessage:
        """
        Process GST validation request
        """
        try:
            # Get GST validation details
            customer_id = message.payload.get("customer_id", "unknown")
            amount = message.payload.get("amount", 0)
            
            # Validate GST
            gst_validation = await self._validate_gst(
                customer_id=customer_id,
                amount=amount
            )
            
            # Return response
            return message.create_response(
                source_agent=self.agent_type,
                message_type=MessageType.GST_VALIDATION,
                payload={
                    "is_valid": gst_validation["is_valid"],
                    "gst_number": gst_validation.get("gst_number", ""),
                    "gst_amount": gst_validation.get("gst_amount", 0),
                    "status": "validated"
                },
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error processing GST validation: {e}")
            raise
    
    async def _create_ledger_entry(
        self,
        entry_type: str,
        amount: float,
        reference_id: str,
        customer_id: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create ledger entry
        Returns ledger entry details
        """
        # TODO: Implement actual ledger entry creation
        # For now, create placeholder entry
        
        entry_id = f"LED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        ledger_entry = {
            "entry_id": entry_id,
            "entry_type": entry_type,
            "amount": amount,
            "reference_id": reference_id,
            "customer_id": customer_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": self.tenant_id
        }
        
        # Store in ledger
        self.ledger_entries[entry_id] = ledger_entry
        
        logger.info(f"Created ledger entry: {entry_id} ({entry_type}, {amount})")
        
        return ledger_entry
    
    async def _validate_compliance(
        self,
        entry_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate compliance for entry
        Returns compliance status and issues
        """
        # TODO: Implement actual compliance validation
        # For now, return placeholder data
        
        issues = []
        warnings = []
        
        # Check GST requirement
        if self.compliance_rules["gst_required"]:
            gst_number = data.get("gst_number", "")
            if not gst_number:
                issues.append("GST number required")
        
        # Check invoice requirement
        if self.compliance_rules["invoice_required"]:
            invoice_id = data.get("invoice_id", "")
            if not invoice_id:
                issues.append("Invoice ID required")
        
        # Check ledger requirement
        if self.compliance_rules["ledger_required"]:
            ledger_entry_id = data.get("ledger_entry_id", "")
            if not ledger_entry_id:
                issues.append("Ledger entry ID required")
        
        # Determine compliance status
        if issues:
            status = "non_compliant"
        elif warnings:
            status = "compliant_with_warnings"
        else:
            status = "compliant"
        
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings
        }
    
    async def _generate_invoice(
        self,
        order_id: str,
        items: Dict[str, Any],
        total_amount: float,
        customer_id: str
    ) -> str:
        """
        Generate invoice for order
        Returns invoice ID
        """
        # TODO: Implement actual invoice generation with WeasyPrint
        # For now, create placeholder invoice
        
        invoice_id = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Generated invoice: {invoice_id} for order {order_id}")
        
        return invoice_id
    
    async def _validate_gst(
        self,
        customer_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Validate GST for customer
        Returns GST validation result
        """
        # TODO: Implement actual GST validation
        # For now, return placeholder data
        
        # Calculate GST amount (18% standard rate)
        gst_amount = amount * 0.18
        
        return {
            "is_valid": True,
            "gst_number": f"24{customer_id[:9]}A1Z5",  # Placeholder GST number
            "gst_amount": gst_amount,
            "gst_rate": 0.18
        }
    
    async def _update_customer_balance(
        self,
        customer_id: str,
        amount: float,
        transaction_type: str
    ) -> Dict[str, Any]:
        """
        Update customer balance
        Returns updated balance
        """
        # TODO: Implement actual balance update
        # For now, return placeholder data
        
        # Get current balance (placeholder)
        current_balance = 0.0
        
        # Update balance based on transaction type
        if transaction_type == "credit":
            new_balance = current_balance + amount
        elif transaction_type == "debit":
            new_balance = current_balance - amount
        else:
            new_balance = current_balance
        
        return {
            "customer_id": customer_id,
            "previous_balance": current_balance,
            "new_balance": new_balance,
            "transaction_amount": amount,
            "transaction_type": transaction_type
        }
    
    async def get_ledger_summary(self) -> Dict[str, Any]:
        """
        Get ledger summary
        Returns summary of all ledger entries
        """
        # Calculate summary
        total_entries = len(self.ledger_entries)
        total_amount = sum(entry["amount"] for entry in self.ledger_entries.values())
        
        # Group by entry type
        by_type = {}
        for entry in self.ledger_entries.values():
            entry_type = entry["entry_type"]
            if entry_type not in by_type:
                by_type[entry_type] = {"count": 0, "amount": 0.0}
            by_type[entry_type]["count"] += 1
            by_type[entry_type]["amount"] += entry["amount"]
        
        return {
            "total_entries": total_entries,
            "total_amount": total_amount,
            "by_type": by_type,
            "tenant_id": self.tenant_id
        }