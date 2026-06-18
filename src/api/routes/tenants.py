"""
Tenant API Routes
Endpoints for tenant management
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.schemas.common import (
    BaseResponse, ErrorResponse, TenantCreateRequest, TenantUpdateRequest,
    TenantInfo, TenantStatus
)
from src.agents.coordinator import agent_coordinator
from datetime import datetime
from src.security.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=BaseResponse)
async def create_tenant(
    request: TenantCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new tenant
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Generate tenant ID
        import uuid
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        
        # Provision tenant
        success = await agent_coordinator.provision_tenant(
            tenant_id=tenant_id,
            tenant_name=request.name,
            industry=request.industry
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create tenant")
        
        # TODO: Save tenant details to database
        # For now, return placeholder data
        
        tenant_info = TenantInfo(
            tenant_id=tenant_id,
            name=request.name,
            phone_number_id=request.phone_number_id,
            gst_state_code=request.gst_state_code,
            industry=request.industry,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        return BaseResponse(
            success=True,
            message="Tenant created successfully",
            data=tenant_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tenant_id}", response_model=BaseResponse)
async def get_tenant(
    tenant_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get tenant information
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Get tenant status
        status = await agent_coordinator.get_tenant_status(tenant_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # TODO: Get tenant details from database
        # For now, return status data
        
        return BaseResponse(
            success=True,
            message="Tenant retrieved successfully",
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{tenant_id}", response_model=BaseResponse)
async def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update tenant information
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Check if tenant exists
        status = await agent_coordinator.get_tenant_status(tenant_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # TODO: Update tenant details in database
        # For now, return success
        
        return BaseResponse(
            success=True,
            message="Tenant updated successfully",
            data={"tenant_id": tenant_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{tenant_id}", response_model=BaseResponse)
async def delete_tenant(
    tenant_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete tenant
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Deprovision tenant
        success = await agent_coordinator.deprovision_tenant(tenant_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete tenant")
        
        # TODO: Delete tenant from database
        
        return BaseResponse(
            success=True,
            message="Tenant deleted successfully",
            data={"tenant_id": tenant_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=BaseResponse)
async def list_tenants(
    limit: int = Query(100, ge=1, le=1000, description="Number of tenants to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all tenants
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Get all tenants
        tenants = await agent_coordinator.get_all_tenants()
        
        # Apply pagination
        paginated_tenants = tenants[offset:offset + limit]
        
        return BaseResponse(
            success=True,
            message="Tenants retrieved successfully",
            data={
                "tenants": paginated_tenants,
                "total": len(tenants),
                "limit": limit,
                "offset": offset
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tenant_id}/status", response_model=BaseResponse)
async def get_tenant_status(
    tenant_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get tenant status
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Get tenant status
        status = await agent_coordinator.get_tenant_status(tenant_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return BaseResponse(
            success=True,
            message="Tenant status retrieved",
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tenant_id}/restart", response_model=BaseResponse)
async def restart_tenant_agents(
    tenant_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Restart tenant agents
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Restart tenant agents
        success = await agent_coordinator.restart_tenant_agents(tenant_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restart tenant agents")
        
        return BaseResponse(
            success=True,
            message="Tenant agents restarted successfully",
            data={"tenant_id": tenant_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting tenant agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/system/status", response_model=BaseResponse)
async def get_system_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get system status
    """
    try:
        # Verify token
        user = verify_token(credentials.credentials)
        
        # Get system status
        status = await agent_coordinator.get_system_status()
        
        return BaseResponse(
            success=True,
            message="System status retrieved",
            data=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")