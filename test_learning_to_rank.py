#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

class LearningToRankTester:
    def __init__(self, base_url="https://2f068322-787b-4e47-ad72-4bf2eb859f45.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_tokens = {}
        self.created_candidates = []
        self.created_jobs = []

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
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

    def setup_authentication(self):
        """Setup authentication tokens"""
        print("🔐 Setting up authentication...")
        
        # Login as admin
        admin_credentials = {
            "email": "admin@jobmatcher.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin login",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['admin'] = response['access_token']
            print(f"   ✅ Admin authenticated")
        
        # Login as recruiter
        recruiter_credentials = {
            "email": "recruiter@jobmatcher.com",
            "password": "recruiter123"
        }
        
        success, response = self.run_test(
            "Recruiter login",
            "POST",
            "auth/login",
            200,
            data=recruiter_credentials
        )
        
        if success and 'access_token' in response:
            self.auth_tokens['recruiter'] = response['access_token']
            print(f"   ✅ Recruiter authenticated")

    def create_test_data(self):
        """Create test candidates and jobs"""
        print("\n📝 Creating test data...")
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token, skipping test data creation")
            return
        
        # Create test candidate
        candidate_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'resume_text': 'Software Engineer with 5 years experience in Python, JavaScript, React, and machine learning.',
            'skills': 'Python, JavaScript, React, Machine Learning',
            'experience_years': 5,
            'education': "Bachelor's in Computer Science"
        }
        
        success, response = self.run_test(
            "Create test candidate",
            "POST",
            "resume",
            200,
            data=candidate_data,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'candidate_id' in response:
            self.created_candidates.append(response['candidate_id'])
            print(f"   ✅ Created candidate: {response['candidate_id']}")
        
        # Create test job
        job_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'required_skills': ['Python', 'JavaScript', 'React'],
            'location': 'San Francisco, CA',
            'salary': '$120,000 - $150,000',
            'description': 'Looking for a senior software engineer with Python and React experience.',
            'min_experience_years': 3
        }
        
        success, response = self.run_test(
            "Create test job",
            "POST",
            "job",
            200,
            data=job_data,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and 'id' in response:
            self.created_jobs.append(response['id'])
            print(f"   ✅ Created job: {response['id']}")

    def test_learning_endpoints(self):
        """Test Learning-to-Rank endpoints"""
        print("\n🧠 Testing Learning-to-Rank endpoints...")
        
        if 'recruiter' not in self.auth_tokens:
            print("❌ No recruiter token available")
            return
        
        # Test 1: Get current weights
        success, response = self.run_test(
            "Get current optimal weights",
            "GET",
            "learning/weights",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success:
            print(f"   Weights: semantic={response.get('semantic_weight')}, "
                  f"skill={response.get('skill_weight')}, "
                  f"experience={response.get('experience_weight')}")
            print(f"   Confidence: {response.get('confidence_score')}")
            print(f"   Interactions: {response.get('interaction_count')}")
        
        # Test 2: Record interaction
        if self.created_candidates and self.created_jobs:
            interaction_data = {
                "candidate_id": self.created_candidates[0],
                "job_id": self.created_jobs[0],
                "interaction_type": "click",
                "search_position": 1,
                "session_id": "test-session-123"
            }
            
            success, response = self.run_test(
                "Record recruiter interaction",
                "POST",
                "interactions",
                201,
                data=interaction_data,
                auth_token=self.auth_tokens['recruiter']
            )
            
            if success:
                print(f"   ✅ Interaction recorded: {response.get('interaction_id')}")
        
        # Test 3: Get metrics (admin only)
        if 'admin' in self.auth_tokens:
            success, response = self.run_test(
                "Get learning metrics (admin)",
                "GET",
                "learning/metrics",
                200,
                auth_token=self.auth_tokens['admin']
            )
            
            if success:
                print(f"   Total interactions: {response.get('total_interactions')}")
                print(f"   Learning status: {response.get('learning_status')}")
        
        # Test 4: Trigger retraining (admin only)
        if 'admin' in self.auth_tokens:
            success, response = self.run_test(
                "Trigger manual retraining (admin)",
                "POST",
                "learning/retrain",
                200,
                auth_token=self.auth_tokens['admin']
            )
            
            if success:
                print(f"   ✅ Retraining completed")

    def test_dynamic_search(self):
        """Test search with dynamic weights"""
        print("\n🔍 Testing dynamic search weights...")
        
        if 'recruiter' not in self.auth_tokens or not self.created_jobs:
            print("❌ Missing requirements for search test")
            return
        
        job_id = self.created_jobs[0]
        success, results = self.run_test(
            "Search with dynamic weights",
            "GET",
            f"search?job_id={job_id}&k=5",
            200,
            auth_token=self.auth_tokens['recruiter']
        )
        
        if success and results:
            print(f"   ✅ Search returned {len(results)} candidates")
            
            if results:
                first_result = results[0]
                score_breakdown = first_result.get('score_breakdown', {})
                
                semantic_weight = score_breakdown.get('semantic_weight')
                skill_weight = score_breakdown.get('skill_overlap_weight')
                experience_weight = score_breakdown.get('experience_weight')
                
                if all(w is not None for w in [semantic_weight, skill_weight, experience_weight]):
                    print(f"   Dynamic weights in search:")
                    print(f"     Semantic: {semantic_weight}")
                    print(f"     Skill: {skill_weight}")
                    print(f"     Experience: {experience_weight}")
                    
                    total = semantic_weight + skill_weight + experience_weight
                    print(f"     Total: {total:.3f} (should be ~1.0)")
                else:
                    print(f"   ❌ Dynamic weights not found in score breakdown")

    def test_access_control(self):
        """Test access control for Learning-to-Rank endpoints"""
        print("\n🔒 Testing access control...")
        
        # Test without authentication
        success, _ = self.run_test(
            "Get weights without auth (should fail)",
            "GET",
            "learning/weights",
            401
        )
        
        success, _ = self.run_test(
            "Record interaction without auth (should fail)",
            "POST",
            "interactions",
            401,
            data={"candidate_id": "test", "job_id": "test", "interaction_type": "click"}
        )
        
        # Test recruiter trying to access admin endpoints
        if 'recruiter' in self.auth_tokens:
            success, _ = self.run_test(
                "Get metrics as recruiter (should fail)",
                "GET",
                "learning/metrics",
                403,
                auth_token=self.auth_tokens['recruiter']
            )
            
            success, _ = self.run_test(
                "Trigger retraining as recruiter (should fail)",
                "POST",
                "learning/retrain",
                403,
                auth_token=self.auth_tokens['recruiter']
            )

    def run_all_tests(self):
        """Run all Learning-to-Rank tests"""
        print("🚀 Learning-to-Rank Algorithm Testing")
        print("="*50)
        
        try:
            self.setup_authentication()
            self.create_test_data()
            self.test_learning_endpoints()
            self.test_dynamic_search()
            self.test_access_control()
            
            print("\n" + "="*50)
            print("📊 TEST RESULTS")
            print("="*50)
            print(f"Tests Run: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            print(f"Tests Failed: {self.tests_run - self.tests_passed}")
            print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            return self.tests_passed == self.tests_run
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {str(e)}")
            return False

if __name__ == "__main__":
    tester = LearningToRankTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)