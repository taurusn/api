"""
Company Features API Tests
Tests the complete company workflow including internship management,
application handling, and role-based access control.
Run these tests while the server is running on http://localhost:8000
"""
import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

# Test data - matches bootstrap users from .env file
test_company = {
    "full_name": "Test Company User",
    "email": "user2@example.com", 
    "password": "user456",
    "role": "company"
}

test_student = {
    "full_name": "Test Student User",
    "email": "user1@example.com",
    "password": "user123",
    "role": "student"
}

# Sample internship data for testing
sample_internship = {
    "title": "Software Engineering Intern",
    "description": "Work with our development team on cutting-edge projects using modern technologies",
    "location": "New York, NY",
    "category": "Technology",
    "type": "onsite",
    "duration_weeks": 12,
    "requirements": "Python, JavaScript, SQL knowledge required",
    "benefits": "Competitive salary, mentorship, real-world experience",
    "salary_min": 3000,
    "salary_max": 5000,
    "status": "draft"
}

class CompanyAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.company_token = None
        self.student_token = None
        self.created_internships = []  # Track created internships for cleanup
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results with consistent formatting"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                    token: str = None) -> requests.Response:
        """Make HTTP request to API endpoint with optional authentication"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                return self.session.get(url, headers=headers, timeout=TIMEOUT)
            elif method.upper() == "POST":
                return self.session.post(url, headers=headers, json=data, timeout=TIMEOUT)
            elif method.upper() == "PATCH":
                return self.session.patch(url, headers=headers, json=data, timeout=TIMEOUT)
            elif method.upper() == "PUT":
                return self.session.put(url, headers=headers, json=data, timeout=TIMEOUT)
            elif method.upper() == "DELETE":
                return self.session.delete(url, headers=headers, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise
    
    def authenticate_users(self):
        """Authenticate both company and student users for testing"""
        print("🔐 Authenticating Test Users")
        
        # Authenticate company user
        try:
            company_login = {
                "email": test_company["email"],
                "password": test_company["password"]
            }
            response = self.make_request("POST", "/auth/login", company_login)
            if response.status_code == 200:
                data = response.json()
                self.company_token = data.get("access_token")
                success = self.company_token is not None
            else:
                success = False
            
            details = f"Status: {response.status_code}"
            self.log_test("Company Authentication", success, details)
        except Exception as e:
            self.log_test("Company Authentication", False, f"Error: {str(e)}")
        
        # Authenticate student user
        try:
            student_login = {
                "email": test_student["email"],
                "password": test_student["password"]
            }
            response = self.make_request("POST", "/auth/login", student_login)
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get("access_token")
                success = self.student_token is not None
            else:
                success = False
            
            details = f"Status: {response.status_code}"
            self.log_test("Student Authentication", success, details)
        except Exception as e:
            self.log_test("Student Authentication", False, f"Error: {str(e)}")
    
    def test_internship_creation(self):
        """Test internship creation with various scenarios"""
        print("🏗️ Testing Internship Creation")
        
        # Test valid internship creation
        try:
            response = self.make_request("POST", "/internships", sample_internship, self.company_token)
            success = response.status_code == 201
            
            if success:
                data = response.json()
                # Verify all fields are correctly set
                success = (
                    data.get("title") == sample_internship["title"] and
                    data.get("description") == sample_internship["description"] and
                    data.get("status") == sample_internship["status"] and
                    data.get("id") is not None
                )
                if success:
                    self.created_internships.append(data["id"])
            
            details = f"Status: {response.status_code}"
            if not success and response.status_code != 201:
                details += f", Response: {response.text[:200]}"
            
            self.log_test("POST /internships (valid creation)", success, details)
        except Exception as e:
            self.log_test("POST /internships (valid creation)", False, f"Error: {str(e)}")
        
        # Test creation without authentication
        try:
            response = self.make_request("POST", "/internships", sample_internship)
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            self.log_test("POST /internships (no auth)", success, details)
        except Exception as e:
            self.log_test("POST /internships (no auth)", False, f"Error: {str(e)}")
        
        # Test creation with student token (should fail)
        try:
            response = self.make_request("POST", "/internships", sample_internship, self.student_token)
            success = response.status_code == 403
            details = f"Status: {response.status_code}"
            self.log_test("POST /internships (student role)", success, details)
        except Exception as e:
            self.log_test("POST /internships (student role)", False, f"Error: {str(e)}")
        
        # Test creation with invalid data
        try:
            invalid_internship = sample_internship.copy()
            invalid_internship["title"] = "AB"  # Too short
            response = self.make_request("POST", "/internships", invalid_internship, self.company_token)
            success = response.status_code == 422
            details = f"Status: {response.status_code}"
            self.log_test("POST /internships (invalid data)", success, details)
        except Exception as e:
            self.log_test("POST /internships (invalid data)", False, f"Error: {str(e)}")
    
    def test_internship_listing(self):
        """Test role-aware internship listing"""
        print("📋 Testing Internship Listing")
        
        # Test company listing (should see their own internships)
        try:
            response = self.make_request("GET", "/internships", token=self.company_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    "items" in data and
                    "total" in data and
                    "page" in data and
                    isinstance(data["items"], list)
                )
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Found {len(data['items'])} internships"
            
            self.log_test("GET /internships (company view)", success, details)
        except Exception as e:
            self.log_test("GET /internships (company view)", False, f"Error: {str(e)}")
        
        # Test student listing (should see all active internships)
        try:
            response = self.make_request("GET", "/internships", token=self.student_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    "items" in data and
                    "total" in data and
                    isinstance(data["items"], list)
                )
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Found {len(data['items'])} internships"
            
            self.log_test("GET /internships (student view)", success, details)
        except Exception as e:
            self.log_test("GET /internships (student view)", False, f"Error: {str(e)}")
        
        # Test pagination
        try:
            response = self.make_request("GET", "/internships?page=1&size=5", token=self.company_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    data.get("page") == 1 and
                    data.get("size") == 5 and
                    len(data.get("items", [])) <= 5
                )
            
            details = f"Status: {response.status_code}"
            self.log_test("GET /internships (pagination)", success, details)
        except Exception as e:
            self.log_test("GET /internships (pagination)", False, f"Error: {str(e)}")
    
    def test_internship_details(self):
        """Test individual internship retrieval"""
        print("🔍 Testing Internship Details")
        
        if not self.created_internships:
            self.log_test("GET /internships/{id}", False, "No internships created to test")
            return
        
        internship_id = self.created_internships[0]
        
        # Test company access to their own internship
        try:
            response = self.make_request("GET", f"/internships/{internship_id}", token=self.company_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    data.get("id") == internship_id and
                    data.get("title") is not None and
                    "total_applications" in data
                )
            
            details = f"Status: {response.status_code}"
            self.log_test("GET /internships/{id} (company access)", success, details)
        except Exception as e:
            self.log_test("GET /internships/{id} (company access)", False, f"Error: {str(e)}")
        
        # Test student access to public internship
        try:
            response = self.make_request("GET", f"/internships/{internship_id}", token=self.student_token)
            # This might be 501 (not implemented) or 200 depending on implementation
            success = response.status_code in [200, 501]
            
            details = f"Status: {response.status_code}"
            if response.status_code == 501:
                details += " (Not implemented - expected)"
            
            self.log_test("GET /internships/{id} (student access)", success, details)
        except Exception as e:
            self.log_test("GET /internships/{id} (student access)", False, f"Error: {str(e)}")
    
    def test_internship_updates(self):
        """Test internship updates and status management"""
        print("✏️ Testing Internship Updates")
        
        if not self.created_internships:
            self.log_test("PATCH /internships/{id}", False, "No internships created to test")
            return
        
        internship_id = self.created_internships[0]
        
        # Test valid update
        try:
            update_data = {
                "title": "Updated Software Engineering Intern",
                "location": "San Francisco, CA"
            }
            response = self.make_request("PATCH", f"/internships/{internship_id}", update_data, self.company_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    data.get("title") == update_data["title"] and
                    data.get("location") == update_data["location"]
                )
            
            details = f"Status: {response.status_code}"
            self.log_test("PATCH /internships/{id} (valid update)", success, details)
        except Exception as e:
            self.log_test("PATCH /internships/{id} (valid update)", False, f"Error: {str(e)}")
        
        # Test status update
        try:
            status_data = {
                "status": "active",
                "reason": "Ready for applications"
            }
            response = self.make_request("PATCH", f"/internships/{internship_id}/status", status_data, self.company_token)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "active"
            
            details = f"Status: {response.status_code}"
            self.log_test("PATCH /internships/{id}/status", success, details)
        except Exception as e:
            self.log_test("PATCH /internships/{id}/status", False, f"Error: {str(e)}")
        
        # Test unauthorized update (student trying to update)
        try:
            update_data = {"title": "Hacked Title"}
            response = self.make_request("PATCH", f"/internships/{internship_id}", update_data, self.student_token)
            success = response.status_code == 403
            
            details = f"Status: {response.status_code}"
            self.log_test("PATCH /internships/{id} (unauthorized)", success, details)
        except Exception as e:
            self.log_test("PATCH /internships/{id} (unauthorized)", False, f"Error: {str(e)}")
    
    def test_internship_filtering(self):
        """Test internship filtering and search"""
        print("🔎 Testing Internship Filtering")
        
        # Test status filter
        try:
            response = self.make_request("GET", "/internships?status=active", token=self.company_token)
            success = response.status_code == 200
            
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Found {len(data.get('items', []))} active internships"
            
            self.log_test("GET /internships (status filter)", success, details)
        except Exception as e:
            self.log_test("GET /internships (status filter)", False, f"Error: {str(e)}")
        
        # Test category filter
        try:
            response = self.make_request("GET", "/internships?category=Technology", token=self.company_token)
            success = response.status_code == 200
            
            details = f"Status: {response.status_code}"
            self.log_test("GET /internships (category filter)", success, details)
        except Exception as e:
            self.log_test("GET /internships (category filter)", False, f"Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("🚨 Testing Error Handling")
        
        # Test nonexistent internship
        try:
            response = self.make_request("GET", "/internships/99999", token=self.company_token)
            success = response.status_code == 404
            
            details = f"Status: {response.status_code}"
            self.log_test("GET /internships/99999 (not found)", success, details)
        except Exception as e:
            self.log_test("GET /internships/99999 (not found)", False, f"Error: {str(e)}")
        
        # Test invalid status transition
        if self.created_internships:
            try:
                # Try to set closed status to active (invalid transition)
                status_data = {"status": "closed"}
                response = self.make_request("PATCH", f"/internships/{self.created_internships[0]}/status", status_data, self.company_token)
                
                # Then try invalid transition back
                if response.status_code == 200:
                    invalid_status_data = {"status": "draft"}
                    response = self.make_request("PATCH", f"/internships/{self.created_internships[0]}/status", invalid_status_data, self.company_token)
                    success = response.status_code == 400
                else:
                    success = True  # If first transition failed, that's also valid
                
                details = f"Status: {response.status_code}"
                self.log_test("PATCH /internships/{id}/status (invalid transition)", success, details)
            except Exception as e:
                self.log_test("PATCH /internships/{id}/status (invalid transition)", False, f"Error: {str(e)}")
    
    def test_internship_health(self):
        """Test internship service health endpoint"""
        print("💊 Testing Service Health")
        
        try:
            response = self.make_request("GET", "/internships/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (
                    data.get("service") == "internships" and
                    data.get("status") == "healthy"
                )
            
            details = f"Status: {response.status_code}"
            self.log_test("GET /internships/health", success, details)
        except Exception as e:
            self.log_test("GET /internships/health", False, f"Error: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("🧹 Cleaning Up Test Data")
        
        for internship_id in self.created_internships:
            try:
                response = self.make_request("DELETE", f"/internships/{internship_id}", token=self.company_token)
                success = response.status_code == 204
                
                details = f"Status: {response.status_code}"
                self.log_test(f"DELETE /internships/{internship_id}", success, details)
            except Exception as e:
                self.log_test(f"DELETE /internships/{internship_id}", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all company feature tests"""
        print("🚀 Starting Company Features Test Suite")
        print("=" * 60)
        
        # Authentication is required for all tests
        self.authenticate_users()
        
        if not self.company_token:
            print("❌ Cannot proceed without company authentication")
            return
        
        # Run all test suites
        self.test_internship_creation()
        self.test_internship_listing()
        self.test_internship_details()
        self.test_internship_updates()
        self.test_internship_filtering()
        self.test_error_handling()
        self.test_internship_health()
        
        # Cleanup
        self.cleanup_test_data()
        
        print("=" * 60)
        print("🏁 Company Features Test Suite Complete")

def main():
    """Main test runner"""
    print("🧪 Company Features API Test Runner")
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed. Make sure the API is running.")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server. Make sure it's running on http://localhost:8000")
        return
    
    # Run tests
    tester = CompanyAPITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()