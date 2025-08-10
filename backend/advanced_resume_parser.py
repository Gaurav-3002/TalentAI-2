import os
import json
import logging
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

logger = logging.getLogger(__name__)
load_dotenv()

class AdvancedResumeParser:
    """
    Advanced resume parser using Gemini 2.0-flash for LLM-powered structured data extraction.
    Supports OCR for scanned PDFs and intelligent entity extraction.
    """
    
    def __init__(self):
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY', 'your-gemini-api-key-here-placeholder')
        self.fallback_key = os.environ.get('EMERGENT_LLM_KEY')  # Fallback to universal key
        self.model = "gemini-2.0-flash"
        
        # Template for structured extraction
        self.extraction_prompt = """
You are an expert resume parser. Analyze the provided resume and extract structured information in JSON format.

Extract the following information:
1. Personal Information (name, email, phone, location, linkedin, github, portfolio)
2. Professional Summary/Objective
3. Skills (technical skills, soft skills, languages, certifications)
4. Work Experience (company, position, duration, location, responsibilities, achievements)
5. Education (institution, degree, field, graduation_date, gpa)
6. Projects (name, description, technologies, links)
7. Certifications (name, issuer, date, credential_id)
8. Awards/Achievements
9. Languages (language, proficiency_level)
10. Publications/Patents (if any)

Return ONLY valid JSON in this exact format:
{
    "personal_info": {
        "name": "string",
        "email": "string",
        "phone": "string",
        "location": "string",
        "linkedin": "string",
        "github": "string",
        "portfolio": "string"
    },
    "summary": "string",
    "skills": {
        "technical": ["skill1", "skill2"],
        "soft_skills": ["skill1", "skill2"],
        "languages": ["language1", "language2"],
        "certifications": ["cert1", "cert2"]
    },
    "work_experience": [
        {
            "company": "string",
            "position": "string",
            "duration": "string",
            "location": "string",
            "responsibilities": ["resp1", "resp2"],
            "achievements": ["achievement1", "achievement2"]
        }
    ],
    "education": [
        {
            "institution": "string",
            "degree": "string",
            "field": "string",
            "graduation_date": "string",
            "gpa": "string"
        }
    ],
    "projects": [
        {
            "name": "string",
            "description": "string",
            "technologies": ["tech1", "tech2"],
            "link": "string"
        }
    ],
    "certifications": [
        {
            "name": "string",
            "issuer": "string",
            "date": "string",
            "credential_id": "string"
        }
    ],
    "awards": ["award1", "award2"],
    "languages_spoken": [
        {
            "language": "string",
            "proficiency": "string"
        }
    ],
    "publications": [
        {
            "title": "string",
            "publication": "string",
            "date": "string"
        }
    ],
    "extracted_years_experience": 0,
    "parsing_confidence": 0.0
}

Important: 
- Extract ALL skills mentioned, including technical, soft skills, and tools
- Calculate years of experience by analyzing work history dates
- Set parsing_confidence between 0.0-1.0 based on document clarity and completeness
- If information is not found, use null or empty arrays/strings
- Ensure all extracted data is accurate and properly categorized
"""

    def _get_api_key(self) -> str:
        """Get the appropriate API key for Gemini"""
        if self.gemini_api_key and self.gemini_api_key != 'your-gemini-api-key-here-placeholder':
            return self.gemini_api_key
        elif self.fallback_key:
            logger.info("Using universal EMERGENT_LLM_KEY for Gemini parsing")
            return self.fallback_key
        else:
            raise ValueError("No valid API key found for Gemini. Please set GEMINI_API_KEY or EMERGENT_LLM_KEY")

    def is_available(self) -> bool:
        """Check if the advanced parser is available (has valid API key)"""
        try:
            key = self._get_api_key()
            return key is not None and key != 'your-gemini-api-key-here-placeholder'
        except:
            return False

    async def parse_resume_from_file(self, file_content: bytes, filename: str, mime_type: str = None) -> Dict[str, Any]:
        """
        Parse resume from file content using Gemini with OCR support
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            mime_type: MIME type of the file
            
        Returns:
            Structured resume data as dictionary
        """
        try:
            # Determine MIME type if not provided
            if not mime_type:
                if filename.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif filename.lower().endswith('.docx'):
                    mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif filename.lower().endswith('.txt'):
                    mime_type = 'text/plain'
                else:
                    mime_type = 'application/octet-stream'

            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                # Initialize Gemini chat
                chat = LlmChat(
                    api_key=self._get_api_key(),
                    session_id=f"resume_parse_{hash(filename)}",
                    system_message="You are an expert resume parser that extracts structured information from documents."
                ).with_model("gemini", self.model)

                # Create file attachment
                file_attachment = FileContentWithMimeType(
                    file_path=temp_file_path,
                    mime_type=mime_type
                )

                # Send parsing request
                user_message = UserMessage(
                    text=self.extraction_prompt,
                    file_contents=[file_attachment]
                )

                response = await chat.send_message(user_message)
                
                # Parse JSON response
                try:
                    # Clean response - remove any markdown formatting
                    clean_response = response.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response[7:]
                    if clean_response.endswith('```'):
                        clean_response = clean_response[:-3]
                    
                    parsed_data = json.loads(clean_response.strip())
                    
                    # Add metadata
                    parsed_data['parsing_method'] = 'llm_advanced'
                    parsed_data['model_used'] = self.model
                    parsed_data['filename'] = filename
                    parsed_data['mime_type'] = mime_type
                    
                    return parsed_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response: {response}")
                    raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Advanced resume parsing failed: {e}")
            raise

    async def parse_resume_from_text(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume from plain text using Gemini
        
        Args:
            resume_text: Resume content as text
            
        Returns:
            Structured resume data as dictionary
        """
        try:
            # Initialize Gemini chat
            chat = LlmChat(
                api_key=self._get_api_key(),
                session_id=f"resume_text_parse_{hash(resume_text[:100])}",
                system_message="You are an expert resume parser that extracts structured information from text."
            ).with_model("gemini", self.model)

            # Create user message with resume text
            full_prompt = f"{self.extraction_prompt}\n\nResume Text:\n{resume_text}"
            user_message = UserMessage(text=full_prompt)

            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                # Clean response - remove any markdown formatting
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                
                parsed_data = json.loads(clean_response.strip())
                
                # Add metadata
                parsed_data['parsing_method'] = 'llm_text'
                parsed_data['model_used'] = self.model
                parsed_data['text_length'] = len(resume_text)
                
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response}")
                raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
                
        except Exception as e:
            logger.error(f"Advanced text parsing failed: {e}")
            raise

    def extract_normalized_skills(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Extract and normalize skills from parsed resume data
        
        Args:
            parsed_data: Structured resume data from LLM parsing
            
        Returns:
            List of normalized skills
        """
        all_skills = set()
        
        if 'skills' in parsed_data:
            skills_section = parsed_data['skills']
            
            # Add technical skills
            if 'technical' in skills_section:
                all_skills.update(skill.lower().strip() for skill in skills_section['technical'] if skill)
            
            # Add soft skills
            if 'soft_skills' in skills_section:
                all_skills.update(skill.lower().strip() for skill in skills_section['soft_skills'] if skill)
            
            # Add languages as skills
            if 'languages' in skills_section:
                all_skills.update(skill.lower().strip() for skill in skills_section['languages'] if skill)
            
            # Add certifications as skills
            if 'certifications' in skills_section:
                all_skills.update(skill.lower().strip() for skill in skills_section['certifications'] if skill)
        
        # Also extract skills from projects
        if 'projects' in parsed_data:
            for project in parsed_data['projects']:
                if 'technologies' in project:
                    all_skills.update(tech.lower().strip() for tech in project['technologies'] if tech)
        
        # Also extract skills from certifications
        if 'certifications' in parsed_data:
            for cert in parsed_data['certifications']:
                if 'name' in cert and cert['name']:
                    all_skills.add(cert['name'].lower().strip())
        
        return list(all_skills)

    def extract_experience_years(self, parsed_data: Dict[str, Any]) -> int:
        """
        Extract years of experience from parsed resume data
        
        Args:
            parsed_data: Structured resume data from LLM parsing
            
        Returns:
            Number of years of experience
        """
        if 'extracted_years_experience' in parsed_data:
            return max(0, int(parsed_data['extracted_years_experience']))
        return 0

    def get_parsing_confidence(self, parsed_data: Dict[str, Any]) -> float:
        """
        Get confidence score of the parsing
        
        Args:
            parsed_data: Structured resume data from LLM parsing
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if 'parsing_confidence' in parsed_data:
            return max(0.0, min(1.0, float(parsed_data['parsing_confidence'])))
        return 0.5  # Default confidence if not provided

# Create global instance
advanced_parser = AdvancedResumeParser()