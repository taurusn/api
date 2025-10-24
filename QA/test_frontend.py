"""
Frontend-style API Tests
Tests that make actual HTTP requests to the running FastAPI server
Run these tests while the server is running on http://localhost:8000
"""
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

# Test data - matches bootstrap users from .env file
test_user = {
    "full_name": "Test Student User",
    "email": "user1@example.com",
    "password": "user123",
    "role": "student"
}

test_company = {
    "full_name": "Test Company User",
    "email": "user2@example.com", 
    "password": "user456",
    "role": "company"
}

# Admin user for testing (from bootstrap)
admin_user = {
    "full_name": "System Administrator",
    "email": "admin@example.com",
    "password": "admin123",
    "role": "admin"
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                    use_auth: bool = False) -> requests.Response:
        """Make HTTP request to API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if use_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        if method.upper() == "GET":
            return self.session.get(url, headers=headers, timeout=TIMEOUT)
        elif method.upper() == "POST":
            return self.session.post(url, headers=headers, json=data, timeout=TIMEOUT)
        elif method.upper() == "PUT":
            return self.session.put(url, headers=headers, json=data, timeout=TIMEOUT)
        elif method.upper() == "DELETE":
            return self.session.delete(url, headers=headers, timeout=TIMEOUT)
    
    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("🔍 Testing Health Endpoints")
        
        # Test root endpoint
        try:
            response = self.make_request("GET", "/")
            success = response.status_code == 200 and "message" in response.json()
            details = f"Status: {response.status_code}, Response: {response.json()}"
            self.log_test("GET /", success, details)
        except Exception as e:
            self.log_test("GET /", False, f"Error: {str(e)}")
        
        # Test health endpoint
        try:
            response = self.make_request("GET", "/health")
            success = response.status_code == 200 and response.json().get("status") == "healthy"
            details = f"Status: {response.status_code}, Response: {response.json()}"
            self.log_test("GET /health", success, details)
        except Exception as e:
            self.log_test("GET /health", False, f"Error: {str(e)}")
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        print("🔍 Testing User Registration")
        
        # Create unique user for registration test
        import time
        unique_email = f"newuser{int(time.time())}@example.com"
        new_user = {
            "full_name": "New Test User",
            "email": unique_email,
            "password": "newpass123",
            "role": "student"
        }
        
        # Test valid registration
        try:
            response = self.make_request("POST", "/auth/register", new_user)
            success = response.status_code == 201
            if success:
                data = response.json()
                success = (data.get("email") == new_user["email"] and 
                          data.get("full_name") == new_user["full_name"] and
                          "password" not in data)
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("POST /auth/register (valid)", success, details)
        except Exception as e:
            self.log_test("POST /auth/register (valid)", False, f"Error: {str(e)}")
        
        # Test duplicate email
        try:
            response = self.make_request("POST", "/auth/register", test_user)
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("POST /auth/register (duplicate)", success, details)
        except Exception as e:
            self.log_test("POST /auth/register (duplicate)", False, f"Error: {str(e)}")
        
        # Test invalid email
        try:
            invalid_user = test_user.copy()
            invalid_user["email"] = "invalid-email"
            response = self.make_request("POST", "/auth/register", invalid_user)
            success = response.status_code == 422
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("POST /auth/register (invalid email)", success, details)
        except Exception as e:
            self.log_test("POST /auth/register (invalid email)", False, f"Error: {str(e)}")
    
    def test_user_login(self):
        """Test user login endpoint"""
        print("🔍 Testing User Login")
        
        # Test valid login
        try:
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            response = self.make_request("POST", "/auth/login", login_data)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                success = (self.access_token is not None and 
                          self.refresh_token is not None and
                          data.get("token_type") == "bearer")
            details = f"Status: {response.status_code}, Has tokens: {bool(self.access_token)}"
            self.log_test("POST /auth/login (valid)", success, details)
        except Exception as e:
            self.log_test("POST /auth/login (valid)", False, f"Error: {str(e)}")
        
        # Test invalid credentials
        try:
            invalid_login = {
                "email": test_user["email"],
                "password": "wrongpassword"
            }
            response = self.make_request("POST", "/auth/login", invalid_login)
            success = response.status_code == 401
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("POST /auth/login (invalid)", success, details)
        except Exception as e:
            self.log_test("POST /auth/login (invalid)", False, f"Error: {str(e)}")
    
    def test_authenticated_endpoints(self):
        """Test endpoints that require authentication"""
        print("🔍 Testing Authenticated Endpoints")
        
        if not self.access_token:
            self.log_test("Authentication required", False, "No access token available")
            return
        
        # Test get current user
        try:
            response = self.make_request("GET", "/auth/me", use_auth=True)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("email") == test_user["email"]
            details = f"Status: {response.status_code}, Email match: {success if response.status_code == 200 else 'N/A'}"
            self.log_test("GET /auth/me", success, details)
        except Exception as e:
            self.log_test("GET /auth/me", False, f"Error: {str(e)}")
        
        # Test logout
        try:
            response = self.make_request("POST", "/auth/logout", use_auth=True)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("success") is True
            details = f"Status: {response.status_code}, Success: {success if response.status_code == 200 else 'N/A'}"
            self.log_test("POST /auth/logout", success, details)
        except Exception as e:
            self.log_test("POST /auth/logout", False, f"Error: {str(e)}")
    
    def test_token_refresh(self):
        """Test token refresh endpoint"""
        print("🔍 Testing Token Refresh")
        
        if not self.refresh_token:
            self.log_test("Token refresh", False, "No refresh token available")
            return
        
        try:
            refresh_data = {"refresh_token": self.refresh_token}
            response = self.make_request("POST", "/auth/refresh", refresh_data)
            success = response.status_code == 200
            if success:
                data = response.json()
                new_access_token = data.get("access_token")
                success = new_access_token is not None and new_access_token != self.access_token
            details = f"Status: {response.status_code}, New token: {bool(success) if response.status_code == 200 else 'N/A'}"
            self.log_test("POST /auth/refresh", success, details)
        except Exception as e:
            self.log_test("POST /auth/refresh", False, f"Error: {str(e)}")
    
    def test_password_reset(self):
        """Test password reset endpoints"""
        print("🔍 Testing Password Reset")
        
        # Test password reset request
        try:
            reset_data = {"email": test_user["email"]}
            response = self.make_request("POST", "/auth/password/reset", reset_data)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("success") is True
            details = f"Status: {response.status_code}, Success: {success if response.status_code == 200 else 'N/A'}"
            self.log_test("POST /auth/password/reset", success, details)
        except Exception as e:
            self.log_test("POST /auth/password/reset", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Frontend-Style API Tests")
        print(f"📡 Server URL: {BASE_URL}")
        print("=" * 50)
        
        self.test_health_endpoints()
        self.test_user_registration()
        self.test_user_login()
        self.test_token_refresh()  # Test refresh before logout invalidates tokens
        self.test_authenticated_endpoints()
        self.test_password_reset()
        
        print("=" * 50)
        print("✅ All tests completed!")
        print(f"📚 Visit {BASE_URL}/docs for interactive API documentation")

def main():
    """Main function to run tests"""
    tester = APITester()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running or not healthy")
            print(f"   Please start the server with: python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        print(f"   Please ensure server is running on {BASE_URL}")
        print("   Start with: python main.py")
        return
    
    # Run tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()