"""
Agent Coordinator
Manages and coordinates all agents in the system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.agents.liaison.liaison_agent import LiaisonAgent
from src.agents.strategist.strategist_agent import StrategistAgent
from src.agents.auditor.auditor_agent import AuditorAgent
from src.agents.messages.message_schema import AgentType, MessageType
from src.agents.common.redis_streams import RedisStreamsManager, redis_streams_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates all agents in the system
    Manages agent lifecycle and communication
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.tenant_agents: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.redis_manager = redis_streams_manager
        
        logger.info("Agent Coordinator initialized")
    
    async def start(self) -> None:
        """
        Start the coordinator
        """
        try:
            logger.info("Starting Agent Coordinator...")
            
            # Connect to Redis
            await self.redis_manager.connect()
            
            # Start coordinator tasks
            self.is_running = True
            
            logger.info("Agent Coordinator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Agent Coordinator: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the coordinator
        """
        try:
            logger.info("Stopping Agent Coordinator...")
            
            # Stop all agents
            await self.stop_all_agents()
            
            # Disconnect from Redis
            await self.redis_manager.disconnect()
            
            self.is_running = False
            
            logger.info("Agent Coordinator stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop Agent Coordinator: {e}")
    
    async def provision_tenant(
        self,
        tenant_id: str,
        tenant_name: str,
        industry: str = "general"
    ) -> bool:
        """
        Provision a new tenant
        Creates tenant-specific agents and resources
        """
        try:
            logger.info(f"Provisioning tenant: {tenant_id} ({tenant_name})")
            
            # Check if tenant already exists
            if tenant_id in self.tenant_agents:
                logger.warning(f"Tenant {tenant_id} already exists")
                return False
            
            # Create tenant-specific streams
            await self._create_tenant_streams(tenant_id)
            
            # Create tenant-specific agents
            await self._create_tenant_agents(tenant_id, industry)
            
            logger.info(f"Tenant {tenant_id} provisioned successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to provision tenant {tenant_id}: {e}")
            return False
    
    async def deprovision_tenant(self, tenant_id: str) -> bool:
        """
        Deprovision a tenant
        Removes tenant-specific agents and resources
        """
        try:
            logger.info(f"Deprovisioning tenant: {tenant_id}")
            
            # Check if tenant exists
            if tenant_id not in self.tenant_agents:
                logger.warning(f"Tenant {tenant_id} does not exist")
                return False
            
            # Stop tenant agents
            await self._stop_tenant_agents(tenant_id)
            
            # Remove tenant agents
            del self.tenant_agents[tenant_id]
            
            # Clean up tenant streams (optional)
            # await self._cleanup_tenant_streams(tenant_id)
            
            logger.info(f"Tenant {tenant_id} deprovisioned successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deprovision tenant {tenant_id}: {e}")
            return False
    
    async def _create_tenant_streams(self, tenant_id: str) -> None:
        """
        Create tenant-specific streams
        """
        # Create streams for each agent type
        for agent_type in AgentType:
            await self.redis_manager.create_stream(
                tenant_id=tenant_id,
                stream_type=agent_type.value
            )
            
            # Create consumer group
            await self.redis_manager.create_consumer_group(
                tenant_id=tenant_id,
                stream_type=agent_type.value,
                agent_name=agent_type.value
            )
        
        logger.info(f"Created streams for tenant {tenant_id}")
    
    async def _create_tenant_agents(
        self,
        tenant_id: str,
        industry: str
    ) -> None:
        """
        Create tenant-specific agents
        """
        # Create Liaison agent
        liaison_agent = LiaisonAgent(tenant_id=tenant_id)
        await liaison_agent.start()
        
        # Create Strategist agent
        strategist_agent = StrategistAgent(tenant_id=tenant_id)
        await strategist_agent.start()
        
        # Create Auditor agent
        auditor_agent = AuditorAgent(tenant_id=tenant_id)
        await auditor_agent.start()
        
        # Store agents
        self.tenant_agents[tenant_id] = {
            "liaison": liaison_agent,
            "strategist": strategist_agent,
            "auditor": auditor_agent,
            "industry": industry,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created agents for tenant {tenant_id}")
    
    async def _stop_tenant_agents(self, tenant_id: str) -> None:
        """
        Stop tenant-specific agents
        """
        if tenant_id not in self.tenant_agents:
            return
        
        agents = self.tenant_agents[tenant_id]
        
        # Stop each agent
        for agent_name, agent in agents.items():
            if agent_name in ["liaison", "strategist", "auditor"]:
                try:
                    await agent.stop()
                    logger.info(f"Stopped {agent_name} agent for tenant {tenant_id}")
                except Exception as e:
                    logger.error(f"Failed to stop {agent_name} agent: {e}")
    
    async def get_tenant_status(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of tenant agents
        """
        if tenant_id not in self.tenant_agents:
            return None
        
        agents = self.tenant_agents[tenant_id]
        
        status = {
            "tenant_id": tenant_id,
            "industry": agents.get("industry", "unknown"),
            "created_at": agents.get("created_at", "unknown"),
            "agents": {}
        }
        
        # Get status of each agent
        for agent_name, agent in agents.items():
            if agent_name in ["liaison", "strategist", "auditor"]:
                try:
                    agent_status = await agent.get_status()
                    status["agents"][agent_name] = agent_status
                except Exception as e:
                    status["agents"][agent_name] = {
                        "error": str(e),
                        "is_running": False
                    }
        
        return status
    
    async def get_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Get status of all tenants
        """
        tenants = []
        
        for tenant_id in self.tenant_agents:
            status = await self.get_tenant_status(tenant_id)
            if status:
                tenants.append(status)
        
        return tenants
    
    async def send_message_to_tenant(
        self,
        tenant_id: str,
        agent_type: AgentType,
        message_data: Dict[str, Any]
    ) -> bool:
        """
        Send message to specific tenant agent
        """
        try:
            if tenant_id not in self.tenant_agents:
                logger.error(f"Tenant {tenant_id} not found")
                return False
            
            agents = self.tenant_agents[tenant_id]
            agent = agents.get(agent_type.value)
            
            if not agent:
                logger.error(f"Agent {agent_type.value} not found for tenant {tenant_id}")
                return False
            
            # Send message to agent
            # TODO: Implement message sending
            logger.info(f"Sent message to {agent_type.value} agent for tenant {tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to tenant {tenant_id}: {e}")
            return False
    
    async def restart_tenant_agents(self, tenant_id: str) -> bool:
        """
        Restart tenant agents
        """
        try:
            if tenant_id not in self.tenant_agents:
                logger.error(f"Tenant {tenant_id} not found")
                return False
            
            # Get tenant info
            tenant_info = self.tenant_agents[tenant_id]
            industry = tenant_info.get("industry", "general")
            
            # Stop existing agents
            await self._stop_tenant_agents(tenant_id)
            
            # Create new agents
            await self._create_tenant_agents(tenant_id, industry)
            
            logger.info(f"Restarted agents for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart tenant agents: {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        """
        status = {
            "coordinator_running": self.is_running,
            "total_tenants": len(self.tenant_agents),
            "tenants": await self.get_all_tenants(),
            "redis_connected": self.redis_manager.redis is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return status
    
    async def cleanup_old_messages(self, tenant_id: str, max_age_hours: int = 24) -> int:
        """
        Cleanup old messages for tenant
        """
        try:
            if tenant_id not in self.tenant_agents:
                logger.error(f"Tenant {tenant_id} not found")
                return 0
            
            total_cleaned = 0
            
            # Cleanup messages for each stream
            for agent_type in AgentType:
                cleaned = await self.redis_manager.cleanup_old_messages(
                    tenant_id=tenant_id,
                    stream_type=agent_type.value,
                    max_age_hours=max_age_hours
                )
                total_cleaned += cleaned
            
            logger.info(f"Cleaned up {total_cleaned} old messages for tenant {tenant_id}")
            return total_cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            return 0
    
    async def stop_all_agents(self) -> None:
        """
        Stop all agents for all tenants
        """
        for tenant_id in list(self.tenant_agents.keys()):
            await self._stop_tenant_agents(tenant_id)
        
        logger.info("Stopped all agents")


# Global coordinator instance
agent_coordinator = AgentCoordinator()