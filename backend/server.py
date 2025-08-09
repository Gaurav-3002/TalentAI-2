from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Form, Depends, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timedelta
import io
import re
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor

# Import our new auth and models
from auth import (
    get_current_user, require_admin, require_recruiter, require_any_auth,
    get_password_hash, verify_password, create_access_token, 
    generate_verification_token, TokenData, UserRole
)
from models import (
    User, UserCreate, UserLogin, UserResponse, TokenResponse,
    AccessLog, AccessLogCreate, AccessReason,
    Candidate, CandidateCreate, CandidateResponse,
    JobPosting, JobPostingCreate, MatchResult, SearchRequest,
    StatusCheck, StatusCheckCreate
)

# File processing imports
from docx import Document
import PyPDF2

# LLM Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create indexes for vector search
async def create_indexes():
    try:
        # Create vector search indexes for candidates and job postings
        await db.candidates.create_index([("embedding", "2dsphere")])
        await db.job_postings.create_index([("embedding", "2dsphere")])
        # Create text indexes for search functionality
        await db.candidates.create_index([("skills", "text"), ("resume_text", "text")])
        await db.job_postings.create_index([("required_skills", "text"), ("description", "text")])
    except Exception as e:
        logger.info(f"Index creation info: {e}")

# Create the main app without a prefix
app = FastAPI(title="Job Matching API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM client
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
if not EMERGENT_LLM_KEY:
    raise ValueError("EMERGENT_LLM_KEY is required for embeddings generation")

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Skills normalization mapping
SKILLS_MAPPING = {
    # Programming Languages
    "javascript": ["js", "javascript", "node.js", "nodejs", "node"],
    "python": ["python", "py", "python3", "django", "flask", "fastapi"],
    "java": ["java", "spring", "spring boot", "hibernate"],
    "react": ["react", "reactjs", "react.js", "jsx"],
    "angular": ["angular", "angularjs", "angular.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "typescript": ["typescript", "ts"],
    "css": ["css", "css3", "scss", "sass", "less"],
    "html": ["html", "html5", "markup"],
    
    # Databases
    "mongodb": ["mongodb", "mongo", "nosql"],
    "mysql": ["mysql", "sql"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "sqlite": ["sqlite", "sqlite3"],
    
    # Cloud & DevOps
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s", "container orchestration"],
    "git": ["git", "version control", "github", "gitlab"],
    
    # AI/ML
    "machine learning": ["machine learning", "ml", "ai", "artificial intelligence"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
}

def normalize_skills(skills_list: List[str]) -> List[str]:
    """Normalize and deduplicate skills"""
    normalized = set()
    for skill in skills_list:
        skill_lower = skill.lower().strip()
        found_match = False
        for canonical, variations in SKILLS_MAPPING.items():
            if skill_lower in variations:
                normalized.add(canonical)
                found_match = True
                break
        if not found_match:
            normalized.add(skill_lower)
    return list(normalized)

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text using keyword matching"""
    text_lower = text.lower()
    found_skills = []
    
    for canonical, variations in SKILLS_MAPPING.items():
        for variation in variations:
            if variation in text_lower:
                found_skills.append(canonical)
                break
    
    return list(set(found_skills))

def extract_experience_years(text: str) -> int:
    """Extract years of experience from text"""
    text_lower = text.lower()
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'(\d+)\+?\s*years?\s*(?:in|with)',
        r'experience\s*:?\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*(?:professional|work)'
    ]
    
    max_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            try:
                years = int(match)
                max_years = max(max_years, years)
            except ValueError:
                continue
    
    return max_years

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding using TF-IDF with improved corpus"""
    try:
        # Create a more comprehensive corpus for better TF-IDF results
        tech_corpus = [
            text,
            "software engineer developer programming coding",
            "javascript python java react node.js",
            "database mongodb mysql postgresql sql",
            "cloud aws azure docker kubernetes",
            "frontend backend full stack development",
            "machine learning ai artificial intelligence",
            "marketing manager social media campaigns",
            "data analysis analytics visualization"
        ]
        
        vectorizer = TfidfVectorizer(
            max_features=384, 
            stop_words='english', 
            lowercase=True,
            ngram_range=(1, 2),  # Include bigrams
            min_df=1,
            max_df=0.95
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(tech_corpus)
            # Get the embedding for our input text (first document)
            embedding = tfidf_matrix[0].toarray()[0].tolist()
            
            # Normalize the embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = (embedding / norm).tolist()
            else:
                # Create a basic embedding based on text features
                words = text.lower().split()
                embedding = [len(words) / 100.0] + [0.1 if word in text.lower() else 0.0 for word in ['javascript', 'python', 'react', 'node', 'database', 'aws', 'docker', 'machine learning', 'marketing', 'design']]
                embedding = embedding[:384] + [0.0] * (384 - len(embedding))
            
            return embedding
        except Exception as e:
            logger.error(f"TF-IDF embedding error: {e}")
            # Return a simple hash-based embedding as fallback
            import hashlib
            text_hash = hashlib.md5(text.lower().encode()).hexdigest()
            embedding = [float(int(char, 16)) / 15.0 for char in text_hash]
            embedding = embedding + [0.1] * (384 - len(embedding))
            return embedding[:384]
            
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        # Return zero vector as fallback
        return [0.1] * 384  # Small values instead of zeros

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between embeddings"""
    try:
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return float(similarity)
    except Exception as e:
        logger.error(f"Similarity calculation error: {e}")
        return 0.0

def calculate_skill_overlap(candidate_skills: List[str], job_skills: List[str]) -> float:
    """Calculate skill overlap percentage"""
    if not job_skills:
        return 1.0
    
    candidate_set = set(skill.lower() for skill in candidate_skills)
    job_set = set(skill.lower() for skill in job_skills)
    
    overlap = len(candidate_set.intersection(job_set))
    return overlap / len(job_set) if job_set else 0.0

def calculate_experience_match(candidate_years: int, required_years: int) -> float:
    """Calculate experience match score"""
    if required_years <= 0:
        return 1.0
    
    if candidate_years >= required_years:
        return 1.0
    else:
        return candidate_years / required_years

# Helper function to log candidate access
async def log_candidate_access(
    user: TokenData, 
    candidate: Candidate, 
    reason: AccessReason, 
    details: Optional[str] = None,
    request: Optional[Request] = None
):
    """Log access to candidate information for compliance"""
    access_log = AccessLog(
        user_id=user.user_id,
        user_email=user.email,
        user_role=user.role,
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        access_reason=reason,
        access_details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    await db.access_logs.insert_one(access_log.dict())
    return access_log

# File processing functions
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Job Matching API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/resume")
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    name: str = Form(...),
    email: str = Form(...),
    resume_text: Optional[str] = Form(None),
    skills: Optional[str] = Form(""),
    experience_years: Optional[int] = Form(0),
    education: Optional[str] = Form("")
):
    """Upload and process resume"""
    try:
        extracted_text = ""
        
        # Extract text from uploaded file if provided
        if file:
            file_content = await file.read()
            if file.filename.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(file_content)
            elif file.filename.lower().endswith('.docx'):
                extracted_text = extract_text_from_docx(file_content)
            elif file.filename.lower().endswith('.txt'):
                extracted_text = file_content.decode('utf-8')
        
        # Use provided resume_text or extracted text
        final_text = resume_text or extracted_text
        if not final_text:
            raise HTTPException(status_code=400, detail="No resume text provided")
        
        # Parse skills from text if not provided
        provided_skills = [s.strip() for s in skills.split(",") if s.strip()] if skills else []
        extracted_skills = extract_skills_from_text(final_text)
        all_skills = list(set(provided_skills + extracted_skills))
        normalized_skills = normalize_skills(all_skills)
        
        # Extract experience if not provided
        final_experience = experience_years or extract_experience_years(final_text)
        
        # Generate embedding
        embedding = await generate_embedding(final_text)
        
        # Create candidate
        candidate = Candidate(
            name=name,
            email=email,
            skills=normalized_skills,
            experience_years=final_experience,
            education=education,
            resume_text=final_text,
            embedding=embedding
        )
        
        # Store in database
        await db.candidates.insert_one(candidate.dict())
        
        return {
            "message": "Resume processed successfully",
            "candidate_id": candidate.id,
            "extracted_skills": normalized_skills,
            "experience_years": final_experience
        }
        
    except Exception as e:
        logger.error(f"Resume processing error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

@api_router.post("/job", response_model=JobPosting)
async def create_job_posting(job_data: JobPostingCreate):
    """Create a new job posting"""
    try:
        # Normalize skills
        normalized_skills = normalize_skills(job_data.required_skills)
        
        # Extract experience from description if not provided
        min_exp = job_data.min_experience_years or extract_experience_years(job_data.description)
        
        # Create full job text for embedding
        job_text = f"{job_data.title} {job_data.company} {job_data.description} {' '.join(normalized_skills)} {job_data.location}"
        
        # Generate embedding
        embedding = await generate_embedding(job_text)
        
        # Create job posting
        job = JobPosting(
            title=job_data.title,
            company=job_data.company,
            required_skills=normalized_skills,
            location=job_data.location,
            salary=job_data.salary,
            description=job_data.description,
            min_experience_years=min_exp,
            embedding=embedding
        )
        
        # Store in database
        await db.job_postings.insert_one(job.dict())
        
        return job
        
    except Exception as e:
        logger.error(f"Job posting creation error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Job posting creation failed: {str(e)}")

@api_router.get("/search", response_model=List[MatchResult])
async def search_candidates(job_id: str, k: int = 10):
    """Search and rank candidates for a job"""
    try:
        # Get job posting
        job = await db.job_postings.find_one({"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job posting not found")
        
        job_obj = JobPosting(**job)
        
        # Get all candidates
        candidates_cursor = db.candidates.find()
        candidates = await candidates_cursor.to_list(1000)
        
        if not candidates:
            return []
        
        # Calculate scores for each candidate
        matches = []
        
        for candidate_data in candidates:
            candidate = Candidate(**candidate_data)
            
            # Calculate semantic similarity
            semantic_score = calculate_similarity(candidate.embedding, job_obj.embedding)
            
            # Calculate skill overlap
            skill_overlap = calculate_skill_overlap(candidate.skills, job_obj.required_skills)
            
            # Calculate experience match
            experience_match = calculate_experience_match(
                candidate.experience_years, 
                job_obj.min_experience_years
            )
            
            # Calculate total score (weighted average)
            total_score = (
                semantic_score * 0.4 +        # 40% semantic similarity
                skill_overlap * 0.4 +         # 40% skill overlap
                experience_match * 0.2        # 20% experience match
            )
            
            match_result = MatchResult(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                candidate_email=candidate.email,
                candidate_skills=candidate.skills,
                candidate_experience_years=candidate.experience_years,
                total_score=total_score,
                semantic_score=semantic_score,
                skill_overlap_score=skill_overlap,
                experience_match_score=experience_match,
                score_breakdown={
                    "semantic_weight": 0.4,
                    "skill_overlap_weight": 0.4,
                    "experience_weight": 0.2,
                    "matched_skills": list(set(candidate.skills).intersection(set(job_obj.required_skills))),
                    "missing_skills": list(set(job_obj.required_skills) - set(candidate.skills))
                }
            )
            
            matches.append(match_result)
        
        # Sort by total score and return top k
        matches.sort(key=lambda x: x.total_score, reverse=True)
        return matches[:k]
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Get endpoints for data
@api_router.get("/candidates", response_model=List[Candidate])
async def get_candidates():
    """Get all candidates"""
    candidates = await db.candidates.find().to_list(1000)
    return [Candidate(**candidate) for candidate in candidates]

@api_router.get("/jobs", response_model=List[JobPosting])
async def get_job_postings():
    """Get all job postings"""
    jobs = await db.job_postings.find().to_list(1000)
    return [JobPosting(**job) for job in jobs]

@api_router.get("/candidates/{candidate_id}", response_model=Candidate)
async def get_candidate(candidate_id: str):
    """Get a specific candidate"""
    candidate = await db.candidates.find_one({"id": candidate_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return Candidate(**candidate)

@api_router.get("/jobs/{job_id}", response_model=JobPosting)
async def get_job_posting(job_id: str):
    """Get a specific job posting"""
    job = await db.job_postings.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return JobPosting(**job)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await create_indexes()
    logger.info("Job Matching API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()