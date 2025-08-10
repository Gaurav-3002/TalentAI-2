"""
Task management service for handling async operations
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from celery_app import celery_app
from models import TaskInfo, TaskInfoCreate, TaskInfoResponse, TaskType, TaskStatus

logger = logging.getLogger(__name__)

class TaskService:
    """Service for managing async tasks"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def create_task(
        self, 
        task_type: TaskType, 
        user_id: str, 
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new task and return task ID"""
        
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_by=user_id,
            metadata=metadata or {}
        )
        
        await self.db.task_status.insert_one(task_info.dict())
        
        logger.info(f"Created task {task_id} of type {task_type} for user {user_id}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskInfoResponse]:
        """Get current status of a task"""
        
        task_doc = await self.db.task_status.find_one({"task_id": task_id})
        if not task_doc:
            return None
        
        task_info = TaskInfo(**task_doc)
        
        # Get Celery task status if available
        try:
            celery_result = celery_app.AsyncResult(task_id)
            if celery_result.state in ['SUCCESS', 'FAILURE', 'REVOKED']:
                # Update database with final status if not already updated
                if task_info.status not in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
                    await self._sync_celery_status(task_id, celery_result)
                    # Refresh task_info
                    task_doc = await self.db.task_status.find_one({"task_id": task_id})
                    task_info = TaskInfo(**task_doc)
        except Exception as e:
            logger.warning(f"Could not get Celery status for task {task_id}: {e}")
        
        # Calculate estimated completion time
        estimated_completion = None
        if task_info.status == TaskStatus.PROGRESS and task_info.progress > 0:
            if task_info.started_at:
                elapsed = (datetime.utcnow() - task_info.started_at).total_seconds()
                if task_info.progress > 10:  # Avoid division by very small numbers
                    estimated_total = (elapsed / task_info.progress) * 100
                    estimated_remaining = estimated_total - elapsed
                    estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_remaining)
        
        return TaskInfoResponse(
            task_id=task_info.task_id,
            task_type=task_info.task_type,
            status=task_info.status,
            progress=task_info.progress,
            result=task_info.result,
            error=task_info.error,
            created_at=task_info.created_at,
            started_at=task_info.started_at,
            completed_at=task_info.completed_at,
            estimated_completion=estimated_completion,
            metadata=task_info.metadata
        )
    
    async def _sync_celery_status(self, task_id: str, celery_result):
        """Sync task status with Celery result"""
        
        status_map = {
            'SUCCESS': TaskStatus.SUCCESS,
            'FAILURE': TaskStatus.FAILURE,
            'REVOKED': TaskStatus.REVOKED,
            'RETRY': TaskStatus.RETRY
        }
        
        update_data = {
            'status': status_map.get(celery_result.state, TaskStatus.PENDING),
            'completed_at': datetime.utcnow()
        }
        
        if celery_result.state == 'SUCCESS':
            update_data['result'] = celery_result.result
            update_data['progress'] = 100
        elif celery_result.state == 'FAILURE':
            update_data['error'] = str(celery_result.info)
        
        await self.db.task_status.update_one(
            {'task_id': task_id},
            {'$set': update_data}
        )
    
    async def cancel_task(self, task_id: str, user_id: str) -> bool:
        """Cancel a running task"""
        
        # Check if task exists and belongs to user
        task_doc = await self.db.task_status.find_one({
            "task_id": task_id,
            "created_by": user_id
        })
        
        if not task_doc:
            return False
        
        task_info = TaskInfo(**task_doc)
        
        # Only cancel if not already completed
        if task_info.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
            return False
        
        try:
            # Revoke Celery task
            celery_app.control.revoke(task_id, terminate=True)
            
            # Update database
            await self.db.task_status.update_one(
                {'task_id': task_id},
                {
                    '$set': {
                        'status': TaskStatus.REVOKED,
                        'completed_at': datetime.utcnow(),
                        'error': 'Task cancelled by user'
                    }
                }
            )
            
            logger.info(f"Task {task_id} cancelled by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_user_tasks(
        self, 
        user_id: str, 
        task_type: Optional[TaskType] = None,
        limit: int = 50
    ) -> list[TaskInfoResponse]:
        """Get tasks for a user"""
        
        query = {"created_by": user_id}
        if task_type:
            query["task_type"] = task_type
        
        task_docs = await self.db.task_status.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        
        tasks = []
        for doc in task_docs:
            task_info = TaskInfo(**doc)
            
            # Calculate estimated completion
            estimated_completion = None
            if task_info.status == TaskStatus.PROGRESS and task_info.progress > 0:
                if task_info.started_at:
                    elapsed = (datetime.utcnow() - task_info.started_at).total_seconds()
                    if task_info.progress > 10:
                        estimated_total = (elapsed / task_info.progress) * 100
                        estimated_remaining = estimated_total - elapsed
                        estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_remaining)
            
            tasks.append(TaskInfoResponse(
                task_id=task_info.task_id,
                task_type=task_info.task_type,
                status=task_info.status,
                progress=task_info.progress,
                result=task_info.result,
                error=task_info.error,
                created_at=task_info.created_at,
                started_at=task_info.started_at,
                completed_at=task_info.completed_at,
                estimated_completion=estimated_completion,
                metadata=task_info.metadata
            ))
        
        return tasks
    
    # Resume Processing Tasks
    async def start_resume_processing(
        self,
        file_content_b64: Optional[str],
        filename: Optional[str],
        resume_text: Optional[str],
        name: str,
        email: str,
        skills: str,
        experience_years: int,
        education: str,
        user_id: str
    ) -> str:
        """Start async resume processing task"""
        
        from tasks.resume_tasks import process_resume_async
        
        task_id = await self.create_task(
            TaskType.RESUME_PROCESSING,
            user_id,
            metadata={
                "filename": filename,
                "has_file": bool(file_content_b64),
                "name": name,
                "email": email
            }
        )
        
        # Start Celery task
        process_resume_async.apply_async(
            task_id=task_id,
            args=[
                task_id, file_content_b64, filename, resume_text,
                name, email, skills, experience_years, education, user_id
            ]
        )
        
        return task_id
    
    # Search Tasks
    async def start_candidate_search(
        self,
        job_id: str,
        k: int,
        blind_screening: bool,
        user_id: str,
        session_id: str
    ) -> str:
        """Start async candidate search task"""
        
        from tasks.search_tasks import search_candidates_async
        
        task_id = await self.create_task(
            TaskType.CANDIDATE_SEARCH,
            user_id,
            metadata={
                "job_id": job_id,
                "k": k,
                "blind_screening": blind_screening,
                "session_id": session_id
            }
        )
        
        # Start Celery task
        search_candidates_async.apply_async(
            task_id=task_id,
            args=[task_id, job_id, k, blind_screening, user_id, session_id]
        )
        
        return task_id
    
    # Learning Tasks
    async def start_model_retraining(
        self,
        job_category: Optional[str],
        recruiter_id: Optional[str],
        force_retrain: bool,
        user_id: str
    ) -> str:
        """Start async model retraining task"""
        
        from tasks.learning_tasks import retrain_learning_model
        
        task_id = await self.create_task(
            TaskType.LEARNING_RETRAIN,
            user_id,
            metadata={
                "job_category": job_category,
                "recruiter_id": recruiter_id,
                "force_retrain": force_retrain
            }
        )
        
        # Start Celery task
        retrain_learning_model.apply_async(
            task_id=task_id,
            args=[task_id, job_category, recruiter_id, force_retrain]
        )
        
        return task_id
    
    # Embedding Tasks
    async def start_batch_embedding_generation(
        self,
        texts: list[str],
        batch_name: str,
        user_id: str
    ) -> str:
        """Start async batch embedding generation task"""
        
        from tasks.embedding_tasks import generate_embedding_batch
        
        task_id = await self.create_task(
            TaskType.EMBEDDING_GENERATION,
            user_id,
            metadata={
                "batch_name": batch_name,
                "text_count": len(texts)
            }
        )
        
        # Start Celery task
        generate_embedding_batch.apply_async(
            task_id=task_id,
            args=[task_id, texts, batch_name]
        )
        
        return task_id