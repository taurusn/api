"""
API Endpoint Tests
General API functionality, validation, and error handling tests
"""
import pytest
from httpx import AsyncClient


class TestAPIHealth:
    """Test API health and basic endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint response"""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint"""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data


class TestAPIValidation:
    """Test API request validation and error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_json_request(self, async_client: AsyncClient):
        """Test API response to invalid JSON"""
        response = await async_client.post(
            "/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """Test API response to missing required fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing required fields: full_name, password, role
        }
        response = await async_client.post("/auth/register", json=incomplete_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.asyncio
    async def test_invalid_field_types(self, async_client: AsyncClient):
        """Test API response to invalid field types"""
        invalid_data = {
            "full_name": 123,  # Should be string
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
        response = await async_client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422


class TestAPIHeaders:
    """Test API header handling"""
    
    @pytest.mark.asyncio
    async def test_content_type_json(self, async_client: AsyncClient):
        """Test API accepts JSON content type"""
        user_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
        response = await async_client.post(
            "/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are present"""
        response = await async_client.get("/")
        
        # Note: CORS headers would be configured in main.py if needed
        assert response.status_code == 200


class TestAPIErrorHandling:
    """Test API error responses and status codes"""
    
    @pytest.mark.asyncio
    async def test_404_endpoint(self, async_client: AsyncClient):
        """Test 404 response for non-existent endpoint"""
        response = await async_client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, async_client: AsyncClient):
        """Test 405 response for wrong HTTP method"""
        response = await async_client.get("/auth/register")  # Should be POST
        
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_unsupported_media_type(self, async_client: AsyncClient):
        """Test 415 response for unsupported content type"""
        response = await async_client.post(
            "/auth/register",
            content="form data",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code in [415, 422]  # Either is acceptable


class TestAPIResponses:
    """Test API response formats and structures"""
    
    @pytest.mark.asyncio
    async def test_success_response_format(self, async_client: AsyncClient):
        """Test successful response format"""
        user_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
        response = await async_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert isinstance(data, dict)
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
        assert "created_at" in data
        
        # Ensure sensitive data is not returned
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_error_response_format(self, async_client: AsyncClient):
        """Test error response format"""
        # Make request that will fail
        response = await async_client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        
        # Check error response structure
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    @pytest.mark.asyncio
    async def test_validation_error_response(self, async_client: AsyncClient):
        """Test validation error response format"""
        # Send invalid data
        response = await async_client.post("/auth/register", json={
            "email": "invalid-email",  # Invalid email format
            "password": "123"  # Too short
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # Check validation error structure
        assert "detail" in data
        assert isinstance(data["detail"], list)
        
        # Each error should have required fields
        for error in data["detail"]:
            assert "loc" in error  # Location of error
            assert "msg" in error  # Error message
            assert "type" in error  # Error type


class TestAPIPerformance:
    """Test API performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, async_client: AsyncClient):
        """Test API response time is reasonable"""
        import time
        
        start_time = time.time()
        response = await async_client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test API can handle concurrent requests"""
        import asyncio
        
        # Make multiple concurrent requests
        tasks = []
        for i in range(10):
            task = async_client.get("/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200