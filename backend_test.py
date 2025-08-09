import requests
import sys
import json
from datetime import datetime
import os

class JobMatchingAPITester:
    def __init__(self, base_url="https://21e4e75d-b898-4ee0-84ee-aa314abed4c3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_candidates = []
        self.created_jobs = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files)
                elif data:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
                else:
                    response = requests.post(url, headers=headers)

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

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n" + "="*50)
        print("TESTING BASIC ENDPOINTS")
        print("="*50)
        
        # Test root endpoint
        success, _ = self.run_test("Root endpoint", "GET", "", 200)
        
        # Test candidates endpoint (should work even if empty)
        success, candidates = self.run_test("Get candidates", "GET", "candidates", 200)
        if success:
            print(f"   Found {len(candidates)} existing candidates")
            
        # Test jobs endpoint (should work even if empty)
        success, jobs = self.run_test("Get jobs", "GET", "jobs", 200)
        if success:
            print(f"   Found {len(jobs)} existing jobs")

    def test_resume_upload_text(self):
        """Test resume upload with text input"""
        print("\n" + "="*50)
        print("TESTING RESUME UPLOAD (TEXT)")
        print("="*50)
        
        # Test case 1: High-skill candidate (Alice Johnson equivalent)
        resume_data = {
            'name': 'Test Alice Johnson',
            'email': 'test.alice@example.com',
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
            "Upload high-skill resume", 
            "POST", 
            "resume", 
            200, 
            data=resume_data,
            files={}  # This will trigger form-data handling
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   Extracted skills: {response.get('extracted_skills', [])}")
            print(f"   Experience years: {response.get('experience_years', 0)}")
        
        # Test case 2: Low-skill candidate (Bob Smith equivalent)
        resume_data_low = {
            'name': 'Test Bob Smith',
            'email': 'test.bob@example.com',
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
            "Upload low-skill resume", 
            "POST", 
            "resume", 
            200, 
            data=resume_data_low,
            files={}
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
        
        # Test case 3: Partial-skill candidate (Carol Davis equivalent)
        resume_data_partial = {
            'name': 'Test Carol Davis',
            'email': 'test.carol@example.com',
            'resume_text': '''
            Junior Frontend Developer with 2 years of experience in HTML, CSS, JavaScript, 
            and React. Learning backend technologies.
            Education: Bachelor's in Computer Science.
            ''',
            'skills': 'HTML, CSS, JavaScript, React',
            'experience_years': 2,
            'education': "Bachelor's in Computer Science"
        }
        
        success, response = self.run_test(
            "Upload partial-skill resume", 
            "POST", 
            "resume", 
            200, 
            data=resume_data_partial,
            files={}
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])

    def test_job_posting(self):
        """Test job posting creation"""
        print("\n" + "="*50)
        print("TESTING JOB POSTING")
        print("="*50)
        
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
            "Create senior developer job", 
            "POST", 
            "job", 
            200, 
            data=job_data
        )
        
        if success and 'id' in response:
            self.created_jobs.append(response['id'])
            print(f"   Required skills: {response.get('required_skills', [])}")
            print(f"   Min experience: {response.get('min_experience_years', 0)} years")
        
        # Test case 2: Junior React Developer job
        job_data_junior = {
            'title': 'Junior React Developer',
            'company': 'StartupCorp',
            'required_skills': ['JavaScript', 'React', 'HTML', 'CSS'],
            'location': 'Remote',
            'salary': '$60,000 - $80,000',
            'description': '''
            Entry-level position for a React Developer. Perfect for recent graduates or 
            developers with 1-2 years of experience in frontend technologies.
            ''',
            'min_experience_years': 1
        }
        
        success, response = self.run_test(
            "Create junior developer job", 
            "POST", 
            "job", 
            200, 
            data=job_data_junior
        )
        
        if success and 'id' in response:
            self.created_jobs.append(response['id'])

    def test_candidate_search(self):
        """Test candidate search and matching"""
        print("\n" + "="*50)
        print("TESTING CANDIDATE SEARCH")
        print("="*50)
        
        if not self.created_jobs:
            print("❌ No jobs created, skipping search tests")
            return
        
        # Test search for senior developer position
        job_id = self.created_jobs[0]  # Senior Full Stack Developer
        success, results = self.run_test(
            "Search candidates for senior role", 
            "GET", 
            f"search?job_id={job_id}&k=10", 
            200
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
        
        # Test search with different k value
        if len(self.created_jobs) > 1:
            job_id = self.created_jobs[1]  # Junior React Developer
            success, results = self.run_test(
                "Search candidates for junior role", 
                "GET", 
                f"search?job_id={job_id}&k=5", 
                200
            )
            
            if success and results:
                print(f"   Found {len(results)} matching candidates for junior role")

    def test_individual_endpoints(self):
        """Test individual candidate and job retrieval"""
        print("\n" + "="*50)
        print("TESTING INDIVIDUAL ENDPOINTS")
        print("="*50)
        
        # Test individual candidate retrieval
        if self.created_candidates:
            candidate_id = self.created_candidates[0]
            success, candidate = self.run_test(
                "Get individual candidate", 
                "GET", 
                f"candidates/{candidate_id}", 
                200
            )
            
            if success:
                print(f"   Retrieved: {candidate.get('name', 'Unknown')}")
        
        # Test individual job retrieval
        if self.created_jobs:
            job_id = self.created_jobs[0]
            success, job = self.run_test(
                "Get individual job", 
                "GET", 
                f"jobs/{job_id}", 
                200
            )
            
            if success:
                print(f"   Retrieved: {job.get('title', 'Unknown')}")

    def test_error_cases(self):
        """Test error handling"""
        print("\n" + "="*50)
        print("TESTING ERROR CASES")
        print("="*50)
        
        # Test resume upload without required fields
        success, _ = self.run_test(
            "Resume upload without name", 
            "POST", 
            "resume", 
            422,  # Validation error
            data={'email': 'test@example.com'}
        )
        
        # Test search with invalid job ID
        success, _ = self.run_test(
            "Search with invalid job ID", 
            "GET", 
            "search?job_id=invalid-id&k=10", 
            404
        )
        
        # Test get non-existent candidate
        success, _ = self.run_test(
            "Get non-existent candidate", 
            "GET", 
            "candidates/non-existent-id", 
            404
        )

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Job Matching API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        
        try:
            self.test_basic_endpoints()
            self.test_resume_upload_text()
            self.test_job_posting()
            self.test_candidate_search()
            self.test_individual_endpoints()
            self.test_error_cases()
            
            # Print final results
            print("\n" + "="*60)
            print("📊 FINAL TEST RESULTS")
            print("="*60)
            print(f"Tests Run: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            print(f"Tests Failed: {self.tests_run - self.tests_passed}")
            print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            if self.created_candidates:
                print(f"\n📝 Created {len(self.created_candidates)} test candidates")
            if self.created_jobs:
                print(f"💼 Created {len(self.created_jobs)} test jobs")
            
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