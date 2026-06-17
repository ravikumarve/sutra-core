"""
Redis Streams Manager for Agent Communication
Handles Redis Streams infrastructure for multi-agent communication
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import redis.asyncio as redis
from redis.asyncio import Redis
from src.config.settings import settings

logger = logging.getLogger(__name__)


class RedisStreamsManager:
    """
    Manages Redis Streams for agent communication
    Provides per-tenant isolation and consumer group management
    """
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.stream_prefix = "sutra:streams"
        self.consumer_group_prefix = "sutra:consumers"
        self.dead_letter_prefix = "sutra:dlq"
        
    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE
            )
            await self.redis.ping()
            logger.info("Redis Streams Manager connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis Streams Manager disconnected")
    
    def _get_stream_name(self, tenant_id: str, stream_type: str) -> str:
        """
        Generate stream name for tenant
        Format: sutra:streams:{tenant_id}:{stream_type}
        """
        return f"{self.stream_prefix}:{tenant_id}:{stream_type}"
    
    def _get_consumer_group_name(self, tenant_id: str, agent_name: str) -> str:
        """
        Generate consumer group name
        Format: sutra:consumers:{tenant_id}:{agent_name}
        """
        return f"{self.consumer_group_prefix}:{tenant_id}:{agent_name}"
    
    def _get_dead_letter_queue_name(self, tenant_id: str) -> str:
        """
        Generate dead letter queue name
        Format: sutra:dlq:{tenant_id}
        """
        return f"{self.dead_letter_prefix}:{tenant_id}"
    
    async def create_stream(
        self,
        tenant_id: str,
        stream_type: str,
        max_length: int = 10000
    ) -> bool:
        """
        Create a new stream for tenant
        Uses MAXLEN for automatic trimming
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            
            # Create stream with max length
            await self.redis.xadd(
                stream_name,
                {"_init": "true"},
                maxlen=max_length
            )
            
            logger.info(f"Created stream: {stream_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create stream: {e}")
            return False
    
    async def create_consumer_group(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str,
        start_from: str = "0"
    ) -> bool:
        """
        Create consumer group for agent
        Uses MKGROUP with idempotency
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Create consumer group (idempotent)
            try:
                await self.redis.xgroup_create(
                    stream_name,
                    group_name,
                    id=start_from,
                    mkstream=True
                )
                logger.info(f"Created consumer group: {group_name}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                logger.info(f"Consumer group already exists: {group_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create consumer group: {e}")
            return False
    
    async def publish_message(
        self,
        tenant_id: str,
        stream_type: str,
        message: Dict[str, Any]
    ) -> Optional[str]:
        """
        Publish message to stream
        Returns message ID
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            
            # Add timestamp to message
            message["_timestamp"] = datetime.utcnow().isoformat()
            
            # Publish to stream
            message_id = await self.redis.xadd(stream_name, message)
            
            logger.debug(f"Published message to {stream_name}: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return None
    
    async def _read_messages_from_group(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int,
        block: Optional[int]
    ) -> List[tuple]:
        """
        Read messages from consumer group
        
        Args:
            stream_name: Stream name
            group_name: Consumer group name
            consumer_name: Consumer name
            count: Number of messages to read
            block: Block timeout in milliseconds
            
        Returns:
            List of (stream, message_list) tuples
        """
        if block:
            # Blocking read
            return await self.redis.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count,
                block=block
            )
        else:
            # Non-blocking read
            return await self.redis.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count
            )

    def _parse_messages(self, messages: List[tuple]) -> List[Dict[str, Any]]:
        """
        Parse raw messages from Redis into structured format
        
        Args:
            messages: Raw messages from Redis
            
        Returns:
            List of parsed message dictionaries
        """
        parsed_messages = []
        for stream, message_list in messages:
            for message_id, message_data in message_list:
                parsed_messages.append({
                    "message_id": message_id,
                    "stream": stream,
                    "data": message_data
                })
        return parsed_messages

    async def read_messages(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str,
        consumer_name: str,
        count: int = 10,
        block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Read messages from stream using consumer group
        Returns list of messages with IDs
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Read messages from consumer group
            messages = await self._read_messages_from_group(
                stream_name, group_name, consumer_name, count, block
            )
            
            # Parse messages
            parsed_messages = self._parse_messages(messages)
            
            logger.debug(f"Read {len(parsed_messages)} messages from {stream_name}")
            return parsed_messages
            
        except Exception as e:
            logger.error(f"Failed to read messages: {e}")
            return []
    
    async def acknowledge_message(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str,
        message_id: str
    ) -> bool:
        """
        Acknowledge message processing
        Removes message from pending list
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Acknowledge message
            await self.redis.xack(stream_name, group_name, message_id)
            
            logger.debug(f"Acknowledged message: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")
            return False
    
    async def send_to_dead_letter_queue(
        self,
        tenant_id: str,
        message: Dict[str, Any],
        error: str,
        retry_count: int = 0
    ) -> bool:
        """
        Send failed message to dead letter queue
        """
        try:
            dlq_name = self._get_dead_letter_queue_name(tenant_id)
            
            # Add metadata to message
            message["_error"] = error
            message["_retry_count"] = retry_count
            message["_failed_at"] = datetime.utcnow().isoformat()
            
            # Send to DLQ
            message_id = await self.redis.xadd(dlq_name, message)
            
            logger.warning(f"Sent message to DLQ: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
            return False
    
    async def get_pending_messages(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages for consumer group
        Useful for recovery and retry
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Get pending messages
            pending = await self.redis.xpending_range(
                stream_name,
                group_name,
                "-", "+",
                count=100
            )
            
            logger.debug(f"Found {len(pending)} pending messages")
            return pending
            
        except Exception as e:
            logger.error(f"Failed to get pending messages: {e}")
            return []
    
    async def claim_messages(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str,
        consumer_name: str,
        min_idle_time: int = 60000  # 1 minute
    ) -> List[Dict[str, Any]]:
        """
        Claim idle messages for processing
        Useful for recovery from crashed consumers
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Claim idle messages
            messages = await self.redis.xautoclaim(
                stream_name,
                group_name,
                consumer_name,
                min_idle_time,
                count=10
            )
            
            logger.debug(f"Claimed {len(messages)} idle messages")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to claim messages: {e}")
            return []
    
    async def get_stream_info(
        self,
        tenant_id: str,
        stream_type: str
    ) -> Dict[str, Any]:
        """
        Get stream information
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            
            # Get stream info
            info = await self.redis.xinfo_stream(stream_name)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            return {}
    
    async def get_consumer_group_info(
        self,
        tenant_id: str,
        stream_type: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Get consumer group information
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            group_name = self._get_consumer_group_name(tenant_id, agent_name)
            
            # Get consumer group info
            info = await self.redis.xinfo_groups(stream_name)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get consumer group info: {e}")
            return {}
    
    async def delete_stream(
        self,
        tenant_id: str,
        stream_type: str
    ) -> bool:
        """
        Delete stream (use with caution)
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            
            # Delete stream
            await self.redis.delete(stream_name)
            
            logger.warning(f"Deleted stream: {stream_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete stream: {e}")
            return False
    
    async def cleanup_old_messages(
        self,
        tenant_id: str,
        stream_type: str,
        max_age_hours: int = 24
    ) -> int:
        """
        Clean up old messages from stream
        Returns number of messages cleaned
        """
        try:
            stream_name = self._get_stream_name(tenant_id, stream_type)
            
            # Trim stream to keep only recent messages
            # This is approximate, Redis uses MAXLEN
            result = await self.redis.xtrim(
                stream_name,
                maxlen=10000,
                approximate=True
            )
            
            logger.info(f"Cleaned up {result} messages from {stream_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup messages: {e}")
            return 0


# Global instance
redis_streams_manager = RedisStreamsManager()