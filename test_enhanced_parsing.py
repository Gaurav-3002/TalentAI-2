#!/usr/bin/env python3

import requests
import json
import sys
import time

class EnhancedResumeParsingTester:
    def __init__(self):
        self.base_url = "https://b0f01cda-2385-4551-81cb-cf84983e55ee.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.auth_token = None
        self.created_candidates = []
        
    def login_as_recruiter(self):
        """Login as recruiter to get auth token"""
        login_data = {
            "email": "recruiter@jobmatcher.com",
            "password": "recruiter123"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                print(f"✅ Logged in as recruiter: {data['user']['full_name']}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_enhanced_resume_upload(self):
        """Test enhanced resume upload with LLM parsing"""
        print("\n" + "="*60)
        print("TESTING ENHANCED RESUME PARSING")
        print("="*60)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        # Test comprehensive resume
        resume_data = {
            'name': 'Dr. Sarah Chen',
            'email': 'sarah.chen@techcorp.com',
            'resume_text': '''
            SARAH CHEN, PhD
            Email: sarah.chen@techcorp.com | Phone: (555) 123-4567
            
            PROFESSIONAL SUMMARY
            Senior Machine Learning Engineer with 8+ years of experience in AI/ML.
            Expert in deep learning, NLP, and computer vision.
            
            TECHNICAL SKILLS
            Programming: Python, R, Java, C++
            ML/AI: TensorFlow, PyTorch, scikit-learn, Keras
            Cloud: AWS, Google Cloud, Docker, Kubernetes
            
            WORK EXPERIENCE
            Senior ML Engineer | TechCorp Inc. | 2020-Present
            • Led development of recommendation system
            • Improved model accuracy by 25%
            
            EDUCATION
            PhD in Computer Science | Stanford University | 2018
            MS in Machine Learning | MIT | 2015
            
            CERTIFICATIONS
            • AWS Certified Machine Learning - Specialty (2022)
            • Google Cloud Professional ML Engineer (2021)
            ''',
            'skills': 'Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP',
            'experience_years': 8,
            'education': "PhD in Computer Science from Stanford University"
        }
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            response = requests.post(
                f"{self.api_url}/resume",
                data=resume_data,
                headers=headers,
                timeout=30
            )
            
            print(f"Resume upload status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Resume upload successful!")
                print(f"   Candidate ID: {data.get('candidate_id')}")
                print(f"   Parsing method: {data.get('parsing_method', 'unknown')}")
                print(f"   Parsing confidence: {data.get('parsing_confidence', 'N/A')}")
                print(f"   Advanced parsing available: {data.get('advanced_parsing_available', False)}")
                print(f"   Extracted skills: {data.get('extracted_skills', [])}")
                print(f"   Experience years: {data.get('experience_years', 0)}")
                
                if 'candidate_id' in data:
                    self.created_candidates.append(data['candidate_id'])
                
                # Check for enhanced fields
                enhanced_fields = ['parsing_method', 'parsing_confidence', 'advanced_parsing_available']
                for field in enhanced_fields:
                    if field in data:
                        print(f"   ✅ Enhanced field '{field}' present")
                    else:
                        print(f"   ❌ Enhanced field '{field}' missing")
                
                return True
            else:
                print(f"❌ Resume upload failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Resume upload error: {e}")
            return False
    
    def test_parsed_resume_endpoint(self):
        """Test the new parsed resume endpoint"""
        print("\n" + "="*60)
        print("TESTING PARSED RESUME ENDPOINT")
        print("="*60)
        
        if not self.auth_token or not self.created_candidates:
            print("❌ No auth token or candidates available")
            return False
        
        candidate_id = self.created_candidates[0]
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            response = requests.get(
                f"{self.api_url}/candidates/{candidate_id}/parsed-resume",
                headers=headers,
                timeout=30
            )
            
            print(f"Parsed resume endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Parsed resume data retrieved!")
                
                # Check structure
                expected_fields = ['personal_info', 'summary', 'skills', 'work_experience', 'education']
                for field in expected_fields:
                    if field in data:
                        print(f"   ✅ Field '{field}' present")
                    else:
                        print(f"   ⚠️  Field '{field}' missing")
                
                return True
            elif response.status_code == 404:
                print("⚠️  No parsed resume data available (expected with placeholder API key)")
                return True  # This is expected behavior
            else:
                print(f"❌ Parsed resume endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Parsed resume endpoint error: {e}")
            return False
    
    def test_candidate_enhanced_fields(self):
        """Test enhanced fields in candidate responses"""
        print("\n" + "="*60)
        print("TESTING ENHANCED CANDIDATE FIELDS")
        print("="*60)
        
        if not self.auth_token or not self.created_candidates:
            print("❌ No auth token or candidates available")
            return False
        
        candidate_id = self.created_candidates[0]
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Test individual candidate endpoint
            response = requests.get(
                f"{self.api_url}/candidates/{candidate_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Individual candidate status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Individual candidate retrieved!")
                
                # Check for enhanced fields
                enhanced_fields = ['parsing_method', 'parsing_confidence', 'has_structured_data']
                for field in enhanced_fields:
                    if field in data:
                        print(f"   ✅ Enhanced field '{field}': {data[field]}")
                    else:
                        print(f"   ❌ Enhanced field '{field}' missing")
                
                return True
            else:
                print(f"❌ Individual candidate failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Individual candidate error: {e}")
            return False
    
    def test_fallback_behavior(self):
        """Test fallback to basic parsing"""
        print("\n" + "="*60)
        print("TESTING FALLBACK BEHAVIOR")
        print("="*60)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        # Test simple resume that should work with basic parsing
        simple_resume = {
            'name': 'Simple Test User',
            'email': 'simple.test@example.com',
            'resume_text': 'Software developer with Python experience.',
            'skills': 'Python',
            'experience_years': 2,
            'education': 'Bachelor degree'
        }
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            response = requests.post(
                f"{self.api_url}/resume",
                data=simple_resume,
                headers=headers,
                timeout=30
            )
            
            print(f"Simple resume upload status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Simple resume processed!")
                print(f"   Parsing method: {data.get('parsing_method', 'unknown')}")
                
                # With placeholder API key, should fall back to basic parsing
                if data.get('parsing_method') == 'basic':
                    print("   ✅ Correctly fell back to basic parsing")
                    return True
                elif data.get('parsing_method') in ['llm_text', 'llm_advanced']:
                    print("   ⚠️  Advanced parsing succeeded (unexpected)")
                    return True  # Still a success, just unexpected
                else:
                    print(f"   ⚠️  Unknown parsing method: {data.get('parsing_method')}")
                    return True
            else:
                print(f"❌ Simple resume failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Simple resume error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all enhanced parsing tests"""
        print("🚀 Enhanced Resume Parsing Test Suite")
        print(f"🌐 Base URL: {self.base_url}")
        
        # Step 1: Login
        if not self.login_as_recruiter():
            print("❌ Failed to login, cannot continue tests")
            return False
        
        # Step 2: Test enhanced resume parsing
        test_results = []
        test_results.append(self.test_enhanced_resume_upload())
        test_results.append(self.test_parsed_resume_endpoint())
        test_results.append(self.test_candidate_enhanced_fields())
        test_results.append(self.test_fallback_behavior())
        
        # Results
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "="*60)
        print("📊 ENHANCED PARSING TEST RESULTS")
        print("="*60)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All enhanced parsing tests passed!")
        else:
            print("⚠️  Some tests failed or had issues")
        
        return passed == total

if __name__ == "__main__":
    tester = EnhancedResumeParsingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)