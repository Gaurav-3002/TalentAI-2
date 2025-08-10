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
    Candidate, CandidateCreate, CandidateResponse, ParsedResumeData,
    JobPosting, JobPostingCreate, MatchResult, SearchRequest,
    StatusCheck, StatusCheckCreate,
    Application, ApplicationCreate, ApplicationWithJob, ApplicationStatus,
    # Learning-to-Rank models
    RecruiterInteraction, InteractionCreate, InteractionType,
    LearningWeights, WeightsUpdate
)

# File processing imports
from docx import Document
import PyPDF2

# LLM Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Vector DB and Embeddings Services
from embedding_service import EmbeddingService
from vector_store import FAISSService

# Learning-to-Rank Service
from learning_to_rank import LearningToRankEngine

# Advanced Resume Parser
from advanced_resume_parser import advanced_parser

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
        
        # Create indexes for new collections
        await db.users.create_index([("email", 1)], unique=True)
        await db.users.create_index([("role", 1)])
        await db.access_logs.create_index([("user_id", 1)])
        await db.access_logs.create_index([("candidate_id", 1)])
        await db.access_logs.create_index([("timestamp", -1)])
        await db.access_logs.create_index([("user_id", 1), ("timestamp", -1)])
        await db.applications.create_index([("candidate_id", 1), ("applied_at", -1)])
        await db.applications.create_index([("job_id", 1)])
        
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
    """Generate embedding using Emergent Integrations via EmbeddingService."""
    try:
        svc = getattr(app.state, "embedding_service", None)
        if not svc:
            raise RuntimeError("Embedding service not initialized")
        emb = await svc.generate_single_embedding(text)
        return emb or []
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return []

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

# Authentication and User Management Routes

@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        verification_token = generate_verification_token()
        
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=hashed_password,
            verification_token=verification_token,
            is_verified=True  # Auto-verify for demo purposes
        )
        
        await db.users.insert_one(user.dict())
        
        return UserResponse(**user.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": user_credentials.email})
        if not user_doc:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        user = User(**user_doc)
        
        # Verify password
        if not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Account is inactive"
            )
        
        # Update last login
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value
            }
        )
        
        user_response = UserResponse(**user.dict())
        user_response.last_login = datetime.utcnow()
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    try:
        user_doc = await db.users.find_one({"id": current_user.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(**user_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")

@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: TokenData = Depends(require_admin)):
    """Get all users (admin only)"""
    try:
        users = await db.users.find().to_list(1000)
        return [UserResponse(**user) for user in users]
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@api_router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, 
    new_role: UserRole,
    current_user: TokenData = Depends(require_admin)
):
    """Update user role (admin only)"""
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"role": new_role.value}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": f"User role updated to {new_role}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user role error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")

# Access Log Routes

@api_router.get("/access-logs", response_model=List[AccessLog])
async def get_access_logs(
    limit: int = 100,
    candidate_id: Optional[str] = None,
    current_user: TokenData = Depends(require_recruiter)
):
    """Get access logs (recruiter/admin only)"""
    try:
        filter_query = {}
        if candidate_id:
            filter_query["candidate_id"] = candidate_id
        
        # Non-admin users can only see their own access logs
        if current_user.role != UserRole.ADMIN:
            filter_query["user_id"] = current_user.user_id
        
        logs = await db.access_logs.find(filter_query).sort("timestamp", -1).limit(limit).to_list(limit)
        return [AccessLog(**log) for log in logs]
        
    except Exception as e:
        logger.error(f"Get access logs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get access logs")

@api_router.post("/access-logs", response_model=AccessLog)
async def create_access_log(
    log_data: AccessLogCreate,
    request: Request,
    current_user: TokenData = Depends(require_any_auth)
):
    """Create access log entry"""
    try:
        # Get candidate info
        candidate_doc = await db.candidates.find_one({"id": log_data.candidate_id})
        if not candidate_doc:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate = Candidate(**candidate_doc)
        
        # Create access log
        access_log = await log_candidate_access(
            current_user, candidate, log_data.access_reason,
            log_data.access_details, request
        )
        
        return access_log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create access log error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create access log")

# Profile and Applications Routes
@api_router.get("/profile")
async def get_profile(current_user: TokenData = Depends(require_any_auth)):
    """Return profile info for current user including role-specific data"""
    try:
        user_doc = await db.users.find_one({"id": current_user.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        user = User(**user_doc)
        base = {
            "user": UserResponse(**user_doc).dict(),
            "role": user.role.value
        }
        if user.role == UserRole.CANDIDATE:
            # Latest candidate record created by this user (resume upload)
            candidate_doc = await db.candidates.find({"created_by": user.id}).sort("created_at", -1).limit(1).to_list(1)
            candidate_info = None
            if candidate_doc:
                c = Candidate(**candidate_doc[0])
                candidate_info = {
                    "candidate_id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "skills": c.skills,
                    "experience_years": c.experience_years,
                    "education": c.education,
                    "resume_text": c.resume_text,
                    "created_at": c.created_at
                }
                # Applications for this candidate with job info
                apps = await db.applications.find({"candidate_id": c.id}).sort("applied_at", -1).to_list(200)
                enriched = []
                for a in apps:
                    job = await db.job_postings.find_one({"id": a["job_id"]})
                    if job:
                        enriched.append(ApplicationWithJob(
                            id=a["id"],
                            job_id=a["job_id"],
                            job_title=job["title"],
                            company=job["company"],
                            status=a.get("status", "applied"),
                            applied_at=a.get("applied_at")
                        ).dict())
                base["applications"] = enriched
            base["candidate_info"] = candidate_info
            return base
        elif user.role == UserRole.RECRUITER:
            jobs = await db.job_postings.find({"created_by": user.id}).sort("created_at", -1).to_list(500)
            base["recruiter_info"] = {
                "jobs_count": len(jobs),
                "jobs": [{"id": j["id"], "title": j["title"], "company": j["company"], "created_at": j["created_at"]} for j in jobs]
            }
            return base
        else:  # ADMIN
            total_users = await db.users.count_documents({})
            counts = {
                "admin": await db.users.count_documents({"role": "admin"}),
                "recruiter": await db.users.count_documents({"role": "recruiter"}),
                "candidate": await db.users.count_documents({"role": "candidate"})
            }
            jobs_count = await db.job_postings.count_documents({})
            candidates_count = await db.candidates.count_documents({})
            base["admin_info"] = {
                "users_count": total_users,
                "counts_by_role": counts,
                "jobs_count": jobs_count,
                "candidates_count": candidates_count
            }
            return base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to get profile")

@api_router.post("/applications", response_model=Application)
async def create_application(data: ApplicationCreate, current_user: TokenData = Depends(require_any_auth)):
    """Create an application for the current candidate user to a job"""
    try:
        # Only candidate can apply
        if current_user.role != UserRole.CANDIDATE:
            raise HTTPException(status_code=403, detail="Only candidates can apply to jobs")
        # Find latest candidate profile belonging to user
        candidate_doc = await db.candidates.find({"created_by": current_user.user_id}).sort("created_at", -1).limit(1).to_list(1)
        if not candidate_doc:
            raise HTTPException(status_code=400, detail="Please upload your resume before applying")
        c = Candidate(**candidate_doc[0])
        # Validate job exists
        job = await db.job_postings.find_one({"id": data.job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        # Prevent duplicate application
        existing = await db.applications.find_one({"candidate_id": c.id, "job_id": data.job_id})
        if existing:
            return Application(**existing)
        app_obj = Application(candidate_id=c.id, job_id=data.job_id)
        await db.applications.insert_one(app_obj.dict())
        return app_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create application error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create application")

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
    education: Optional[str] = Form(""),
    current_user: TokenData = Depends(require_any_auth)
):
    """Upload and process resume with advanced LLM parsing (authenticated users only)"""
    try:
        extracted_text = ""
        parsed_resume = None
        parsing_method = "basic"
        parsing_confidence = None
        
        # Step 1: Extract text from uploaded file if provided
        if file:
            file_content = await file.read()
            filename = file.filename or "resume"
            
            # Try advanced parsing first if available
            if advanced_parser.is_available():
                try:
                    logger.info(f"Attempting advanced parsing for file: {filename}")
                    parsed_data = await advanced_parser.parse_resume_from_file(
                        file_content, filename
                    )
                    
                    # Convert to ParsedResumeData model
                    parsed_resume = ParsedResumeData(**parsed_data)
                    parsing_method = "llm_advanced"
                    parsing_confidence = parsed_resume.parsing_confidence
                    
                    # Extract text from parsed data or use original method as fallback
                    if parsed_resume.personal_info.name:
                        extracted_text = f"Resume content processed via LLM\n"
                        extracted_text += f"Name: {parsed_resume.personal_info.name}\n"
                        extracted_text += f"Summary: {parsed_resume.summary or ''}\n"
                        
                        # Add work experience text
                        for exp in parsed_resume.work_experience:
                            extracted_text += f"\nWork: {exp.position} at {exp.company} ({exp.duration})\n"
                            extracted_text += "\n".join(exp.responsibilities)
                        
                        # Add education text
                        for edu in parsed_resume.education:
                            extracted_text += f"\nEducation: {edu.degree} in {edu.field} from {edu.institution}\n"
                        
                        # Add projects
                        for proj in parsed_resume.projects:
                            extracted_text += f"\nProject: {proj.name} - {proj.description}\n"
                    
                    logger.info(f"Advanced parsing successful with confidence: {parsing_confidence}")
                    
                except Exception as e:
                    logger.warning(f"Advanced parsing failed, falling back to basic: {e}")
                    # Fall back to basic parsing
                    if filename.lower().endswith('.pdf'):
                        extracted_text = extract_text_from_pdf(file_content)
                    elif filename.lower().endswith('.docx'):
                        extracted_text = extract_text_from_docx(file_content)
                    elif filename.lower().endswith('.txt'):
                        extracted_text = file_content.decode('utf-8')
            else:
                # Use basic parsing
                logger.info("Advanced parser not available, using basic parsing")
                if filename.lower().endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(file_content)
                elif filename.lower().endswith('.docx'):
                    extracted_text = extract_text_from_docx(file_content)
                elif filename.lower().endswith('.txt'):
                    extracted_text = file_content.decode('utf-8')
        
        # Step 2: Handle text-only resume input
        elif resume_text and not file:
            if advanced_parser.is_available():
                try:
                    logger.info("Attempting advanced parsing for text input")
                    parsed_data = await advanced_parser.parse_resume_from_text(resume_text)
                    parsed_resume = ParsedResumeData(**parsed_data)
                    parsing_method = "llm_text"
                    parsing_confidence = parsed_resume.parsing_confidence
                    extracted_text = resume_text
                    logger.info(f"Advanced text parsing successful with confidence: {parsing_confidence}")
                except Exception as e:
                    logger.warning(f"Advanced text parsing failed, using basic: {e}")
                    extracted_text = resume_text
            else:
                extracted_text = resume_text
        
        # Use provided resume_text or extracted text
        final_text = resume_text or extracted_text
        if not final_text:
            raise HTTPException(status_code=400, detail="No resume text provided")
        
        # Step 3: Extract skills and experience
        if parsed_resume:
            # Use LLM-extracted data
            final_skills = advanced_parser.extract_normalized_skills(parsed_resume.dict())
            final_experience = advanced_parser.extract_experience_years(parsed_resume.dict())
            
            # Override with manual input if provided
            if skills.strip():
                manual_skills = [s.strip() for s in skills.split(",") if s.strip()]
                final_skills.extend(manual_skills)
                final_skills = list(set(final_skills))  # Deduplicate
            
            if experience_years > 0:
                final_experience = experience_years
                
            # Get education from parsed data if not manually provided
            if not education and parsed_resume.education:
                education_text = []
                for edu in parsed_resume.education:
                    edu_str = f"{edu.degree} in {edu.field} from {edu.institution}"
                    if edu.graduation_date:
                        edu_str += f" ({edu.graduation_date})"
                    education_text.append(edu_str)
                education = "; ".join(education_text)
            
            # Use name and email from parsed data if available
            if not name and parsed_resume.personal_info.name:
                name = parsed_resume.personal_info.name
            if not email and parsed_resume.personal_info.email:
                email = parsed_resume.personal_info.email
                
        else:
            # Use basic parsing methods
            provided_skills = [s.strip() for s in skills.split(",") if s.strip()] if skills else []
            extracted_skills = extract_skills_from_text(final_text)
            all_skills = list(set(provided_skills + extracted_skills))
            final_skills = normalize_skills(all_skills)
            final_experience = experience_years or extract_experience_years(final_text)
        
        # Step 4: Generate embedding
        embedding = await generate_embedding(final_text)
        
        # Step 5: Create candidate with enhanced data
        candidate = Candidate(
            name=name,
            email=email,
            skills=final_skills,
            experience_years=final_experience,
            education=education,
            resume_text=final_text,
            embedding=embedding,
            created_by=current_user.user_id,
            parsed_resume=parsed_resume,
            parsing_method=parsing_method,
            parsing_confidence=parsing_confidence
        )
        
        # Step 6: Store in database
        await db.candidates.insert_one(candidate.dict())

        # Step 7: Upsert into FAISS
        try:
            faiss = getattr(app.state, "faiss", None)
            if faiss and candidate.embedding:
                import numpy as np
                await faiss.add_vectors(
                    np.array([candidate.embedding], dtype=float),
                    [{"type": "candidate", "candidate_id": candidate.id, "name": candidate.name, "email": candidate.email}]
                )
                await faiss.save()
        except Exception as e:
            logger.error(f"FAISS add candidate failed: {e}")
        
        # Step 8: Return enhanced response
        response_data = {
            "message": "Resume processed successfully",
            "candidate_id": candidate.id,
            "extracted_skills": final_skills,
            "experience_years": final_experience,
            "parsing_method": parsing_method
        }
        
        if parsing_confidence is not None:
            response_data["parsing_confidence"] = parsing_confidence
            
        if parsed_resume:
            response_data["advanced_parsing_available"] = True
            response_data["structured_data"] = {
                "personal_info": parsed_resume.personal_info.dict() if parsed_resume.personal_info else None,
                "summary": parsed_resume.summary,
                "work_experience_count": len(parsed_resume.work_experience),
                "education_count": len(parsed_resume.education),
                "projects_count": len(parsed_resume.projects),
                "certifications_count": len(parsed_resume.certifications)
            }
        else:
            response_data["advanced_parsing_available"] = False
        
        return response_data
        
    except Exception as e:
        logger.error(f"Resume processing error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

@api_router.post("/job", response_model=JobPosting)
async def create_job_posting(
    job_data: JobPostingCreate,
    current_user: TokenData = Depends(require_recruiter)
):
    """Create a new job posting (recruiter/admin only)"""
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
            embedding=embedding,
            created_by=current_user.user_id
        )
        
        # Store in database
        await db.job_postings.insert_one(job.dict())

        # Add to FAISS as job vector to support semantic lookups
        try:
            faiss = getattr(app.state, "faiss", None)
            if faiss and job.embedding:
                import numpy as np
                await faiss.add_vectors(
                    np.array([job.embedding], dtype=float),
                    [{"type": "job", "job_id": job.id, "title": job.title, "company": job.company}]
                )
                await faiss.save()
        except Exception as e:
            logger.error(f"FAISS add job failed: {e}")
        
        return job
        
    except Exception as e:
        logger.error(f"Job posting creation error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Job posting creation failed: {str(e)}")

@api_router.get("/search", response_model=List[MatchResult])
async def search_candidates(
    request: Request,
    job_id: str, 
    k: int = 10,
    blind_screening: bool = False,
    current_user: TokenData = Depends(require_recruiter)
):
    """Search and rank candidates for a job with optional blind screening using ML-optimized weights"""
    try:
        # Get job posting
        job = await db.job_postings.find_one({"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job posting not found")
        
        job_obj = JobPosting(**job)
        
        # Get optimal weights using Learning-to-Rank engine
        learning_engine = getattr(app.state, "learning_engine", None)
        if learning_engine:
            optimal_weights = await learning_engine.get_optimal_weights(
                job_category=job_obj.title,  # Could be improved with proper categorization
                recruiter_id=current_user.user_id
            )
            weights = {
                'semantic': optimal_weights.semantic_weight,
                'skill': optimal_weights.skill_weight,
                'experience': optimal_weights.experience_weight
            }
            logger.info(f"Using ML-optimized weights: {weights}, confidence: {optimal_weights.confidence_score:.3f}")
        else:
            # Fallback to fixed weights if learning engine not available
            weights = {'semantic': 0.4, 'skill': 0.4, 'experience': 0.2}
            logger.info("Using default fixed weights (Learning engine not available)")
        
        # Get all candidates
        candidates_cursor = db.candidates.find()
        candidates = await candidates_cursor.to_list(1000)
        
        if not candidates:
            return []
        
        # Calculate scores for each candidate
        matches = []
        
        for candidate_data in candidates:
            candidate = Candidate(**candidate_data)
            
            # Log access for each candidate viewed in search results
            await log_candidate_access(
                current_user, candidate, AccessReason.SEARCH,
                f"Search for job: {job_obj.title} at {job_obj.company}, blind_mode={blind_screening}",
                request
            )
            
            # Calculate semantic similarity (use FAISS for better retrieval; fallback to cosine)
            semantic_score = 0.0
            try:
                faiss = getattr(app.state, "faiss", None)
                if faiss and candidate.embedding and job_obj.embedding:
                    import numpy as np
                    # Use job embedding as query against candidate vector; score is inner-product ~ cosine
                    res = await faiss.search(np.array(job_obj.embedding, dtype=float), k=1)
                    if res:
                        # If the top result corresponds to this candidate, use that score; otherwise fallback to cosine
                        top = res[0]
                        if top.get("metadata", {}).get("candidate_id") == candidate.id:
                            semantic_score = float(top.get("score", 0.0))
                if semantic_score == 0.0 and candidate.embedding and job_obj.embedding:
                    semantic_score = calculate_similarity(candidate.embedding, job_obj.embedding)
            except Exception as _e:
                semantic_score = calculate_similarity(candidate.embedding, job_obj.embedding)
            
            # Calculate skill overlap
            skill_overlap = calculate_skill_overlap(candidate.skills, job_obj.required_skills)
            
            # Calculate experience match
            experience_match = calculate_experience_match(
                candidate.experience_years, 
                job_obj.min_experience_years
            )
            
            # Calculate total score using ML-optimized weights
            total_score = (
                semantic_score * weights['semantic'] +
                skill_overlap * weights['skill'] +
                experience_match * weights['experience']
            )
            
            score_breakdown = {
                "semantic_weight": weights['semantic'],
                "skill_overlap_weight": weights['skill'],
                "experience_weight": weights['experience'],
                "matched_skills": list(set(candidate.skills).intersection(set(job_obj.required_skills))),
                "missing_skills": list(set(job_obj.required_skills) - set(candidate.skills))
            }
            
            # Create match result with PII redaction support
            match_result = MatchResult.from_candidate_and_scores(
                candidate=candidate,
                total_score=total_score,
                semantic_score=semantic_score,
                skill_overlap_score=skill_overlap,
                experience_match_score=experience_match,
                score_breakdown=score_breakdown,
                blind_mode=blind_screening
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
@api_router.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(
    blind_mode: bool = False,
    current_user: TokenData = Depends(require_recruiter)
):
    """Get all candidates with optional PII redaction"""
    try:
        candidates = await db.candidates.find().to_list(1000)
        return [
            CandidateResponse.from_candidate(Candidate(**candidate), blind_mode=blind_mode)
            for candidate in candidates
        ]
    except Exception as e:
        logger.error(f"Get candidates error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get candidates")

@api_router.get("/jobs", response_model=List[JobPosting])
async def get_job_postings(current_user: TokenData = Depends(require_any_auth)):
    """Get all job postings (authenticated users only)"""
    try:
        jobs = await db.job_postings.find().to_list(1000)
        return [JobPosting(**job) for job in jobs]
    except Exception as e:
        logger.error(f"Get jobs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jobs")

@api_router.get("/candidates/{candidate_id}/parsed-resume", response_model=ParsedResumeData)
async def get_candidate_parsed_resume(
    candidate_id: str,
    current_user: TokenData = Depends(require_recruiter)
):
    """Get structured parsed resume data for a specific candidate"""
    try:
        candidate = await db.candidates.find_one({"id": candidate_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_obj = Candidate(**candidate)
        
        if not candidate_obj.parsed_resume:
            raise HTTPException(
                status_code=404, 
                detail="No parsed resume data available. Candidate was processed with basic parsing only."
            )
        
        return candidate_obj.parsed_resume
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get parsed resume error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get parsed resume")

@api_router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    request: Request,
    blind_mode: bool = False,
    current_user: TokenData = Depends(require_recruiter)
):
    """Get a specific candidate with access logging and optional PII redaction"""
    try:
        candidate = await db.candidates.find_one({"id": candidate_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_obj = Candidate(**candidate)
        
        # Log access to this candidate's profile
        await log_candidate_access(
            current_user, candidate_obj, AccessReason.VIEW_PROFILE,
            f"Viewed candidate profile, blind_mode={blind_mode}", request
        )
        
        return CandidateResponse.from_candidate(candidate_obj, blind_mode=blind_mode)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get candidate error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get candidate")

@api_router.get("/jobs/{job_id}", response_model=JobPosting)
async def get_job_posting(
    job_id: str,
    current_user: TokenData = Depends(require_any_auth)
):
    """Get a specific job posting"""
    try:
        job = await db.job_postings.find_one({"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job posting not found")
        return JobPosting(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")

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
    await seed_initial_users()
    
    # Initialize EmbeddingService
    try:
        embedding_service = EmbeddingService()
        app.state.embedding_service = embedding_service
        logger.info("EmbeddingService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize EmbeddingService: {e}")
        app.state.embedding_service = None
    
    # Initialize FAISS
    try:
        faiss_service = FAISSService(
            index_path="/app/backend/faiss_data/index.bin",
            metadata_path="/app/backend/faiss_data/meta.json"
        )
        await faiss_service.initialize()
        app.state.faiss = faiss_service
        logger.info("FAISS service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FAISS: {e}")
        app.state.faiss = None
    
    # Initialize Learning-to-Rank Engine
    try:
        learning_engine = LearningToRankEngine(db)
        app.state.learning_engine = learning_engine
        logger.info("Learning-to-Rank engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Learning-to-Rank engine: {e}")
        app.state.learning_engine = None
    
    logger.info("Job Matching API started successfully")

async def seed_initial_users():
    """Create initial admin and recruiter users"""
    try:
        # Check if admin already exists
        admin_exists = await db.users.find_one({"email": "admin@jobmatcher.com"})
        if not admin_exists:
            admin_user = User(
                email="admin@jobmatcher.com",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("admin123"),
                is_verified=True
            )
            await db.users.insert_one(admin_user.dict())
            logger.info("Created default admin user: admin@jobmatcher.com / admin123")
        
        # Check if recruiter already exists
        recruiter_exists = await db.users.find_one({"email": "recruiter@jobmatcher.com"})
        if not recruiter_exists:
            recruiter_user = User(
                email="recruiter@jobmatcher.com",
                full_name="Default Recruiter",
                role=UserRole.RECRUITER,
                hashed_password=get_password_hash("recruiter123"),
                is_verified=True
            )
            await db.users.insert_one(recruiter_user.dict())
            logger.info("Created default recruiter user: recruiter@jobmatcher.com / recruiter123")
        
        # Check if candidate already exists
        candidate_exists = await db.users.find_one({"email": "candidate@jobmatcher.com"})
        if not candidate_exists:
            candidate_user = User(
                email="candidate@jobmatcher.com",
                full_name="Default Candidate",
                role=UserRole.CANDIDATE,
                hashed_password=get_password_hash("candidate123"),
                is_verified=True
            )
            await db.users.insert_one(candidate_user.dict())
            logger.info("Created default candidate user: candidate@jobmatcher.com / candidate123")
            
    except Exception as e:
        logger.error(f"Error seeding initial users: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()