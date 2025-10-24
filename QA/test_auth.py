"""
Authentication API Tests
Tests for user registration, login, token management, and password operations
"""
import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Test user registration functionality"""
    
    @pytest.mark.asyncio
    async def test_register_valid_user(self, async_client: AsyncClient, test_user_data):
        """Test successful user registration"""
        # Debug: Print test data
        print(f"Test data: {test_user_data}")
        print(f"Password length: {len(test_user_data['password'])}")
        print(f"Password bytes: {len(test_user_data['password'].encode('utf-8'))}")
        
        response = await async_client.post("/auth/register", json=test_user_data)
        
        # Debug: Print response details if test fails
        if response.status_code != 201:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        await async_client.post("/auth/register", json=test_user_data)
        
        # Try to register same email again
        response = await async_client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient, test_user_data):
        """Test registration with invalid email format"""
        test_user_data["email"] = "invalid-email"
        
        response = await async_client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient, test_user_data):
        """Test registration with weak password"""
        test_user_data["password"] = "123"  # Too short
        
        response = await async_client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 422


class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, async_client: AsyncClient, test_user_data):
        """Test successful login"""
        # Register user first
        await async_client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, async_client: AsyncClient):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient, test_user_data):
        """Test login with wrong password"""
        # Register user first
        await async_client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await async_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


class TestTokenManagement:
    """Test JWT token operations"""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, authenticated_user):
        """Test getting current user with valid token"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["user"]["email"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client: AsyncClient, authenticated_user):
        """Test token refresh"""
        refresh_data = {"refresh_token": authenticated_user["refresh_token"]}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid-refresh-token"}
        response = await async_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, async_client: AsyncClient, authenticated_user):
        """Test user logout"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        response = await async_client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestPasswordOperations:
    """Test password reset and change operations"""
    
    @pytest.mark.asyncio
    async def test_password_reset_request(self, async_client: AsyncClient, test_user_data):
        """Test password reset request"""
        # Register user first
        await async_client.post("/auth/register", json=test_user_data)
        
        # Request password reset
        reset_data = {"email": test_user_data["email"]}
        response = await async_client.post("/auth/password/reset", json=reset_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset link has been sent" in data["message"]
    
    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, async_client: AsyncClient):
        """Test password reset for non-existent email"""
        reset_data = {"email": "nonexistent@example.com"}
        response = await async_client.post("/auth/password/reset", json=reset_data)
        
        # Should still return success for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_change_password(self, async_client: AsyncClient, authenticated_user):
        """Test password change for authenticated user"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        change_data = {
            "current_password": "testpassword123",
            "new_password": "newtestpassword456"
        }
        response = await async_client.post("/auth/password/change", json=change_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successfully changed" in data["message"]
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, async_client: AsyncClient, authenticated_user):
        """Test password change with wrong current password"""
        headers = {"Authorization": f"Bearer {authenticated_user['token']}"}
        change_data = {
            "current_password": "wrongpassword",
            "new_password": "newtestpassword456"
        }
        response = await async_client.post("/auth/password/change", json=change_data, headers=headers)
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self, async_client: AsyncClient):
        """Test password change without authentication"""
        change_data = {
            "current_password": "testpassword123",
            "new_password": "newtestpassword456"
        }
        response = await async_client.post("/auth/password/change", json=change_data)
        
        assert response.status_code == 422  # Missing Authorization header