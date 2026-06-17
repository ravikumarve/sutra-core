"""
Agent API Routes
Endpoints for agent management and communication
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.schemas.common import (
    BaseResponse, ErrorResponse, AgentInfo, AgentStatus,
    AgentMessageRequest, AgentMessageResponse
)
from src.agents.coordinator import agent_coordinator
from src.agents.messages.message_schema import AgentType, MessageType
from src.security.auth import verify_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.get("/status", response_model=BaseResponse)
async def get_agent_status(
    tenant_id: str = Query(..., description="Tenant ID"),
    agent_type: Optional[str] = Query(None, description="Agent type"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get agent status for tenant
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # Get tenant status
        status = await agent_coordinator.get_tenant_status(tenant_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Filter by agent type if specified
        if agent_type:
            if agent_type not in status["agents"]:
                raise HTTPException(status_code=404, detail="Agent not found")
            return BaseResponse(
                success=True,
                message=f"Agent {agent_type} status retrieved",
                data={
                    "agent_type": agent_type,
                    "status": status["agents"][agent_type]
                }
            )
        
        return BaseResponse(
            success=True,
            message="Agent status retrieved",
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/message", response_model=BaseResponse)
async def send_agent_message(
    request: AgentMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Send message to agent
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # Validate agent type
        try:
            target_agent = AgentType(request.target_agent)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent type")
        
        # Send message to agent
        success = await agent_coordinator.send_message_to_tenant(
            tenant_id=request.tenant_id,
            agent_type=target_agent,
            message_data=request.payload
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        return BaseResponse(
            success=True,
            message="Message sent successfully",
            data={
                "tenant_id": request.tenant_id,
                "target_agent": request.target_agent,
                "message_type": request.message_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending agent message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/restart", response_model=BaseResponse)
async def restart_agent(
    tenant_id: str = Query(..., description="Tenant ID"),
    agent_type: Optional[str] = Query(None, description="Agent type"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Restart agent(s) for tenant
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # Restart tenant agents
        success = await agent_coordinator.restart_tenant_agents(tenant_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restart agents")
        
        return BaseResponse(
            success=True,
            message="Agents restarted successfully",
            data={
                "tenant_id": tenant_id,
                "agent_type": agent_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=BaseResponse)
async def get_agent_metrics(
    tenant_id: str = Query(..., description="Tenant ID"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get agent metrics for tenant
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # Get tenant status
        status = await agent_coordinator.get_tenant_status(tenant_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Calculate metrics
        metrics = {
            "total_agents": len(status["agents"]),
            "running_agents": sum(
                1 for agent in status["agents"].values()
                if agent.get("is_running", False)
            ),
            "total_queue_size": sum(
                agent.get("queue_size", 0)
                for agent in status["agents"].values()
            ),
            "total_active_tasks": sum(
                agent.get("active_tasks", 0)
                for agent in status["agents"].values()
            ),
            "agents": status["agents"]
        }
        
        return BaseResponse(
            success=True,
            message="Agent metrics retrieved",
            data=metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/logs", response_model=BaseResponse)
async def get_agent_logs(
    tenant_id: str = Query(..., description="Tenant ID"),
    agent_type: Optional[str] = Query(None, description="Agent type"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get agent logs for tenant
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # TODO: Implement actual log retrieval
        # For now, return placeholder data
        
        logs = [
            {
                "timestamp": "2026-04-26T10:00:00Z",
                "level": "INFO",
                "message": "Agent started successfully",
                "agent_type": agent_type or "liaison"
            }
        ]
        
        return BaseResponse(
            success=True,
            message="Agent logs retrieved",
            data={
                "tenant_id": tenant_id,
                "agent_type": agent_type,
                "logs": logs,
                "total": len(logs)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/messages/cleanup", response_model=BaseResponse)
async def cleanup_agent_messages(
    tenant_id: str = Query(..., description="Tenant ID"),
    max_age_hours: int = Query(24, ge=1, le=720, description="Maximum message age in hours"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Cleanup old messages for tenant
    """
    try:
        # Verify token
        user = await verify_token(credentials.credentials)
        
        # Cleanup old messages
        cleaned = await agent_coordinator.cleanup_old_messages(
            tenant_id=tenant_id,
            max_age_hours=max_age_hours
        )
        
        return BaseResponse(
            success=True,
            message=f"Cleaned up {cleaned} old messages",
            data={
                "tenant_id": tenant_id,
                "cleaned_count": cleaned,
                "max_age_hours": max_age_hours
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")