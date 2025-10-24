"""
Test configuration and fixtures for QA tests
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_database_session, Base
from core.config import settings

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test_internship_hub.db"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_database_session():
    """Override database session for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    app.dependency_overrides[get_database_session] = override_get_database_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_db):
    """Create async test client"""
    app.dependency_overrides[get_database_session] = override_get_database_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for tests"""
    return {
        "full_name": "Test User",
        "email": "test@example.com", 
        "password": "testpassword123",
        "role": "student"
    }


@pytest.fixture
def test_login_data():
    """Sample login data for tests"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
async def authenticated_user(async_client, test_user_data):
    """Create and authenticate a test user"""
    # Register user
    register_response = await async_client.post("/auth/register", json=test_user_data)
    assert register_response.status_code == 201
    
    # Login user
    login_data = {"email": test_user_data["email"], "password": test_user_data["password"]}
    login_response = await async_client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    return {
        "user": register_response.json(),
        "token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"]
    }