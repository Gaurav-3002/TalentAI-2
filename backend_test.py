import requests
import sys
import json
from datetime import datetime
import os

class JobMatchingAPITester:
    def __init__(self, base_url="https://cd03202a-fe69-421e-96bf-700c52b040ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_candidates = []
        self.created_jobs = []
        self.auth_tokens = {}  # Store tokens for different users
        self.created_users = []  # Track created test users

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, form_data=False, auth_token=None):
        """Run a single API test with optional authentication"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        # Add authentication header if token provided
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_token:
            print(f"   Auth: Bearer token provided")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files or form_data:
                    # Send as form data (multipart/form-data)
                    response = requests.post(url, data=data, files=files, headers=headers)
                elif data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
                else:
                    response = requests.post(url, headers=headers)
            elif method == 'PUT':
                if data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.put(url, json=data, headers=headers)
                else:
                    response = requests.put(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   Created ID: {response_data['id']}")
                    elif isinstance(response_data, list):
                        print(f"   Returned {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_seeded_users(self):
        """Test that default admin and recruiter accounts exist and can login"""
        print("\n" + "="*50)
        print("TESTING SEEDED USERS")
        print("="*50)
        
        # Test admin login
        admin_credentials = {
            "email": "admin@jobmatcher.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Login with seeded admin account",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['admin'] = response['access_token']
            print(f"   Admin user: {response['user']['full_name']} ({response['user']['role']})")
        
        # Test recruiter login
        recruiter_credentials = {
            "email": "recruiter@jobmatcher.com", 
            "password": "recruiter123"
        }
        
        success, response = self.run_test(
            "Login with seeded recruiter account",
            "POST", 
            "auth/login",
            200,
            data=recruiter_credentials
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['recruiter'] = response['access_token']
            print(f"   Recruiter user: {response['user']['full_name']} ({response['user']['role']})")

    def test_authentication_system(self):
        """Test user registration, login, and JWT token validation"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATION SYSTEM")
        print("="*50)
        
        # Test user registration
        test_user_data = {
            "email": "testcandidate@example.com",
            "full_name": "Test Candidate User",
            "password": "testpass123",
            "role": "candidate"
        }
        
        success, response = self.run_test(
            "User registration",
            "POST",
            "auth/register", 
            200,
            data=test_user_data
        )
        
        if success:
            self.created_users.append(response['id'])
            print(f"   Registered user: {response['full_name']} ({response['role']})")
        
        # Test duplicate registration (should fail)
        success, _ = self.run_test(
            "Duplicate user registration",
            "POST",
            "auth/register",
            400,  # Should fail with 400
            data=test_user_data
        )
        
        # Test user login
        login_data = {
            "email": "testcandidate@example.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['candidate'] = response['access_token']
            print(f"   Login successful, token received")
            print(f"   User: {response['user']['full_name']} ({response['user']['role']})")
        
        # Test invalid login
        invalid_login = {
            "email": "testcandidate@example.com",
            "password": "wrongpassword"
        }
        
        success, _ = self.run_test(
            "Invalid login attempt",
            "POST",
            "auth/login",
            401,  # Should fail with 401
            data=invalid_login
        )

    def test_jwt_token_validation(self):
        """Test JWT token validation and current user endpoint"""
        print("\n" + "="*50)
        print("TESTING JWT TOKEN VALIDATION")
        print("="*50)
        
        # Test /auth/me with valid token
        if 'candidate' in self.auth_tokens:
            success, response = self.run_test(
                "Get current user info (valid token)",
                "GET",
                "auth/me",
                200,
                auth_token=self.auth_tokens['candidate']
            )
            
            if success:
                print(f"   Current user: {response.get('full_name')} ({response.get('role')})")
        
        # Test /auth/me without token (should fail)
        success, _ = self.run_test(
            "Get current user info (no token)",
            "GET", 
            "auth/me",
            401  # Should fail with 401
        )
        
        # Test /auth/me with invalid token (should fail)
        success, _ = self.run_test(
            "Get current user info (invalid token)",
            "GET",
            "auth/me", 
            401,  # Should fail with 401
            auth_token="invalid-token-12345"
        )

    def test_role_based_access_control(self):
        """Test role-based access control for different endpoints"""
        print("\n" + "="*50)
        print("TESTING ROLE-BASED ACCESS CONTROL")
        print("="*50)
        
        # Test admin-only endpoint: get all users
        if 'admin' in self.auth_tokens:
            success, response = self.run_test(
                "Get all users (admin access)",
                "GET",
                "users",
                200,
                auth_token=self.auth_tokens['admin']
            )
            
            if success:
                print(f"   Admin can access users list: {len(response)} users found")
        
        # Test recruiter trying to access admin-only endpoint (should fail)
        if 'recruiter' in self.auth_tokens:
            success, _ = self.run_test(
                "Get all users (recruiter access - should fail)",
                "GET",
                "users",
                403,  # Should fail with 403
                auth_token=self.auth_tokens['recruiter']
            )
        
        # Test candidate trying to access admin-only endpoint (should fail)
        if 'candidate' in self.auth_tokens:
            success, _ = self.run_test(
                "Get all users (candidate access - should fail)",
                "GET",
                "users",
                403,  # Should fail with 403
                auth_token=self.auth_tokens['candidate']
            )
        
        # Test role update (admin only)
        if 'admin' in self.auth_tokens and self.created_users:
            user_id = self.created_users[0]
            success, response = self.run_test(
                "Update user role (admin access)",
                "PUT",
                f"users/{user_id}/role?new_role=recruiter",
                200,
                auth_token=self.auth_tokens['admin']
            )

    def test_user_management(self):
        """Test user management endpoints"""
        print("\n" + "="*50)
        print("TESTING USER MANAGEMENT")
        print("="*50)
        
        # Test getting current user info
        if 'admin' in self.auth_tokens:
            success, response = self.run_test(
                "Get current user info (admin)",
                "GET",
                "auth/me",
                200,
                auth_token=self.auth_tokens['admin']
            )
            
            if success:
                print(f"   Admin user info: {response.get('full_name')} ({response.get('role')})")
        
        # Test getting all users (admin only)
        if 'admin' in self.auth_tokens:
            success, users = self.run_test(
                "Get all users (admin only)",
                "GET",
                "users",
                200,
                auth_token=self.auth_tokens['admin']
            )
            
            if success:
                print(f"   Found {len(users)} total users in system")
                for user in users[:3]:  # Show first 3 users
                    print(f"   User: {user.get('full_name')} ({user.get('role')}) - {user.get('email')}")

    def test_protected_endpoints(self):
        """Test that protected endpoints require proper authentication and roles"""
        print("\n" + "="*50)
        print("TESTING PROTECTED ENDPOINTS")
        print("="*50)
        
        # Test resume upload without authentication (should fail)
        resume_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'resume_text': 'Test resume content',
        }
        
        success, _ = self.run_test(
            "Resume upload without auth (should fail)",
            "POST",
            "resume",
            401,  # Should fail with 401
            data=resume_data,
            form_data=True
        )
        
        # Test job creation without authentication (should fail)
        job_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'required_skills': ['Python'],
            'description': 'Test job description'
        }
        
        success, _ = self.run_test(
            "Job creation without auth (should fail)",
            "POST",
            "job",
            401,  # Should fail with 401
            data=job_data
        )
        
        # Test candidate search without authentication (should fail)
        success, _ = self.run_test(
            "Candidate search without auth (should fail)",
            "GET",
            "search?job_id=test-id&k=10",
            401  # Should fail with 401
        )
        
        # Test job creation with candidate role (should fail)
        if 'candidate' in self.auth_tokens:
            success, _ = self.run_test(
                "Job creation with candidate role (should fail)",
                "POST",
                "job",
                403,  # Should fail with 403 (forbidden)
                data=job_data,
                auth_token=self.auth_tokens['candidate']
            )

    def test_resume_upload_authenticated(self):
        """Test resume upload with proper authentication"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATED RESUME UPLOAD")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping authenticated resume tests")
            return
        
        # Test case 1: High-skill candidate
        resume_data = {
            'name': 'Alice Johnson',
            'email': 'alice.johnson@example.com',
            'resume_text': '''
            Senior Full Stack Developer with 8 years of experience in JavaScript, React, Node.js, Python, 
            MongoDB, AWS, Docker, and machine learning. Expert in building scalable web applications.
            Education: Master's in Computer Science from Stanford University.
            ''',
            'skills': 'JavaScript, React, Node.js, Python, MongoDB, AWS, Docker, Machine Learning',
            'experience_years': 8,
            'education': "Master's in Computer Science"
        }
        
        success, response = self.run_test(
            "Upload high-skill resume (authenticated)", 
            "POST", 
            "resume", 
            200, 
            data=resume_data,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   Extracted skills: {response.get('extracted_skills', [])}")
            print(f"   Experience years: {response.get('experience_years', 0)}")
        
        # Test case 2: Marketing candidate
        resume_data_marketing = {
            'name': 'Bob Smith',
            'email': 'bob.smith@example.com',
            'resume_text': '''
            Marketing Manager with 5 years of experience in social media campaigns, 
            content creation, and brand management. Strong communication skills.
            Education: Bachelor's in Marketing.
            ''',
            'skills': 'Marketing, Social Media, Content Creation',
            'experience_years': 5,
            'education': "Bachelor's in Marketing"
        }
        
        success, response = self.run_test(
            "Upload marketing resume (authenticated)", 
            "POST", 
            "resume", 
            200, 
            data=resume_data_marketing,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])

    def test_job_posting_authenticated(self):
        """Test job posting creation with proper authentication"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATED JOB POSTING")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping authenticated job tests")
            return
        
        # Test case 1: Senior Full Stack Developer job
        job_data = {
            'title': 'Senior Full Stack Developer',
            'company': 'Tech Innovations Inc',
            'required_skills': ['JavaScript', 'React', 'Node.js', 'Python', 'MongoDB', 'AWS'],
            'location': 'San Francisco, CA',
            'salary': '$120,000 - $160,000',
            'description': '''
            We are looking for a Senior Full Stack Developer with expertise in modern web technologies.
            The ideal candidate should have experience with JavaScript, React, Node.js, Python, MongoDB, and AWS.
            Minimum 5 years of experience required.
            ''',
            'min_experience_years': 5
        }
        
        success, response = self.run_test(
            "Create senior developer job (authenticated)", 
            "POST", 
            "job", 
            200, 
            data=job_data,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'id' in response:
            self.created_jobs.append(response['id'])
            print(f"   Required skills: {response.get('required_skills', [])}")
            print(f"   Min experience: {response.get('min_experience_years', 0)} years")

    def test_access_logging(self):
        """Test access logging functionality"""
        print("\n" + "="*50)
        print("TESTING ACCESS LOGGING")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping access logging tests")
            return
        
        # Test candidate search (should create access logs)
        if self.created_jobs:
            job_id = self.created_jobs[0]
            success, results = self.run_test(
                "Candidate search (creates access logs)",
                "GET",
                f"search?job_id={job_id}&k=5",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   Search completed, should have created access logs for {len(results)} candidates")
        
        # Test viewing specific candidate (should create access log)
        if self.created_candidates:
            candidate_id = self.created_candidates[0]
            success, response = self.run_test(
                "View candidate profile (creates access log)",
                "GET",
                f"candidates/{candidate_id}",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   Viewed candidate: {response.get('name')}")
        
        # Test retrieving access logs
        success, logs = self.run_test(
            "Get access logs",
            "GET",
            "access-logs?limit=10",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print(f"   Retrieved {len(logs)} access log entries")
            if logs:
                latest_log = logs[0]
                print(f"   Latest log: {latest_log.get('access_reason')} - {latest_log.get('candidate_name')}")
        
        # Test creating manual access log
        if self.created_candidates:
            log_data = {
                "candidate_id": self.created_candidates[0],
                "access_reason": "evaluation",
                "access_details": "Manual evaluation for position"
            }
            
            success, response = self.run_test(
                "Create manual access log",
                "POST",
                "access-logs",
                200,
                data=log_data,
                auth_token=self.auth_tokens['recruiter']
            )

    def test_pii_redaction_blind_screening(self):
        """Test PII redaction and blind screening functionality"""
        print("\n" + "="*50)
        print("TESTING PII REDACTION & BLIND SCREENING")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping PII redaction tests")
            return
        
        # Test candidate search with blind screening
        if self.created_jobs:
            job_id = self.created_jobs[0]
            success, results = self.run_test(
                "Candidate search with blind screening",
                "GET",
                f"search?job_id={job_id}&k=5&blind_screening=true",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success and results:
                print(f"   Blind search returned {len(results)} candidates")
                for i, result in enumerate(results[:2]):
                    print(f"   Candidate {i+1}: {result['candidate_name']} | {result['candidate_email']}")
                    # Check if PII is redacted (should contain *** or be shortened)
                    if '***' in result['candidate_name'] or '***' in result['candidate_email']:
                        print(f"   ✅ PII properly redacted")
                    else:
                        print(f"   ⚠️  PII may not be redacted")
        
        # Test candidate viewing with blind mode
        if self.created_candidates:
            candidate_id = self.created_candidates[0]
            success, response = self.run_test(
                "View candidate with blind mode",
                "GET",
                f"candidates/{candidate_id}?blind_mode=true",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   Blind mode candidate: {response.get('name')} | {response.get('email')}")
                if '***' in response.get('name', '') or '***' in response.get('email', ''):
                    print(f"   ✅ PII properly redacted in blind mode")
                else:
                    print(f"   ⚠️  PII may not be redacted in blind mode")
        
        # Test regular candidate list with blind mode
        success, candidates = self.run_test(
            "Get candidates list with blind mode",
            "GET",
            "candidates?blind_mode=true",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and candidates:
            print(f"   Retrieved {len(candidates)} candidates in blind mode")

    def test_candidate_search_authenticated(self):
        """Test candidate search and matching with authentication"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATED CANDIDATE SEARCH")
        print("="*50)
        
        if not self.created_jobs:
            print("❌ No jobs created, skipping search tests")
            return
            
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping search tests")
            return
        
        # Test search for senior developer position
        job_id = self.created_jobs[0]  # Senior Full Stack Developer
        success, results = self.run_test(
            "Search candidates for senior role (authenticated)", 
            "GET", 
            f"search?job_id={job_id}&k=10", 
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and results:
            print(f"   Found {len(results)} matching candidates")
            print("\n   📊 RANKING RESULTS:")
            for i, result in enumerate(results[:3]):  # Show top 3
                print(f"   #{i+1} {result['candidate_name']}")
                print(f"      Total Score: {result['total_score']:.3f}")
                print(f"      Semantic: {result['semantic_score']:.3f}")
                print(f"      Skill Overlap: {result['skill_overlap_score']:.3f}")
                print(f"      Experience: {result['experience_match_score']:.3f}")
                print(f"      Matched Skills: {result['score_breakdown']['matched_skills']}")
                print(f"      Missing Skills: {result['score_breakdown']['missing_skills']}")
                print()

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n" + "="*50)
        print("TESTING BASIC ENDPOINTS")
        print("="*50)
        
        # Test root endpoint
        success, _ = self.run_test("Root endpoint", "GET", "", 200)
        
        # Test candidates endpoint without auth (should fail)
        success, _ = self.run_test("Get candidates without auth (should fail)", "GET", "candidates", 401)
            
        # Test jobs endpoint without auth (should fail)
        success, _ = self.run_test("Get jobs without auth (should fail)", "GET", "jobs", 401)

    def test_individual_endpoints_authenticated(self):
        """Test individual candidate and job retrieval with authentication"""
        print("\n" + "="*50)
        print("TESTING INDIVIDUAL ENDPOINTS (AUTHENTICATED)")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping individual endpoint tests")
            return
        
        # Test individual candidate retrieval
        if self.created_candidates:
            candidate_id = self.created_candidates[0]
            success, candidate = self.run_test(
                "Get individual candidate (authenticated)", 
                "GET", 
                f"candidates/{candidate_id}", 
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   Retrieved: {candidate.get('name', 'Unknown')}")
        
        # Test individual job retrieval
        if self.created_jobs:
            job_id = self.created_jobs[0]
            success, job = self.run_test(
                "Get individual job (authenticated)", 
                "GET", 
                f"jobs/{job_id}", 
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   Retrieved: {job.get('title', 'Unknown')}")
        
        # Test candidates list endpoint
        success, candidates = self.run_test(
            "Get all candidates (authenticated)",
            "GET",
            "candidates",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print(f"   Retrieved {len(candidates)} candidates from list endpoint")
        
        # Test jobs list endpoint  
        success, jobs = self.run_test(
            "Get all jobs (authenticated)",
            "GET",
            "jobs",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print(f"   Retrieved {len(jobs)} jobs from list endpoint")

    def test_error_cases(self):
        """Test error handling with authentication"""
        print("\n" + "="*50)
        print("TESTING ERROR CASES")
        print("="*50)
        
        # Test resume upload without required fields (with auth)
        if 'recruiter' in self.auth_tokens:
            success, _ = self.run_test(
                "Resume upload without name (authenticated)", 
                "POST", 
                "resume", 
                422,  # Validation error
                data={'email': 'test@example.com'},
                form_data=True,
                auth_token=self.auth_tokens['recruiter']
            )
        
        # Test search with invalid job ID (with auth)
        if 'recruiter' in self.auth_tokens:
            success, _ = self.run_test(
                "Search with invalid job ID (authenticated)", 
                "GET", 
                "search?job_id=invalid-id&k=10", 
                404,
                auth_token=self.auth_tokens['recruiter']
            )
        
        # Test get non-existent candidate (with auth)
        if 'recruiter' in self.auth_tokens:
            success, _ = self.run_test(
                "Get non-existent candidate (authenticated)", 
                "GET", 
                "candidates/non-existent-id", 
                404,
                auth_token=self.auth_tokens['recruiter']
            )

    def run_all_tests(self):
        """Run all tests including Sprint 6 security features"""
        print("🚀 Starting Job Matching API Tests - Sprint 6 Security Features")
        print(f"🌐 Base URL: {self.base_url}")
        
        try:
            # Sprint 6 Security Tests (Priority Order)
            self.test_seeded_users()
            self.test_authentication_system()
            self.test_jwt_token_validation()
            self.test_role_based_access_control()
            self.test_user_management()
            self.test_protected_endpoints()
            
            # Authenticated functionality tests
            self.test_resume_upload_authenticated()
            self.test_job_posting_authenticated()
            self.test_access_logging()
            self.test_pii_redaction_blind_screening()
            self.test_candidate_search_authenticated()
            
            # Basic functionality tests
            self.test_basic_endpoints()
            self.test_individual_endpoints_authenticated()
            self.test_error_cases()
            
            # Print final results
            print("\n" + "="*60)
            print("📊 FINAL TEST RESULTS - SPRINT 6 SECURITY")
            print("="*60)
            print(f"Tests Run: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            print(f"Tests Failed: {self.tests_run - self.tests_passed}")
            print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            if self.created_users:
                print(f"\n👥 Created {len(self.created_users)} test users")
            if self.created_candidates:
                print(f"📝 Created {len(self.created_candidates)} test candidates")
            if self.created_jobs:
                print(f"💼 Created {len(self.created_jobs)} test jobs")
            if self.auth_tokens:
                print(f"🔐 Authenticated as {len(self.auth_tokens)} different user roles")
            
            return self.tests_passed == self.tests_run
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {str(e)}")
            return False

def main():
    tester = JobMatchingAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())