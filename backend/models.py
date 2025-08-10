from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"

class AccessReason(str, Enum):
    SEARCH = "search"
    VIEW_PROFILE = "view_profile"
    EVALUATION = "evaluation"
    CONTACT = "contact"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.CANDIDATE
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    verification_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.CANDIDATE

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Access Log Models
class AccessLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_role: UserRole
    candidate_id: str
    candidate_name: str
    candidate_email: str
    access_reason: AccessReason
    access_details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AccessLogCreate(BaseModel):
    candidate_id: str
    access_reason: AccessReason
    access_details: Optional[str] = None

# Enhanced Candidate Models
class Candidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    skills: List[str] = []
    experience_years: int = 0
    education: str = ""
    resume_text: str
    embedding: List[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # User ID who created this candidate

class CandidateResponse(BaseModel):
    """Response model that can handle PII redaction"""
    id: str
    name: str
    email: str
    skills: List[str]
    experience_years: int
    education: str
    created_at: datetime
    
    @classmethod
    def from_candidate(cls, candidate: Candidate, blind_mode: bool = False):
        """Create response with optional PII redaction"""
        if blind_mode:
            # Redact PII information
            name_parts = candidate.name.split()
            redacted_name = f"{name_parts[0][0]}***" if name_parts else "Anonymous"
            
            email_parts = candidate.email.split("@")
            redacted_email = f"{email_parts[0][:2]}***@{email_parts[1]}" if len(email_parts) == 2 else "***@***.com"
            
            return cls(
                id=candidate.id,
                name=redacted_name,
                email=redacted_email,
                skills=candidate.skills,
                experience_years=candidate.experience_years,
                education=candidate.education,
                created_at=candidate.created_at
            )
        else:
            return cls(
                id=candidate.id,
                name=candidate.name,
                email=candidate.email,
                skills=candidate.skills,
                experience_years=candidate.experience_years,
                education=candidate.education,
                created_at=candidate.created_at
            )

class CandidateCreate(BaseModel):
    name: str
    email: str
    resume_text: str
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = 0
    education: Optional[str] = ""

# Enhanced Job Posting Models
class JobPosting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    required_skills: List[str] = []
    location: str = ""
    salary: str = ""
    description: str
    min_experience_years: int = 0
    embedding: List[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID who created this job

class JobPostingCreate(BaseModel):
    title: str
    company: str
    required_skills: List[str]
    location: Optional[str] = ""
    salary: Optional[str] = ""
    description: str
    min_experience_years: Optional[int] = 0

# Applications Models
class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    REVIEWING = "reviewing"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class Application(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    job_id: str
    status: ApplicationStatus = ApplicationStatus.APPLIED
    applied_at: datetime = Field(default_factory=datetime.utcnow)

class ApplicationCreate(BaseModel):
    job_id: str

class ApplicationWithJob(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    status: ApplicationStatus
    applied_at: datetime

# Enhanced Match Result Models
class MatchResult(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_skills: List[str]
    candidate_experience_years: int
    total_score: float
    semantic_score: float
    skill_overlap_score: float
    experience_match_score: float
    score_breakdown: Dict[str, Any]
    
    @classmethod
    def from_candidate_and_scores(
        cls, 
        candidate: Candidate, 
        total_score: float,
        semantic_score: float,
        skill_overlap_score: float, 
        experience_match_score: float,
        score_breakdown: Dict[str, Any],
        blind_mode: bool = False
    ):
        """Create match result with optional PII redaction"""
        if blind_mode:
            # Redact PII information
            name_parts = candidate.name.split()
            redacted_name = f"{name_parts[0][0]}***" if name_parts else "Anonymous"
            
            email_parts = candidate.email.split("@")
            redacted_email = f"{email_parts[0][:2]}***@{email_parts[1]}" if len(email_parts) == 2 else "***@***.com"
            
            return cls(
                candidate_id=candidate.id,
                candidate_name=redacted_name,
                candidate_email=redacted_email,
                candidate_skills=candidate.skills,
                candidate_experience_years=candidate.experience_years,
                total_score=total_score,
                semantic_score=semantic_score,
                skill_overlap_score=skill_overlap_score,
                experience_match_score=experience_match_score,
                score_breakdown=score_breakdown
            )
        else:
            return cls(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                candidate_email=candidate.email,
                candidate_skills=candidate.skills,
                candidate_experience_years=candidate.experience_years,
                total_score=total_score,
                semantic_score=semantic_score,
                skill_overlap_score=skill_overlap_score,
                experience_match_score=experience_match_score,
                score_breakdown=score_breakdown
            )

class SearchRequest(BaseModel):
    job_id: str
    k: int = 10
    blind_screening: bool = False

# Status Check Models (keeping existing)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str