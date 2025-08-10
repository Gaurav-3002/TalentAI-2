#!/usr/bin/env python3
"""
Script to add sample data to the job matching database
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models import Candidate, JobPosting
from server import normalize_skills, extract_experience_years

load_dotenv()

async def add_sample_data():
    """Add sample candidates and job postings"""
    
    # Connect to database
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Adding sample data to database...")
    
    # Sample candidates
    sample_candidates = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@email.com",
            "skills": ["JavaScript", "React", "Node.js", "TypeScript", "AWS"],
            "experience_years": 5,
            "education": "Bachelor's in Computer Science",
            "resume_text": "Experienced frontend developer with 5 years in React and JavaScript. Built scalable web applications using modern frameworks.",
            "parsing_method": "basic",
            "parsing_confidence": None,
            "created_by": "admin"
        },
        {
            "name": "Bob Smith",
            "email": "bob.smith@email.com",
            "skills": ["Python", "Django", "PostgreSQL", "Docker", "Machine Learning"],
            "experience_years": 7,
            "education": "Master's in Software Engineering",
            "resume_text": "Senior backend developer with expertise in Python and Django. Experience in ML model deployment and containerization.",
            "parsing_method": "basic",
            "parsing_confidence": None,
            "created_by": "admin"
        },
        {
            "name": "Carol Davis",
            "email": "carol.davis@email.com",
            "skills": ["Java", "Spring Boot", "Microservices", "Kubernetes", "MySQL"],
            "experience_years": 4,
            "education": "Bachelor's in Information Technology",
            "resume_text": "Full-stack Java developer with strong background in enterprise applications and microservices architecture.",
            "parsing_method": "basic",
            "parsing_confidence": None,
            "created_by": "admin"
        },
        {
            "name": "David Wilson",
            "email": "david.wilson@email.com",
            "skills": ["React Native", "Flutter", "iOS", "Android", "Firebase"],
            "experience_years": 3,
            "education": "Bachelor's in Computer Engineering",
            "resume_text": "Mobile app developer specializing in cross-platform development with React Native and Flutter.",
            "parsing_method": "basic",
            "parsing_confidence": None
        },
        {
            "name": "Emma Thompson",
            "email": "emma.thompson@email.com",
            "skills": ["Data Science", "Python", "TensorFlow", "SQL", "R"],
            "experience_years": 6,
            "education": "PhD in Data Science",
            "resume_text": "Data scientist with extensive experience in machine learning, statistical analysis, and predictive modeling.",
            "parsing_method": "basic",
            "parsing_confidence": None
        }
    ]
    
    # Sample job postings
    sample_jobs = [
        {
            "title": "Senior Frontend Developer",
            "company": "TechCorp Inc.",
            "location": "San Francisco, CA",
            "description": "We are looking for an experienced frontend developer to join our growing team. You will be responsible for building user-facing features using React and modern JavaScript.",
            "required_skills": ["JavaScript", "React", "TypeScript", "CSS", "Git"],
            "min_experience_years": 3,
            "salary": "$120,000 - $160,000",
            "created_by": "admin"
        },
        {
            "title": "Python Backend Engineer",
            "company": "DataFlow Solutions",
            "location": "New York, NY",
            "description": "Join our backend team to build scalable APIs and microservices. Experience with Python, Django, and cloud platforms required.",
            "required_skills": ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
            "min_experience_years": 4,
            "salary": "$130,000 - $170,000",
            "created_by": "admin"
        },
        {
            "title": "Full Stack Java Developer",
            "company": "Enterprise Systems Ltd.",
            "location": "Austin, TX",
            "description": "Looking for a full-stack developer with strong Java skills to work on enterprise applications and microservices.",
            "required_skills": ["Java", "Spring Boot", "MySQL", "Angular", "Kubernetes"],
            "min_experience_years": 3,
            "salary": "$110,000 - $150,000",
            "created_by": "admin"
        },
        {
            "title": "Mobile App Developer",
            "company": "MobileFirst Studios",
            "location": "Seattle, WA",
            "description": "Build amazing mobile applications for iOS and Android platforms. Experience with React Native or Flutter preferred.",
            "required_skills": ["React Native", "JavaScript", "iOS", "Android", "Firebase"],
            "min_experience_years": 2,
            "salary": "$100,000 - $140,000",
            "created_by": "admin"
        },
        {
            "title": "Data Scientist",
            "company": "AI Innovations",
            "location": "Boston, MA",
            "description": "Apply machine learning and statistical analysis to solve complex business problems. PhD or Master's degree preferred.",
            "required_skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Statistics"],
            "min_experience_years": 4,
            "salary": "$140,000 - $180,000",
            "created_by": "admin"
        }
    ]
    
    # Check if data already exists
    existing_candidates = await db.candidates.count_documents({})
    existing_jobs = await db.job_postings.count_documents({})
    
    if existing_candidates > 5:
        print(f"Found {existing_candidates} candidates, skipping candidate creation")
    else:
        print("Adding sample candidates...")
        for candidate_data in sample_candidates:
            # Normalize skills
            candidate_data["skills"] = normalize_skills(candidate_data["skills"])
            
            # Create candidate object
            candidate = Candidate(**candidate_data)
            
            # Check if candidate already exists
            existing = await db.candidates.find_one({"email": candidate.email})
            if not existing:
                await db.candidates.insert_one(candidate.dict())
                print(f"Added candidate: {candidate.name}")
            else:
                print(f"Candidate {candidate.name} already exists")
    
    if existing_jobs > 5:
        print(f"Found {existing_jobs} jobs, skipping job creation")
    else:
        print("Adding sample job postings...")
        for job_data in sample_jobs:
            # Normalize skills
            job_data["required_skills"] = normalize_skills(job_data["required_skills"])
            
            # Create job object
            job = JobPosting(**job_data)
            
            # Check if job already exists
            existing = await db.job_postings.find_one({"title": job.title, "company": job.company})
            if not existing:
                await db.job_postings.insert_one(job.dict())
                print(f"Added job: {job.title} at {job.company}")
            else:
                print(f"Job {job.title} at {job.company} already exists")
    
    # Print final counts
    total_candidates = await db.candidates.count_documents({})
    total_jobs = await db.job_postings.count_documents({})
    print(f"\nDatabase now contains:")
    print(f"  - {total_candidates} candidates")
    print(f"  - {total_jobs} job postings")
    
    client.close()
    print("Sample data added successfully!")

if __name__ == "__main__":
    asyncio.run(add_sample_data())