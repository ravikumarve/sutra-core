"""
Message Audit Logging
Comprehensive logging for all agent messages for compliance and debugging
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.db.models import MessageAuditLog
from src.db.connection import get_db_session
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_PROCESSED = "message_processed"
    MESSAGE_FAILED = "message_failed"
    MESSAGE_ACKNOWLEDGED = "message_acknowledged"
    MESSAGE_RETRIED = "message_retried"
    MESSAGE_EXPIRED = "message_expired"
    MESSAGE_DELETED = "message_deleted"


class MessageAuditor:
    """
    Audits all agent messages
    Provides comprehensive logging for compliance and debugging
    """
    
    def __init__(self):
        self.enabled = settings.AUDIT_LOGGING_ENABLED
        self.logger = logging.getLogger("message_audit")
    
    async def log_message(
        self,
        action: AuditAction,
        message_id: str,
        tenant_id: str,
        source_agent: str,
        target_agent: Optional[str],
        message_type: str,
        payload: Dict[str, Any],
        status: str = "success",
        error_message: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Optional[MessageAuditLog]:
        """
        Log message to audit database
        """
        if not self.enabled:
            return None
        
        try:
            async with get_db_session() as session:
                # Create audit log entry
                audit_log = MessageAuditLog(
                    message_id=message_id,
                    tenant_id=tenant_id,
                    action=action.value,
                    source_agent=source_agent,
                    target_agent=target_agent,
                    message_type=message_type,
                    payload=payload,
                    status=status,
                    error_message=error_message,
                    additional_info=additional_info or {},
                    timestamp=datetime.utcnow()
                )
                
                session.add(audit_log)
                await session.commit()
                await session.refresh(audit_log)
                
                # Also log to file for immediate visibility
                self._log_to_file(
                    action=action.value,
                    message_id=message_id,
                    tenant_id=tenant_id,
                    source_agent=source_agent,
                    target_agent=target_agent,
                    message_type=message_type,
                    status=status,
                    error_message=error_message
                )
                
                logger.debug(f"Audit log created: {message_id}")
                return audit_log
                
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None
    
    def _log_to_file(
        self,
        action: str,
        message_id: str,
        tenant_id: str,
        source_agent: str,
        target_agent: Optional[str],
        message_type: str,
        status: str,
        error_message: Optional[str]
    ) -> None:
        """
        Log to file for immediate visibility
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "message_id": message_id,
            "tenant_id": tenant_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "message_type": message_type,
            "status": status,
            "error_message": error_message
        }
        
        self.logger.info(json.dumps(log_entry))
    
    async def get_message_history(
        self,
        message_id: str,
        tenant_id: str
    ) -> List[MessageAuditLog]:
        """
        Get complete message history
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MessageAuditLog)
                    .where(
                        and_(
                            MessageAuditLog.message_id == message_id,
                            MessageAuditLog.tenant_id == tenant_id
                        )
                    )
                    .order_by(MessageAuditLog.timestamp)
                )
                
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []
    
    async def get_tenant_message_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        message_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MessageAuditLog]:
        """
        Get message logs for tenant with filtering
        """
        try:
            async with get_db_session() as session:
                query = select(MessageAuditLog).where(
                    MessageAuditLog.tenant_id == tenant_id
                )
                
                # Apply filters
                if start_date:
                    query = query.where(MessageAuditLog.timestamp >= start_date)
                
                if end_date:
                    query = query.where(MessageAuditLog.timestamp <= end_date)
                
                if message_type:
                    query = query.where(MessageAuditLog.message_type == message_type)
                
                if status:
                    query = query.where(MessageAuditLog.status == status)
                
                # Order and paginate
                query = query.order_by(MessageAuditLog.timestamp.desc())
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get tenant message logs: {e}")
            return []
    
    async def get_message_statistics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get message statistics for tenant
        """
        try:
            async with get_db_session() as session:
                query = select(MessageAuditLog).where(
                    MessageAuditLog.tenant_id == tenant_id
                )
                
                if start_date:
                    query = query.where(MessageAuditLog.timestamp >= start_date)
                
                if end_date:
                    query = query.where(MessageAuditLog.timestamp <= end_date)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                # Calculate statistics
                stats = {
                    "total_messages": len(logs),
                    "successful_messages": len([l for l in logs if l.status == "success"]),
                    "failed_messages": len([l for l in logs if l.status == "failed"]),
                    "by_message_type": {},
                    "by_agent": {},
                    "by_action": {}
                }
                
                for log in logs:
                    # Count by message type
                    if log.message_type not in stats["by_message_type"]:
                        stats["by_message_type"][log.message_type] = 0
                    stats["by_message_type"][log.message_type] += 1
                    
                    # Count by agent
                    if log.source_agent not in stats["by_agent"]:
                        stats["by_agent"][log.source_agent] = 0
                    stats["by_agent"][log.source_agent] += 1
                    
                    # Count by action
                    if log.action not in stats["by_action"]:
                        stats["by_action"][log.action] = 0
                    stats["by_action"][log.action] += 1
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get message statistics: {e}")
            return {}
    
    async def get_failed_messages(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> List[MessageAuditLog]:
        """
        Get failed messages for tenant
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MessageAuditLog)
                    .where(
                        and_(
                            MessageAuditLog.tenant_id == tenant_id,
                            MessageAuditLog.status == "failed"
                        )
                    )
                    .order_by(MessageAuditLog.timestamp.desc())
                    .limit(limit)
                )
                
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get failed messages: {e}")
            return []
    
    async def cleanup_old_logs(
        self,
        retention_days: int = 30
    ) -> int:
        """
        Cleanup old audit logs
        Returns number of logs deleted
        """
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                result = await session.execute(
                    select(MessageAuditLog)
                    .where(MessageAuditLog.timestamp < cutoff_date)
                )
                
                old_logs = result.scalars().all()
                
                for log in old_logs:
                    await session.delete(log)
                
                await session.commit()
                
                logger.info(f"Cleaned up {len(old_logs)} old audit logs")
                return len(old_logs)
                
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    async def export_logs(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> str:
        """
        Export logs for tenant
        Returns exported data as string
        """
        try:
            logs = await self.get_tenant_message_logs(
                tenant_id=tenant_id,
                limit=10000,  # Large limit for export
                start_date=start_date,
                end_date=end_date
            )
            
            if format == "json":
                return json.dumps([log.to_dict() for log in logs], indent=2)
            elif format == "csv":
                # Simple CSV export
                import csv
                import io
                
                output = io.StringIO()
                if logs:
                    writer = csv.DictWriter(output, fieldnames=logs[0].to_dict().keys())
                    writer.writeheader()
                    for log in logs:
                        writer.writerow(log.to_dict())
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return ""


class MessageMetrics:
    """
    Tracks message metrics for monitoring
    """
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "processing_time": [],
            "by_message_type": {},
            "by_agent": {}
        }
    
    def increment_metric(self, metric_name: str, value: int = 1) -> None:
        """
        Increment metric counter
        """
        if metric_name not in self._metrics:
            self._metrics[metric_name] = 0
        self._metrics[metric_name] += value
    
    def record_processing_time(self, time_ms: float) -> None:
        """
        Record message processing time
        """
        self._metrics["processing_time"].append(time_ms)
        
        # Keep only last 1000 measurements
        if len(self._metrics["processing_time"]) > 1000:
            self._metrics["processing_time"] = self._metrics["processing_time"][-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics
        """
        metrics = self._metrics.copy()
        
        # Calculate average processing time
        if metrics["processing_time"]:
            metrics["avg_processing_time"] = sum(metrics["processing_time"]) / len(metrics["processing_time"])
            metrics["max_processing_time"] = max(metrics["processing_time"])
            metrics["min_processing_time"] = min(metrics["processing_time"])
        else:
            metrics["avg_processing_time"] = 0
            metrics["max_processing_time"] = 0
            metrics["min_processing_time"] = 0
        
        # Remove raw processing time list
        del metrics["processing_time"]
        
        return metrics
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics
        """
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "processing_time": [],
            "by_message_type": {},
            "by_agent": {}
        }


# Global instances
message_auditor = MessageAuditor()
message_metrics = MessageMetrics()