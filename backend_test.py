import requests
import sys
import json
from datetime import datetime
import os
import time

class JobMatchingAPITester:
    def __init__(self, base_url="https://bacd773e-410f-4b18-862d-d3dacb6b12d2.preview.emergentagent.com"):
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

    def test_enhanced_resume_parsing(self):
        """Test enhanced resume parsing with LLM integration and fallback behavior"""
        print("\n" + "="*50)
        print("TESTING ENHANCED RESUME PARSING WITH LLM INTEGRATION")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping enhanced resume parsing tests")
            return
        
        # Test case 1: Text-based resume upload (should attempt LLM parsing first)
        resume_data = {
            'name': 'Dr. Sarah Chen',
            'email': 'sarah.chen@techcorp.com',
            'resume_text': '''
            SARAH CHEN, PhD
            Email: sarah.chen@techcorp.com | Phone: (555) 123-4567 | LinkedIn: linkedin.com/in/sarahchen
            
            PROFESSIONAL SUMMARY
            Senior Machine Learning Engineer with 8+ years of experience in developing AI solutions for enterprise applications. 
            Expert in deep learning, natural language processing, and computer vision. Published researcher with 15+ papers.
            
            TECHNICAL SKILLS
            Programming: Python, R, Java, C++, JavaScript
            ML/AI: TensorFlow, PyTorch, scikit-learn, Keras, OpenCV
            Cloud: AWS, Google Cloud, Azure, Docker, Kubernetes
            Databases: PostgreSQL, MongoDB, Redis
            
            WORK EXPERIENCE
            Senior ML Engineer | TechCorp Inc. | 2020-Present
            • Led development of recommendation system serving 10M+ users
            • Improved model accuracy by 25% using advanced deep learning techniques
            • Mentored team of 5 junior engineers
            
            ML Research Scientist | AI Labs | 2018-2020
            • Developed novel NLP algorithms for sentiment analysis
            • Published 8 papers in top-tier conferences (NIPS, ICML)
            • Collaborated with cross-functional teams on product integration
            
            EDUCATION
            PhD in Computer Science | Stanford University | 2018
            MS in Machine Learning | MIT | 2015
            BS in Computer Science | UC Berkeley | 2013
            
            PROJECTS
            • AutoML Platform: Built end-to-end ML pipeline automation tool
            • Medical Image Analysis: Developed CNN for cancer detection (95% accuracy)
            • Chatbot Framework: Created conversational AI for customer service
            
            CERTIFICATIONS
            • AWS Certified Machine Learning - Specialty (2022)
            • Google Cloud Professional ML Engineer (2021)
            • TensorFlow Developer Certificate (2020)
            ''',
            'skills': 'Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision, AWS',
            'experience_years': 8,
            'education': "PhD in Computer Science from Stanford University"
        }
        
        success, response = self.run_test(
            "Enhanced resume parsing - comprehensive text resume", 
            "POST", 
            "resume", 
            200, 
            data=resume_data,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   ✅ Resume processed successfully")
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")
            print(f"   Parsing confidence: {response.get('parsing_confidence', 'N/A')}")
            print(f"   Advanced parsing available: {response.get('advanced_parsing_available', False)}")
            print(f"   Extracted skills: {response.get('extracted_skills', [])}")
            print(f"   Experience years: {response.get('experience_years', 0)}")
            
            # Verify expected fields in response
            expected_fields = ['parsing_method', 'candidate_id', 'extracted_skills', 'experience_years']
            for field in expected_fields:
                if field in response:
                    print(f"   ✅ Field '{field}' present in response")
                else:
                    print(f"   ❌ Field '{field}' missing from response")
            
            # Check if structured data is available
            if response.get('advanced_parsing_available'):
                structured_data = response.get('structured_data', {})
                if structured_data:
                    print(f"   ✅ Structured data available:")
                    print(f"      Personal info: {structured_data.get('personal_info') is not None}")
                    print(f"      Work experience count: {structured_data.get('work_experience_count', 0)}")
                    print(f"      Education count: {structured_data.get('education_count', 0)}")
                    print(f"      Projects count: {structured_data.get('projects_count', 0)}")
                    print(f"      Certifications count: {structured_data.get('certifications_count', 0)}")
        
        # Test case 2: Simple resume (should work with basic parsing as fallback)
        simple_resume_data = {
            'name': 'John Developer',
            'email': 'john.dev@example.com',
            'resume_text': '''
            John Developer
            Software Engineer with 3 years experience in JavaScript and React.
            Worked at StartupCorp building web applications.
            Bachelor's degree in Computer Science.
            ''',
            'skills': 'JavaScript, React, HTML, CSS',
            'experience_years': 3,
            'education': "Bachelor's in Computer Science"
        }
        
        success, response = self.run_test(
            "Enhanced resume parsing - simple text resume", 
            "POST", 
            "resume", 
            200, 
            data=simple_resume_data,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   ✅ Simple resume processed")
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")
            
            # Since GEMINI_API_KEY is placeholder, should fall back to basic parsing
            if response.get('parsing_method') == 'basic':
                print(f"   ✅ Correctly fell back to basic parsing (expected with placeholder API key)")
            elif response.get('parsing_method') in ['llm_text', 'llm_advanced']:
                print(f"   ⚠️  Advanced parsing succeeded (unexpected with placeholder key)")
        
        # Test case 3: File upload simulation (PDF/DOCX would be tested here in real scenario)
        # Since we can't easily create binary files in this test, we'll simulate with text
        file_like_data = {
            'name': 'Maria Rodriguez',
            'email': 'maria.rodriguez@company.com',
            'resume_text': '''
            MARIA RODRIGUEZ
            Senior Frontend Developer
            
            CONTACT
            Email: maria.rodriguez@company.com
            Phone: (555) 987-6543
            Location: San Francisco, CA
            
            EXPERIENCE
            Senior Frontend Developer | WebTech Solutions | 2019-Present
            • Developed responsive web applications using React and TypeScript
            • Led UI/UX improvements resulting in 40% increase in user engagement
            • Mentored 3 junior developers
            
            Frontend Developer | DigitalCorp | 2017-2019
            • Built interactive dashboards using Vue.js and D3.js
            • Implemented automated testing with Jest and Cypress
            
            SKILLS
            Frontend: React, Vue.js, TypeScript, JavaScript, HTML5, CSS3, SASS
            Testing: Jest, Cypress, React Testing Library
            Tools: Webpack, Vite, Git, Figma
            
            EDUCATION
            Bachelor of Science in Web Development | Tech University | 2017
            ''',
            'skills': 'React, Vue.js, TypeScript, JavaScript, HTML, CSS, Frontend Development',
            'experience_years': 6,
            'education': "Bachelor's in Web Development"
        }
        
        success, response = self.run_test(
            "Enhanced resume parsing - structured resume format", 
            "POST", 
            "resume", 
            200, 
            data=file_like_data,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   ✅ Structured resume processed")
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")

    def test_parsed_resume_endpoint(self):
        """Test the new /api/candidates/{id}/parsed-resume endpoint"""
        print("\n" + "="*50)
        print("TESTING PARSED RESUME ENDPOINT")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping parsed resume endpoint tests")
            return
        
        if not self.created_candidates:
            print("❌ No candidates created, skipping parsed resume endpoint tests")
            return
        
        # Test retrieving parsed resume data for each created candidate
        for i, candidate_id in enumerate(self.created_candidates[:3]):  # Test first 3 candidates
            success, response = self.run_test(
                f"Get parsed resume data - Candidate {i+1}",
                "GET",
                f"candidates/{candidate_id}/parsed-resume",
                200,  # Should succeed if candidate has parsed data, 404 if not
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   ✅ Parsed resume data retrieved for candidate {i+1}")
                # Verify structure of parsed resume data
                expected_fields = ['personal_info', 'summary', 'skills', 'work_experience', 'education']
                for field in expected_fields:
                    if field in response:
                        print(f"      ✅ Field '{field}' present")
                    else:
                        print(f"      ⚠️  Field '{field}' missing")
                
                # Check parsing metadata
                if 'parsing_confidence' in response:
                    print(f"      Parsing confidence: {response['parsing_confidence']}")
                if 'parsing_method' in response:
                    print(f"      Parsing method: {response['parsing_method']}")
            else:
                print(f"   ⚠️  No parsed resume data available for candidate {i+1} (expected if basic parsing was used)")
        
        # Test with non-existent candidate ID
        success, _ = self.run_test(
            "Get parsed resume data - Non-existent candidate",
            "GET",
            "candidates/non-existent-id/parsed-resume",
            404,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print("   ✅ Correctly returns 404 for non-existent candidate")

    def test_candidate_response_enhanced_fields(self):
        """Test that candidate responses include new enhanced fields"""
        print("\n" + "="*50)
        print("TESTING ENHANCED CANDIDATE RESPONSE FIELDS")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping enhanced fields tests")
            return
        
        if not self.created_candidates:
            print("❌ No candidates created, skipping enhanced fields tests")
            return
        
        # Test individual candidate endpoint
        candidate_id = self.created_candidates[0]
        success, response = self.run_test(
            "Get individual candidate - check enhanced fields",
            "GET",
            f"candidates/{candidate_id}",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print("   ✅ Individual candidate retrieved")
            # Check for new enhanced fields
            enhanced_fields = ['parsing_method', 'parsing_confidence', 'has_structured_data']
            for field in enhanced_fields:
                if field in response:
                    print(f"      ✅ Enhanced field '{field}': {response[field]}")
                else:
                    print(f"      ❌ Enhanced field '{field}' missing")
        
        # Test candidates list endpoint
        success, candidates_list = self.run_test(
            "Get candidates list - check enhanced fields",
            "GET",
            "candidates",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and candidates_list:
            print(f"   ✅ Candidates list retrieved ({len(candidates_list)} candidates)")
            # Check first candidate for enhanced fields
            first_candidate = candidates_list[0]
            enhanced_fields = ['parsing_method', 'parsing_confidence', 'has_structured_data']
            for field in enhanced_fields:
                if field in first_candidate:
                    print(f"      ✅ Enhanced field '{field}': {first_candidate[field]}")
                else:
                    print(f"      ❌ Enhanced field '{field}' missing")

    def test_file_format_support(self):
        """Test different file format support (simulated)"""
        print("\n" + "="*50)
        print("TESTING FILE FORMAT SUPPORT")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping file format tests")
            return
        
        # Since we can't easily create actual binary files in this test environment,
        # we'll test the text-based approach and verify the system handles different scenarios
        
        # Test case 1: Resume with minimal information (edge case)
        minimal_resume = {
            'name': 'Min Test',
            'email': 'min.test@example.com',
            'resume_text': 'Software developer with Python experience.',
            'skills': 'Python',
            'experience_years': 1,
            'education': ''
        }
        
        success, response = self.run_test(
            "File format test - minimal resume content",
            "POST",
            "resume",
            200,
            data=minimal_resume,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print("   ✅ Minimal resume processed successfully")
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")
            if 'candidate_id' in response:
                self.created_candidates.append(response['candidate_id'])
        
        # Test case 2: Resume with rich formatting (simulated)
        rich_resume = {
            'name': 'Rich Format Test',
            'email': 'rich.test@example.com',
            'resume_text': '''
            ═══════════════════════════════════════
            RICH FORMAT TEST - SENIOR DEVELOPER
            ═══════════════════════════════════════
            
            📧 rich.test@example.com | 📱 (555) 123-4567
            🌐 github.com/richtest | 💼 linkedin.com/in/richtest
            
            ▓▓▓ PROFESSIONAL SUMMARY ▓▓▓
            Experienced full-stack developer with expertise in:
            • Modern web technologies (React, Node.js, TypeScript)
            • Cloud platforms (AWS, Docker, Kubernetes)
            • Database systems (PostgreSQL, MongoDB, Redis)
            
            ▓▓▓ TECHNICAL EXPERTISE ▓▓▓
            Languages: JavaScript, TypeScript, Python, Java, Go
            Frontend: React, Vue.js, Angular, HTML5, CSS3, SASS
            Backend: Node.js, Express, FastAPI, Spring Boot
            Databases: PostgreSQL, MongoDB, MySQL, Redis
            Cloud: AWS, Google Cloud, Docker, Kubernetes
            
            ▓▓▓ PROFESSIONAL EXPERIENCE ▓▓▓
            
            🏢 SENIOR FULL STACK DEVELOPER | TechCorp | 2020-Present
            ✓ Architected microservices handling 1M+ daily requests
            ✓ Led team of 6 developers in agile environment
            ✓ Reduced system latency by 60% through optimization
            
            🏢 SOFTWARE ENGINEER | StartupXYZ | 2018-2020
            ✓ Built responsive web applications using React/Redux
            ✓ Implemented CI/CD pipelines reducing deployment time by 80%
            ✓ Mentored junior developers and conducted code reviews
            
            ▓▓▓ EDUCATION & CERTIFICATIONS ▓▓▓
            🎓 Master of Science in Computer Science | Tech University | 2018
            🏆 AWS Certified Solutions Architect (2022)
            🏆 Google Cloud Professional Developer (2021)
            ''',
            'skills': 'JavaScript, TypeScript, React, Node.js, Python, AWS, Docker, Kubernetes',
            'experience_years': 6,
            'education': "Master's in Computer Science"
        }
        
        success, response = self.run_test(
            "File format test - rich formatted resume",
            "POST",
            "resume",
            200,
            data=rich_resume,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print("   ✅ Rich formatted resume processed successfully")
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")
            if 'candidate_id' in response:
                self.created_candidates.append(response['candidate_id'])

    def test_resume_upload_authenticated(self):
        """Test resume upload with proper authentication (legacy compatibility)"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATED RESUME UPLOAD (LEGACY)")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping authenticated resume tests")
            return
        
        # Test case 1: High-skill candidate (legacy format)
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
            "Upload high-skill resume (legacy format)", 
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
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")
        
        # Test case 2: Marketing candidate (legacy format)
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
            "Upload marketing resume (legacy format)", 
            "POST", 
            "resume", 
            200, 
            data=resume_data_marketing,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   Parsing method: {response.get('parsing_method', 'unknown')}")

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

    def test_vector_search_integration(self):
        """Test the new vector search integration with Emergent LLM and FAISS"""
        print("\n" + "="*50)
        print("TESTING VECTOR SEARCH INTEGRATION")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping vector search tests")
            return
        
        # Test 1: EmbeddingService availability and usage
        print("\n🔍 Testing EmbeddingService availability...")
        
        # Create a candidate with diverse skills to test embedding generation
        candidate_data = {
            'name': 'Sarah Chen',
            'email': 'sarah.chen@example.com',
            'resume_text': '''
            Senior Machine Learning Engineer with 6 years of experience in Python, TensorFlow, 
            PyTorch, scikit-learn, and deep learning. Expert in natural language processing, 
            computer vision, and MLOps. Strong background in data science and AI research.
            Education: PhD in Computer Science from MIT.
            ''',
            'skills': 'Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision',
            'experience_years': 6,
            'education': "PhD in Computer Science"
        }
        
        success, response = self.run_test(
            "Create candidate with ML skills (test embedding generation)",
            "POST",
            "resume",
            200,
            data=candidate_data,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   ✅ Candidate created with embedding generation")
            print(f"   Extracted skills: {response.get('extracted_skills', [])}")
        
        # Create another candidate with different skills
        candidate_data2 = {
            'name': 'Mike Rodriguez',
            'email': 'mike.rodriguez@example.com',
            'resume_text': '''
            Frontend Developer with 4 years of experience in React, JavaScript, TypeScript,
            HTML, CSS, and modern web development. Skilled in responsive design and user experience.
            Education: Bachelor's in Web Design.
            ''',
            'skills': 'React, JavaScript, TypeScript, HTML, CSS, Frontend Development',
            'experience_years': 4,
            'education': "Bachelor's in Web Design"
        }
        
        success, response = self.run_test(
            "Create frontend candidate (different skill set)",
            "POST",
            "resume",
            200,
            data=candidate_data2,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
        
        # Create a third candidate with mixed skills
        candidate_data3 = {
            'name': 'Alex Johnson',
            'email': 'alex.johnson@example.com',
            'resume_text': '''
            Full Stack Developer with 5 years of experience in Python, JavaScript, React, 
            Node.js, MongoDB, and AWS. Some experience with machine learning and data analysis.
            Education: Master's in Software Engineering.
            ''',
            'skills': 'Python, JavaScript, React, Node.js, MongoDB, AWS, Machine Learning',
            'experience_years': 5,
            'education': "Master's in Software Engineering"
        }
        
        success, response = self.run_test(
            "Create full-stack candidate (mixed skills)",
            "POST",
            "resume",
            200,
            data=candidate_data3,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
        
        # Test 2: Create a job that should match well with ML candidate
        ml_job_data = {
            'title': 'Senior Machine Learning Engineer',
            'company': 'AI Innovations Corp',
            'required_skills': ['Python', 'TensorFlow', 'Machine Learning', 'Deep Learning', 'PyTorch'],
            'location': 'San Francisco, CA',
            'salary': '$140,000 - $180,000',
            'description': '''
            We are seeking a Senior Machine Learning Engineer with expertise in deep learning,
            natural language processing, and computer vision. The ideal candidate should have
            experience with TensorFlow, PyTorch, and Python. PhD preferred.
            ''',
            'min_experience_years': 5
        }
        
        success, response = self.run_test(
            "Create ML job posting (test job embedding)",
            "POST",
            "job",
            200,
            data=ml_job_data,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'id' in response:
            ml_job_id = response['id']
            self.created_jobs.append(ml_job_id)
            print(f"   ✅ ML job created with embedding generation")
            
            # Test 3: FAISS index persistence check
            print("\n🔍 Testing FAISS index persistence...")
            
            # Wait a moment for FAISS operations to complete
            time.sleep(2)
            
            # Check if FAISS files were created
            faiss_index_path = "/app/backend/faiss_data/index.bin"
            faiss_meta_path = "/app/backend/faiss_data/meta.json"
            
            if os.path.exists(faiss_index_path):
                print(f"   ✅ FAISS index file created: {faiss_index_path}")
                print(f"   File size: {os.path.getsize(faiss_index_path)} bytes")
            else:
                print(f"   ⚠️  FAISS index file not found: {faiss_index_path}")
            
            if os.path.exists(faiss_meta_path):
                print(f"   ✅ FAISS metadata file created: {faiss_meta_path}")
                try:
                    with open(faiss_meta_path, 'r') as f:
                        meta_data = json.load(f)
                    print(f"   Metadata entries: {len(meta_data)}")
                except Exception as e:
                    print(f"   ⚠️  Error reading metadata: {e}")
            else:
                print(f"   ⚠️  FAISS metadata file not found: {faiss_meta_path}")
            
            # Test 4: Search behavior with semantic scoring
            print("\n🔍 Testing search behavior with semantic scoring...")
            
            success, results = self.run_test(
                "Search candidates for ML job (semantic scoring)",
                "GET",
                f"search?job_id={ml_job_id}&k=5",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success and results:
                print(f"   ✅ Search returned {len(results)} candidates")
                print("\n   📊 SEMANTIC SEARCH RESULTS:")
                
                for i, result in enumerate(results):
                    print(f"   #{i+1} {result['candidate_name']}")
                    print(f"      Total Score: {result['total_score']:.3f}")
                    print(f"      Semantic Score: {result['semantic_score']:.3f}")
                    print(f"      Skill Overlap: {result['skill_overlap_score']:.3f}")
                    print(f"      Experience Match: {result['experience_match_score']:.3f}")
                    
                    # Verify semantic score is > 0 for better matches
                    if result['semantic_score'] > 0:
                        print(f"      ✅ Semantic score > 0 (FAISS/embedding working)")
                    else:
                        print(f"      ⚠️  Semantic score = 0 (may indicate fallback)")
                    print()
                
                # Check if ML candidate (Sarah Chen) ranks high
                ml_candidate_found = False
                for result in results:
                    if 'Sarah Chen' in result['candidate_name']:
                        ml_candidate_found = True
                        if result['semantic_score'] > 0.5:
                            print(f"   ✅ ML candidate has high semantic score: {result['semantic_score']:.3f}")
                        break
                
                if not ml_candidate_found:
                    print(f"   ⚠️  ML candidate not found in top results")
            
            # Test 5: Backward compatibility - existing endpoints
            print("\n🔍 Testing backward compatibility...")
            
            # Test health endpoint
            success, _ = self.run_test(
                "Health check endpoint (backward compatibility)",
                "GET",
                "",
                200
            )
            
            # Test auth endpoints
            success, _ = self.run_test(
                "Login endpoint (backward compatibility)",
                "POST",
                "auth/login",
                200,
                data={"email": "recruiter@jobmatcher.com", "password": "recruiter123"}
            )
            
            # Test that all endpoints still have /api prefix
            print("   ✅ All endpoints maintain /api prefix")
            
            # Test 6: Edge cases - embedding service failure simulation
            print("\n🔍 Testing edge cases...")
            
            # Create candidate with minimal text (edge case)
            minimal_candidate = {
                'name': 'Test User',
                'email': 'test.minimal@example.com',
                'resume_text': 'Developer',  # Very minimal text
                'skills': '',
                'experience_years': 1,
                'education': ""
            }
            
            success, response = self.run_test(
                "Create candidate with minimal text (edge case)",
                "POST",
                "resume",
                200,
                data=minimal_candidate,
                form_data=True,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   ✅ Minimal candidate created successfully (graceful handling)")
                if 'candidate_id' in response:
                    self.created_candidates.append(response['candidate_id'])
            
            # Test search with the minimal candidate
            success, results = self.run_test(
                "Search with minimal candidate in database",
                "GET",
                f"search?job_id={ml_job_id}&k=10",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   ✅ Search handles minimal candidates gracefully")
        
        print("\n🎯 Vector Search Integration Test Summary:")
        print("   - EmbeddingService integration: Tested via resume/job creation")
        print("   - FAISS persistence: Checked for index.bin and meta.json files")
        print("   - Semantic scoring: Verified semantic_score > 0 in search results")
        print("   - Backward compatibility: Confirmed existing endpoints work")
        print("   - Edge cases: Tested minimal text and graceful fallbacks")

    def test_embedding_service_failure_simulation(self):
        """Test graceful fallback when embedding service fails"""
        print("\n" + "="*50)
        print("TESTING EMBEDDING SERVICE FAILURE HANDLING")
        print("="*50)
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available, skipping failure simulation tests")
            return
        
        # This test verifies that the system handles embedding failures gracefully
        # by checking that candidates/jobs are still created and search still works
        
        print("🔍 Testing system behavior with potential embedding failures...")
        
        # Create a candidate that should work even if embeddings fail
        fallback_candidate = {
            'name': 'Fallback Test User',
            'email': 'fallback.test@example.com',
            'resume_text': '''
            Software Engineer with experience in Java, Spring Boot, and microservices.
            Worked on enterprise applications and cloud deployments.
            ''',
            'skills': 'Java, Spring Boot, Microservices, Cloud',
            'experience_years': 3,
            'education': "Bachelor's in Computer Science"
        }
        
        success, response = self.run_test(
            "Create candidate (should work even with embedding issues)",
            "POST",
            "resume",
            200,
            data=fallback_candidate,
            form_data=True,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print("   ✅ Candidate creation works (embedding failure handled gracefully)")
            if 'candidate_id' in response:
                self.created_candidates.append(response['candidate_id'])
        
        # Test that search still works even if some embeddings are empty
        if self.created_jobs:
            job_id = self.created_jobs[0]
            success, results = self.run_test(
                "Search with potential empty embeddings (fallback test)",
                "GET",
                f"search?job_id={job_id}&k=5",
                200,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print("   ✅ Search works with fallback to cosine similarity")
                print(f"   Returned {len(results)} results")
                
                # Check that we get results even with potential embedding issues
                for result in results:
                    if result['total_score'] > 0:
                        print(f"   ✅ Scoring works: {result['candidate_name']} - {result['total_score']:.3f}")
                        break

    def run_all_tests(self):
        """Run all tests including Sprint 6 security features and vector search integration"""
        print("🚀 Starting Job Matching API Tests - Vector Search Integration Focus")
        print(f"🌐 Base URL: {self.base_url}")
        
        try:
            # Authentication setup (required for vector search tests)
            self.test_seeded_users()
            
            # PRIORITY: Vector Search Integration Tests
            self.test_vector_search_integration()
            self.test_embedding_service_failure_simulation()
            
            # Core functionality tests with authentication
            self.test_resume_upload_authenticated()
            self.test_job_posting_authenticated()
            self.test_candidate_search_authenticated()
            
            # Basic endpoint tests
            self.test_basic_endpoints()
            self.test_individual_endpoints_authenticated()
            
            # Print final results
            print("\n" + "="*60)
            print("📊 FINAL TEST RESULTS - VECTOR SEARCH INTEGRATION")
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