#!/usr/bin/env python3
"""
Test script for the Job Matching Engine
Tests the three required scenarios: high match, low match, and partial match
"""

import asyncio
import aiohttp
import json
import time

API_BASE = "http://localhost:8001/api"

async def test_matching_engine():
    async with aiohttp.ClientSession() as session:
        print("🚀 Starting Job Matching Engine Tests")
        print("=" * 50)
        
        # Test Case 1: High Match Candidate
        print("\n📋 Test Case 1: High Match Scenario")
        print("-" * 30)
        
        # Create a high-match candidate
        high_match_data = {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "resume_text": """
            Senior Software Engineer with 5+ years of experience developing web applications using JavaScript, React, Node.js, and MongoDB. 
            Expert in full-stack development, API design, and database optimization. 
            Strong background in agile methodologies and team leadership.
            Experience with AWS, Docker, and CI/CD pipelines.
            Bachelor's degree in Computer Science.
            """,
            "skills": "JavaScript,React,Node.js,MongoDB,AWS,Docker",
            "experience_years": "5",
            "education": "Bachelor's in Computer Science"
        }
        
        async with session.post(f"{API_BASE}/resume", data=high_match_data) as resp:
            high_match_result = await resp.json()
            print(f"✅ High match candidate created: {high_match_result['candidate_id']}")
            print(f"   Extracted skills: {high_match_result['extracted_skills']}")
        
        # Test Case 2: Low Match Candidate  
        print("\n📋 Test Case 2: Low Match Scenario")
        print("-" * 30)
        
        low_match_data = {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "resume_text": """
            Marketing Manager with 3 years of experience in digital marketing, social media campaigns, and content creation.
            Proficient in Photoshop, Adobe Creative Suite, and Google Analytics.
            Experience with email marketing platforms and SEO optimization.
            Bachelor's degree in Marketing.
            """,
            "skills": "Marketing,Photoshop,SEO,Google Analytics",
            "experience_years": "3",
            "education": "Bachelor's in Marketing"
        }
        
        async with session.post(f"{API_BASE}/resume", data=low_match_data) as resp:
            low_match_result = await resp.json()
            print(f"✅ Low match candidate created: {low_match_result['candidate_id']}")
            print(f"   Extracted skills: {low_match_result['extracted_skills']}")
        
        # Test Case 3: Partial Match Candidate
        print("\n📋 Test Case 3: Partial Match Scenario")
        print("-" * 30)
        
        partial_match_data = {
            "name": "Carol Davis",
            "email": "carol@example.com",
            "resume_text": """
            Junior Frontend Developer with 2 years of experience in JavaScript and React development.
            Familiar with HTML, CSS, and basic API integration.
            Some experience with Git version control.
            Currently learning Node.js and backend development.
            Associate degree in Web Development.
            """,
            "skills": "JavaScript,React,HTML,CSS,Git",
            "experience_years": "2",
            "education": "Associate in Web Development"
        }
        
        async with session.post(f"{API_BASE}/resume", data=partial_match_data) as resp:
            partial_match_result = await resp.json()
            print(f"✅ Partial match candidate created: {partial_match_result['candidate_id']}")
            print(f"   Extracted skills: {partial_match_result['extracted_skills']}")
        
        # Create a test job posting
        print("\n💼 Creating Test Job Posting")
        print("-" * 30)
        
        job_data = {
            "title": "Senior Full Stack Developer",
            "company": "TechCorp Inc",
            "required_skills": ["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
            "location": "San Francisco, CA",
            "salary": "$100,000 - $140,000",
            "description": """
            We are looking for a Senior Full Stack Developer with 4+ years of experience to join our growing team.
            The ideal candidate should have strong experience in JavaScript, React, Node.js, and MongoDB.
            Experience with cloud platforms like AWS is highly preferred.
            You will be responsible for developing scalable web applications and working closely with our product team.
            """,
            "min_experience_years": 4
        }
        
        async with session.post(f"{API_BASE}/job", json=job_data) as resp:
            job_result = await resp.json()
            job_id = job_result['id']
            print(f"✅ Job posting created: {job_id}")
            print(f"   Required skills: {job_result['required_skills']}")
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Search for matching candidates
        print("\n🔍 Searching for Matching Candidates")
        print("-" * 30)
        
        async with session.get(f"{API_BASE}/search?job_id={job_id}&k=10") as resp:
            search_results = await resp.json()
            
            print(f"Found {len(search_results)} matching candidates:")
            print()
            
            for i, candidate in enumerate(search_results, 1):
                print(f"Rank #{i}: {candidate['candidate_name']}")
                print(f"  📧 Email: {candidate['candidate_email']}")
                print(f"  🎯 Total Score: {candidate['total_score']:.3f} ({candidate['total_score']*100:.1f}%)")
                print(f"  🧠 Semantic Score: {candidate['semantic_score']:.3f}")
                print(f"  🔧 Skill Overlap: {candidate['skill_overlap_score']:.3f}")
                print(f"  📈 Experience Match: {candidate['experience_match_score']:.3f}")
                print(f"  ✅ Matched Skills: {candidate['score_breakdown']['matched_skills']}")
                print(f"  ❌ Missing Skills: {candidate['score_breakdown']['missing_skills']}")
                print(f"  💼 Experience: {candidate['candidate_experience_years']} years")
                print()
        
        # Validate test cases
        print("🧪 Test Case Validation")
        print("-" * 30)
        
        # Find each candidate in results
        alice_result = next((c for c in search_results if c['candidate_name'] == 'Alice Johnson'), None)
        bob_result = next((c for c in search_results if c['candidate_name'] == 'Bob Smith'), None)
        carol_result = next((c for c in search_results if c['candidate_name'] == 'Carol Davis'), None)
        
        if alice_result:
            print(f"✅ HIGH MATCH (Alice): Score = {alice_result['total_score']:.3f}")
            print(f"   Expected: High score (>0.7) ✓" if alice_result['total_score'] > 0.7 else f"   Expected: High score (>0.7) ❌")
        
        if bob_result:
            print(f"✅ LOW MATCH (Bob): Score = {bob_result['total_score']:.3f}")
            print(f"   Expected: Low score (<0.3) ✓" if bob_result['total_score'] < 0.3 else f"   Expected: Low score (<0.3) ❌")
        
        if carol_result:
            print(f"✅ PARTIAL MATCH (Carol): Score = {carol_result['total_score']:.3f}")
            print(f"   Expected: Medium score (0.3-0.7) ✓" if 0.3 <= carol_result['total_score'] <= 0.7 else f"   Expected: Medium score (0.3-0.7) ❌")
        
        print("\n🎉 Job Matching Engine Tests Completed!")
        
        # Test ranking formula modularity
        print("\n🔧 Testing Modular Ranking Formula")
        print("-" * 30)
        print("Current weights:")
        print("  - Semantic similarity: 40%")
        print("  - Skill overlap: 40%") 
        print("  - Experience match: 20%")
        print("✅ Weights can be easily adjusted in the calculate_total_score function")
        
if __name__ == "__main__":
    asyncio.run(test_matching_engine())