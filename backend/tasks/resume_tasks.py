"""
Resume processing tasks
"""
import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from celery import shared_task
from celery.exceptions import Retry

from tasks.base_task import BaseJobMatcherTask
from models import (
    Candidate, ParsedResumeData, AsyncResumeProcessingResult, 
    TaskType, TaskStatus
)

# Import necessary services and utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_resume_parser import advanced_parser
from server import (
    extract_text_from_pdf, extract_text_from_docx, 
    extract_skills_from_text, normalize_skills, extract_experience_years
)

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseJobMatcherTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_resume_async(
    self,
    task_id: str,
    file_content_b64: Optional[str] = None,
    filename: Optional[str] = None,
    resume_text: Optional[str] = None,
    name: str = "",
    email: str = "",
    skills: str = "",
    experience_years: int = 0,
    education: str = "",
    user_id: str = ""
) -> Dict[str, Any]:
    """
    Asynchronously process a resume with LLM parsing, embedding generation, and FAISS update
    """
    logger.info(f"Starting async resume processing for task {task_id}")
    
    # Update task status to started
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_process_resume_internal(
            self, task_id, file_content_b64, filename, resume_text,
            name, email, skills, experience_years, education, user_id
        ))
        return result
        
    except Exception as e:
        logger.error(f"Resume processing failed for task {task_id}: {e}")
        logger.error(traceback.format_exc())
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _process_resume_internal(
    task_instance,
    task_id: str,
    file_content_b64: Optional[str],
    filename: Optional[str],
    resume_text: Optional[str],
    name: str,
    email: str,
    skills: str,
    experience_years: int,
    education: str,
    user_id: str
) -> Dict[str, Any]:
    """Internal async resume processing logic"""
    
    extracted_text = ""
    parsed_resume = None
    parsing_method = "basic"
    parsing_confidence = None
    
    try:
        # Step 1: Extract text from uploaded file if provided (10% progress)
        task_instance.update_progress(task_id, 10, "Extracting text from file...")
        
        if file_content_b64 and filename:
            import base64
            file_content = base64.b64decode(file_content_b64)
            
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
                    
                    # Extract text from parsed data
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
                    task_instance.update_progress(task_id, 25, "Advanced LLM parsing completed")
                    
                except Exception as e:
                    logger.warning(f"Advanced parsing failed, falling back to basic: {e}")
                    # Fall back to basic parsing
                    if filename.lower().endswith('.pdf'):
                        extracted_text = extract_text_from_pdf(file_content)
                    elif filename.lower().endswith('.docx'):
                        extracted_text = extract_text_from_docx(file_content)
                    elif filename.lower().endswith('.txt'):
                        extracted_text = file_content.decode('utf-8')
                    task_instance.update_progress(task_id, 25, "Basic file parsing completed")
            else:
                # Use basic parsing
                logger.info("Advanced parser not available, using basic parsing")
                if filename.lower().endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(file_content)
                elif filename.lower().endswith('.docx'):
                    extracted_text = extract_text_from_docx(file_content)
                elif filename.lower().endswith('.txt'):
                    extracted_text = file_content.decode('utf-8')
                task_instance.update_progress(task_id, 25, "Basic file parsing completed")
        
        # Step 2: Handle text-only resume input (30% progress)
        elif resume_text and not file_content_b64:
            task_instance.update_progress(task_id, 30, "Processing text resume...")
            
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
            raise ValueError("No resume text provided")
        
        # Step 3: Extract skills and experience (50% progress)
        task_instance.update_progress(task_id, 50, "Extracting skills and experience...")
        
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
        
        # Step 4: Generate embedding (70% progress)
        task_instance.update_progress(task_id, 70, "Generating embeddings...")
        
        embedding = await _generate_embedding_for_resume(final_text)
        embedding_generated = bool(embedding)
        
        # Step 5: Create candidate (85% progress)
        task_instance.update_progress(task_id, 85, "Creating candidate record...")
        
        candidate = Candidate(
            name=name,
            email=email,
            skills=final_skills,
            experience_years=final_experience,
            education=education,
            resume_text=final_text,
            embedding=embedding,
            created_by=user_id,
            parsed_resume=parsed_resume,
            parsing_method=parsing_method,
            parsing_confidence=parsing_confidence
        )
        
        # Step 6: Store in database (90% progress)
        task_instance.update_progress(task_id, 90, "Saving to database...")
        
        await task_instance.db.candidates.insert_one(candidate.dict())

        # Step 7: Update FAISS (95% progress)
        task_instance.update_progress(task_id, 95, "Updating vector index...")
        
        faiss_updated = await _update_faiss_for_candidate(task_instance, candidate)
        
        # Step 8: Prepare result (100% progress)
        task_instance.update_progress(task_id, 100, "Processing completed successfully")
        
        result = AsyncResumeProcessingResult(
            candidate_id=candidate.id,
            extracted_skills=final_skills,
            experience_years=final_experience,
            parsing_method=parsing_method,
            parsing_confidence=parsing_confidence,
            advanced_parsing_available=bool(parsed_resume),
            structured_data={
                "personal_info": parsed_resume.personal_info.dict() if parsed_resume and parsed_resume.personal_info else None,
                "summary": parsed_resume.summary if parsed_resume else None,
                "work_experience_count": len(parsed_resume.work_experience) if parsed_resume else 0,
                "education_count": len(parsed_resume.education) if parsed_resume else 0,
                "projects_count": len(parsed_resume.projects) if parsed_resume else 0,
                "certifications_count": len(parsed_resume.certifications) if parsed_resume else 0
            } if parsed_resume else None,
            embedding_generated=embedding_generated,
            faiss_updated=faiss_updated
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Resume processing error: {e}")
        task_instance.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _generate_embedding_for_resume(text: str) -> List[float]:
    """Generate embedding for resume text"""
    try:
        # Import embedding service
        from embedding_service import EmbeddingService
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        embedding = await embedding_service.generate_single_embedding(text)
        return embedding or []
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return []

async def _update_faiss_for_candidate(task_instance, candidate) -> bool:
    """Update FAISS vector store with new candidate"""
    try:
        from vector_store import FAISSService
        import numpy as np
        
        if not candidate.embedding:
            return False
            
        # Initialize FAISS service
        faiss_service = FAISSService()
        await faiss_service.add_vectors(
            np.array([candidate.embedding], dtype=float),
            [{"type": "candidate", "candidate_id": candidate.id, "name": candidate.name, "email": candidate.email}]
        )
        await faiss_service.save()
        return True
        
    except Exception as e:
        logger.error(f"FAISS update failed: {e}")
        return False