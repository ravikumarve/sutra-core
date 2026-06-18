"""
Unit Tests for API Endpoints
Tests agent and tenant API endpoints
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.main import app
from src.api.schemas.common import (
    AgentMessageRequest, TenantCreateRequest, BaseResponse
)


@pytest.mark.unit
class TestAgentAPIEndpoints:
    """Test agent API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Sample authentication headers"""
        return {"Authorization": "Bearer test_token"}
    
    def test_get_agent_status_success(self, client, auth_headers):
        """Test getting agent status - success"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            with patch('src.api.routes.agents.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_tenant_status = AsyncMock(return_value={
                    "tenant_id": "test_tenant",
                    "agents": {
                        "liaison": {"is_running": True, "queue_size": 0}
                    }
                })
                
                # Make request
                response = client.get(
                    "/api/v1/agents/status?tenant_id=test_tenant",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data
    
    def test_get_agent_status_not_found(self, client, auth_headers):
        """Test getting agent status - not found"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            with patch('src.api.routes.agents.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_tenant_status = AsyncMock(return_value=None)
                
                # Make request
                response = client.get(
                    "/api/v1/agents/status?tenant_id=nonexistent",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 404
    
    def test_send_agent_message_success(self, client, auth_headers):
        """Test sending agent message - success"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            with patch('src.api.routes.agents.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.send_message_to_tenant = AsyncMock(return_value=True)
                
                # Make request
                request_data = {
                    "tenant_id": "test_tenant",
                    "target_agent": "liaison",
                    "message_type": "intent_extracted",
                    "payload": {"text": "Hello"}
                }
                
                response = client.post(
                    "/api/v1/agents/message",
                    json=request_data,
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
    
    def test_send_agent_message_invalid_agent(self, client, auth_headers):
        """Test sending agent message - invalid agent type"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            # Setup mock
            mock_verify.return_value = {"user_id": "test_user"}
            
            # Make request with invalid agent
            request_data = {
                "tenant_id": "test_tenant",
                "target_agent": "invalid_agent",
                "message_type": "intent_extracted",
                "payload": {"text": "Hello"}
            }
            
            response = client.post(
                "/api/v1/agents/message",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify response
            assert response.status_code == 400
    
    def test_restart_agent_success(self, client, auth_headers):
        """Test restarting agent - success"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            with patch('src.api.routes.agents.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.restart_tenant_agents = AsyncMock(return_value=True)
                
                # Make request
                response = client.post(
                    "/api/v1/agents/restart?tenant_id=test_tenant",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
    
    def test_get_agent_metrics_success(self, client, auth_headers):
        """Test getting agent metrics - success"""
        with patch('src.api.routes.agents.verify_token') as mock_verify:
            with patch('src.api.routes.agents.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_tenant_status = AsyncMock(return_value={
                    "tenant_id": "test_tenant",
                    "agents": {
                        "liaison": {"is_running": True, "queue_size": 5, "active_tasks": 2},
                        "strategist": {"is_running": True, "queue_size": 3, "active_tasks": 1}
                    }
                })
                
                # Make request
                response = client.get(
                    "/api/v1/agents/metrics?tenant_id=test_tenant",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data
                assert "total_agents" in data["data"]
                assert "running_agents" in data["data"]


@pytest.mark.unit
class TestTenantAPIEndpoints:
    """Test tenant API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Sample authentication headers"""
        return {"Authorization": "Bearer test_token"}
    
    def test_create_tenant_success(self, client, auth_headers):
        """Test creating tenant - success"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.provision_tenant = AsyncMock(return_value=True)
                
                # Make request
                request_data = {
                    "name": "Test Business",
                    "phone_number_id": "9876543210",
                    "gst_state_code": 24,
                    "industry": "textiles"
                }
                
                response = client.post(
                    "/api/v1/tenants/",
                    json=request_data,
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data
    
    def test_create_tenant_validation_error(self, client, auth_headers):
        """Test creating tenant - validation error"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            # Setup mock
            mock_verify.return_value = {"user_id": "test_user"}
            
            # Make request with invalid data
            request_data = {
                "name": "AB",  # Too short
                "phone_number_id": "123",  # Too short
                "gst_state_code": 99  # Invalid state code
            }
            
            response = client.post(
                "/api/v1/tenants/",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify response
            assert response.status_code == 422
    
    def test_get_tenant_success(self, client, auth_headers):
        """Test getting tenant - success"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_tenant_status = AsyncMock(return_value={
                    "tenant_id": "test_tenant",
                    "name": "Test Business",
                    "industry": "textiles"
                })
                
                # Make request
                response = client.get(
                    "/api/v1/tenants/test_tenant",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
    
    def test_get_tenant_not_found(self, client, auth_headers):
        """Test getting tenant - not found"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_tenant_status = AsyncMock(return_value=None)
                
                # Make request
                response = client.get(
                    "/api/v1/tenants/nonexistent",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 404
    
    def test_list_tenants_success(self, client, auth_headers):
        """Test listing tenants - success"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_all_tenants = AsyncMock(return_value=[
                    {"tenant_id": "tenant_1", "name": "Business 1"},
                    {"tenant_id": "tenant_2", "name": "Business 2"}
                ])
                
                # Make request
                response = client.get(
                    "/api/v1/tenants/",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data
                assert "tenants" in data["data"]
    
    def test_delete_tenant_success(self, client, auth_headers):
        """Test deleting tenant - success"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.deprovision_tenant = AsyncMock(return_value=True)
                
                # Make request
                response = client.delete(
                    "/api/v1/tenants/test_tenant",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
    
    def test_get_system_status_success(self, client, auth_headers):
        """Test getting system status - success"""
        with patch('src.api.routes.tenants.verify_token') as mock_verify:
            with patch('src.api.routes.tenants.agent_coordinator') as mock_coordinator:
                # Setup mocks
                mock_verify.return_value = {"user_id": "test_user"}
                mock_coordinator.get_system_status = AsyncMock(return_value={
                    "coordinator_running": True,
                    "total_tenants": 5,
                    "redis_connected": True
                })
                
                # Make request
                response = client.get(
                    "/api/v1/tenants/system/status",
                    headers=auth_headers
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data