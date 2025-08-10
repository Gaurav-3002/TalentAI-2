#!/usr/bin/env python3
"""
Backend Authentication Testing Script
Focused on testing authentication failures reported from frontend integration
"""

import requests
import sys
import json
from datetime import datetime
import time

class BackendAuthTester:
    def __init__(self, base_url="https://b0f01cda-2385-4551-81cb-cf84983e55ee.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_tokens = {}
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        print(f"   Expected Status: {expected_status}")
        
        if headers:
            print(f"   Headers: {list(headers.keys())}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if data:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Actual Status: {response.status_code}")
            
            # Check response headers for CORS
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            if any(cors_headers.values()):
                print(f"   CORS Headers: {cors_headers}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED")
                try:
                    response_data = response.json()
                    self.log_test_result(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_test_result(name, True, f"Status: {response.status_code}, No JSON")
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error Response: {error_detail}")
                    self.log_test_result(name, False, f"Status: {response.status_code}, Error: {error_detail}")
                except:
                    print(f"   Response Text: {response.text[:200]}")
                    self.log_test_result(name, False, f"Status: {response.status_code}, Text: {response.text[:100]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timeout ({timeout}s)")
            self.log_test_result(name, False, "Timeout")
            return False, {}
        except requests.exceptions.ConnectionError as e:
            print(f"❌ FAILED - Connection error: {str(e)}")
            self.log_test_result(name, False, f"Connection error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.log_test_result(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health check endpoint"""
        print("\n" + "="*60)
        print("1. HEALTH CHECK TESTING")
        print("="*60)
        
        # Test root endpoint
        success, response = self.run_test(
            "Health Check - Root endpoint",
            "GET",
            "",
            200
        )
        
        if success:
            print(f"   ✅ Backend is responding")
            print(f"   Response: {response}")
        else:
            print(f"   ❌ Backend health check failed")
            return False
        
        return True

    def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n" + "="*60)
        print("2. CORS CONFIGURATION TESTING")
        print("="*60)
        
        # Test CORS preflight request
        cors_headers = {
            'Origin': self.base_url,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        
        try:
            response = requests.options(f"{self.api_url}/auth/login", headers=cors_headers, timeout=30)
            print(f"\n🔍 Testing CORS Preflight...")
            print(f"   Status: {response.status_code}")
            print(f"   CORS Headers in Response:")
            
            cors_response_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            for header, value in cors_response_headers.items():
                print(f"     {header}: {value}")
            
            # Check if CORS is properly configured
            if cors_response_headers['Access-Control-Allow-Origin']:
                print(f"   ✅ CORS Origin header present")
                self.log_test_result("CORS Configuration", True, "CORS headers present")
            else:
                print(f"   ❌ CORS Origin header missing")
                self.log_test_result("CORS Configuration", False, "CORS headers missing")
                
        except Exception as e:
            print(f"   ❌ CORS test failed: {e}")
            self.log_test_result("CORS Configuration", False, f"Exception: {e}")

    def test_demo_user_authentication(self):
        """Test demo user authentication with specific credentials"""
        print("\n" + "="*60)
        print("3. DEMO USER AUTHENTICATION TESTING")
        print("="*60)
        
        # Test admin demo user
        admin_credentials = {
            "email": "admin@jobmatcher.com",
            "password": "admin123"
        }
        
        print(f"\n🔍 Testing Admin Demo User Login...")
        success, response = self.run_test(
            "Demo Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_credentials,
            headers={'Content-Type': 'application/json'}
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['admin'] = response['access_token']
            print(f"   ✅ Admin login successful")
            print(f"   User: {response.get('user', {}).get('full_name', 'Unknown')}")
            print(f"   Role: {response.get('user', {}).get('role', 'Unknown')}")
            print(f"   Token: {response['access_token'][:20]}...")
        else:
            print(f"   ❌ Admin login failed")
            return False
        
        # Test recruiter demo user
        recruiter_credentials = {
            "email": "recruiter@jobmatcher.com",
            "password": "recruiter123"
        }
        
        print(f"\n🔍 Testing Recruiter Demo User Login...")
        success, response = self.run_test(
            "Demo Recruiter Login",
            "POST",
            "auth/login",
            200,
            data=recruiter_credentials,
            headers={'Content-Type': 'application/json'}
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['recruiter'] = response['access_token']
            print(f"   ✅ Recruiter login successful")
            print(f"   User: {response.get('user', {}).get('full_name', 'Unknown')}")
            print(f"   Role: {response.get('user', {}).get('role', 'Unknown')}")
            print(f"   Token: {response['access_token'][:20]}...")
        else:
            print(f"   ❌ Recruiter login failed")
            return False
        
        # Test candidate demo user (try common passwords)
        candidate_passwords = ["candidate123", "password", "123456", "candidate"]
        candidate_email = "candidate@jobmatcher.com"
        
        print(f"\n🔍 Testing Candidate Demo User Login...")
        candidate_login_success = False
        
        for password in candidate_passwords:
            candidate_credentials = {
                "email": candidate_email,
                "password": password
            }
            
            success, response = self.run_test(
                f"Demo Candidate Login (password: {password})",
                "POST",
                "auth/login",
                200,
                data=candidate_credentials,
                headers={'Content-Type': 'application/json'}
            )
            
            if success and 'access_token' in response:
                self.auth_tokens['candidate'] = response['access_token']
                print(f"   ✅ Candidate login successful with password: {password}")
                print(f"   User: {response.get('user', {}).get('full_name', 'Unknown')}")
                print(f"   Role: {response.get('user', {}).get('role', 'Unknown')}")
                candidate_login_success = True
                break
        
        if not candidate_login_success:
            print(f"   ⚠️  Candidate demo user not found or password unknown")
            # This is not a failure since candidate user might not be seeded
        
        return len(self.auth_tokens) >= 2  # At least admin and recruiter should work

    def test_user_registration(self):
        """Test new user registration"""
        print("\n" + "="*60)
        print("4. USER REGISTRATION TESTING")
        print("="*60)
        
        # Test new user registration
        test_user_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "full_name": "Test User Registration",
            "password": "testpass123",
            "role": "candidate"
        }
        
        print(f"\n🔍 Testing New User Registration...")
        success, response = self.run_test(
            "New User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if success:
            print(f"   ✅ User registration successful")
            print(f"   User ID: {response.get('id', 'Unknown')}")
            print(f"   Email: {response.get('email', 'Unknown')}")
            print(f"   Role: {response.get('role', 'Unknown')}")
            
            # Test login with newly registered user
            login_data = {
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
            
            print(f"\n🔍 Testing Login with Newly Registered User...")
            success, login_response = self.run_test(
                "Login with New User",
                "POST",
                "auth/login",
                200,
                data=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if success and 'access_token' in login_response:
                print(f"   ✅ New user login successful")
                self.auth_tokens['new_user'] = login_response['access_token']
                return True
            else:
                print(f"   ❌ New user login failed")
                return False
        else:
            print(f"   ❌ User registration failed")
            return False

    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        print("\n" + "="*60)
        print("5. JWT TOKEN VALIDATION TESTING")
        print("="*60)
        
        if not self.auth_tokens:
            print(f"   ❌ No auth tokens available for testing")
            return False
        
        # Test /auth/me with valid token
        for role, token in self.auth_tokens.items():
            print(f"\n🔍 Testing /auth/me with {role} token...")
            
            headers = {'Authorization': f'Bearer {token}'}
            success, response = self.run_test(
                f"Get Current User Info ({role})",
                "GET",
                "auth/me",
                200,
                headers=headers
            )
            
            if success:
                print(f"   ✅ Token validation successful for {role}")
                print(f"   User: {response.get('full_name', 'Unknown')}")
                print(f"   Email: {response.get('email', 'Unknown')}")
                print(f"   Role: {response.get('role', 'Unknown')}")
            else:
                print(f"   ❌ Token validation failed for {role}")
                return False
        
        # Test with invalid token
        print(f"\n🔍 Testing with Invalid Token...")
        invalid_headers = {'Authorization': 'Bearer invalid-token-12345'}
        success, _ = self.run_test(
            "Invalid Token Test",
            "GET",
            "auth/me",
            401,  # Should fail
            headers=invalid_headers
        )
        
        # Test without token
        print(f"\n🔍 Testing without Token...")
        success, _ = self.run_test(
            "No Token Test",
            "GET",
            "auth/me",
            401  # Should fail
        )
        
        return True

    def test_protected_endpoints(self):
        """Test protected endpoints with and without authentication"""
        print("\n" + "="*60)
        print("6. PROTECTED ENDPOINTS TESTING")
        print("="*60)
        
        # Test endpoints that should require authentication
        protected_endpoints = [
            ("GET", "jobs", "Get Jobs"),
            ("GET", "candidates", "Get Candidates"),
            ("POST", "job", "Create Job"),
            ("POST", "resume", "Upload Resume"),
            ("GET", "users", "Get Users (Admin only)")
        ]
        
        print(f"\n🔍 Testing Protected Endpoints WITHOUT Authentication...")
        for method, endpoint, description in protected_endpoints:
            success, _ = self.run_test(
                f"{description} (No Auth - Should Fail)",
                method,
                endpoint,
                401,  # Should fail with 401 or 403
                data={} if method == "POST" else None
            )
        
        # Test with valid authentication
        if 'recruiter' in self.auth_tokens:
            print(f"\n🔍 Testing Protected Endpoints WITH Recruiter Authentication...")
            recruiter_headers = {'Authorization': f'Bearer {self.auth_tokens["recruiter"]}'}
            
            # Test jobs endpoint (should work for recruiter)
            success, response = self.run_test(
                "Get Jobs (Recruiter Auth)",
                "GET",
                "jobs",
                200,
                headers=recruiter_headers
            )
            
            if success:
                print(f"   ✅ Jobs endpoint accessible with recruiter auth")
                print(f"   Found {len(response)} jobs")
            
            # Test candidates endpoint (should work for recruiter)
            success, response = self.run_test(
                "Get Candidates (Recruiter Auth)",
                "GET",
                "candidates",
                200,
                headers=recruiter_headers
            )
            
            if success:
                print(f"   ✅ Candidates endpoint accessible with recruiter auth")
                print(f"   Found {len(response)} candidates")
        
        return True

    def test_authentication_edge_cases(self):
        """Test authentication edge cases and error scenarios"""
        print("\n" + "="*60)
        print("7. AUTHENTICATION EDGE CASES TESTING")
        print("="*60)
        
        # Test invalid email format
        print(f"\n🔍 Testing Invalid Email Format...")
        invalid_email_data = {
            "email": "invalid-email-format",
            "password": "password123"
        }
        
        success, _ = self.run_test(
            "Login with Invalid Email Format",
            "POST",
            "auth/login",
            401,  # Should fail
            data=invalid_email_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Test empty credentials
        print(f"\n🔍 Testing Empty Credentials...")
        empty_data = {
            "email": "",
            "password": ""
        }
        
        success, _ = self.run_test(
            "Login with Empty Credentials",
            "POST",
            "auth/login",
            422,  # Should fail with validation error
            data=empty_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Test wrong password for valid user
        print(f"\n🔍 Testing Wrong Password...")
        wrong_password_data = {
            "email": "admin@jobmatcher.com",
            "password": "wrongpassword123"
        }
        
        success, _ = self.run_test(
            "Login with Wrong Password",
            "POST",
            "auth/login",
            401,  # Should fail
            data=wrong_password_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Test malformed JSON
        print(f"\n🔍 Testing Malformed Request...")
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                data="invalid json data",
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            print(f"   Malformed JSON Status: {response.status_code}")
            if response.status_code in [400, 422]:
                print(f"   ✅ Properly handles malformed JSON")
                self.log_test_result("Malformed JSON Handling", True, f"Status: {response.status_code}")
            else:
                print(f"   ⚠️  Unexpected status for malformed JSON: {response.status_code}")
                self.log_test_result("Malformed JSON Handling", False, f"Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error testing malformed JSON: {e}")
            self.log_test_result("Malformed JSON Handling", False, f"Exception: {e}")
        
        return True

    def test_database_connectivity(self):
        """Test if backend can connect to database and has demo users"""
        print("\n" + "="*60)
        print("8. DATABASE CONNECTIVITY TESTING")
        print("="*60)
        
        if 'admin' not in self.auth_tokens:
            print(f"   ❌ No admin token available for database tests")
            return False
        
        # Test getting all users (admin only)
        print(f"\n🔍 Testing Database User Query...")
        admin_headers = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        success, response = self.run_test(
            "Get All Users (Database Test)",
            "GET",
            "users",
            200,
            headers=admin_headers
        )
        
        if success:
            print(f"   ✅ Database connectivity working")
            print(f"   Found {len(response)} users in database")
            
            # Check for demo users
            demo_users = []
            for user in response:
                email = user.get('email', '')
                if email in ['admin@jobmatcher.com', 'recruiter@jobmatcher.com', 'candidate@jobmatcher.com']:
                    demo_users.append(f"{user.get('full_name', 'Unknown')} ({email})")
            
            if demo_users:
                print(f"   ✅ Demo users found:")
                for demo_user in demo_users:
                    print(f"     - {demo_user}")
            else:
                print(f"   ⚠️  No demo users found in database")
            
            return True
        else:
            print(f"   ❌ Database connectivity test failed")
            return False

    def test_api_endpoint_routing(self):
        """Test that API endpoints are properly routed with /api prefix"""
        print("\n" + "="*60)
        print("9. API ENDPOINT ROUTING TESTING")
        print("="*60)
        
        # Test various endpoints to ensure /api prefix is working
        endpoints_to_test = [
            ("GET", "", "Root endpoint"),
            ("POST", "auth/login", "Login endpoint"),
            ("POST", "auth/register", "Register endpoint"),
            ("GET", "auth/me", "Current user endpoint"),
        ]
        
        print(f"\n🔍 Testing API Endpoint Routing...")
        for method, endpoint, description in endpoints_to_test:
            full_url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
            print(f"   Testing: {description} -> {full_url}")
            
            try:
                if method == "GET":
                    response = requests.get(full_url, timeout=10)
                else:
                    response = requests.post(full_url, json={}, timeout=10)
                
                # We expect various status codes, but not 404 (which would indicate routing issues)
                if response.status_code != 404:
                    print(f"     ✅ Endpoint routed correctly (Status: {response.status_code})")
                else:
                    print(f"     ❌ Endpoint not found (404) - routing issue")
                    self.log_test_result(f"Routing - {description}", False, "404 Not Found")
                    
            except Exception as e:
                print(f"     ❌ Error testing endpoint: {e}")
                self.log_test_result(f"Routing - {description}", False, f"Exception: {e}")
        
        return True

    def run_comprehensive_auth_tests(self):
        """Run all authentication-focused tests"""
        print("🚀 STARTING COMPREHENSIVE BACKEND AUTHENTICATION TESTING")
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"🔗 API Base URL: {self.api_url}")
        print("="*80)
        
        test_functions = [
            self.test_health_check,
            self.test_cors_configuration,
            self.test_demo_user_authentication,
            self.test_user_registration,
            self.test_jwt_token_validation,
            self.test_protected_endpoints,
            self.test_authentication_edge_cases,
            self.test_database_connectivity,
            self.test_api_endpoint_routing
        ]
        
        failed_tests = []
        
        for test_func in test_functions:
            try:
                result = test_func()
                if not result:
                    failed_tests.append(test_func.__name__)
            except Exception as e:
                print(f"\n❌ Test {test_func.__name__} failed with exception: {e}")
                failed_tests.append(test_func.__name__)
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE AUTHENTICATION TEST RESULTS")
        print("="*80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Test Functions:")
            for test in failed_tests:
                print(f"   - {test}")
        
        print(f"\n🔐 Authentication Tokens Obtained:")
        for role, token in self.auth_tokens.items():
            print(f"   - {role}: {token[:20]}...")
        
        # Detailed test results
        print(f"\n📋 DETAILED TEST RESULTS:")
        passed_tests = [r for r in self.test_results if r['success']]
        failed_test_results = [r for r in self.test_results if not r['success']]
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                print(f"   ✅ {test['name']}: {test['details']}")
        
        if failed_test_results:
            print(f"\n❌ FAILED TESTS ({len(failed_test_results)}):")
            for test in failed_test_results:
                print(f"   ❌ {test['name']}: {test['details']}")
        
        # Critical issues summary
        print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
        critical_issues = []
        
        if not any('Demo Admin Login' in r['name'] and r['success'] for r in self.test_results):
            critical_issues.append("Admin demo user login failing")
        
        if not any('Demo Recruiter Login' in r['name'] and r['success'] for r in self.test_results):
            critical_issues.append("Recruiter demo user login failing")
        
        if not any('CORS Configuration' in r['name'] and r['success'] for r in self.test_results):
            critical_issues.append("CORS configuration issues")
        
        if not any('Get Jobs (Recruiter Auth)' in r['name'] and r['success'] for r in self.test_results):
            critical_issues.append("Protected endpoints not accessible with valid auth")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"   🚨 {issue}")
        else:
            print(f"   ✅ No critical authentication issues found")
        
        return len(failed_tests) == 0

def main():
    """Main function to run authentication tests"""
    tester = BackendAuthTester()
    success = tester.run_comprehensive_auth_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())