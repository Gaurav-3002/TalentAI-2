"""
Base task class with common functionality
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Task
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BaseJobMatcherTask(Task):
    """Base task class with database connection and common utilities"""
    
    def __init__(self):
        # MongoDB connection
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self._db = None
        
    @property
    def db(self):
        """Lazy database connection"""
        if self._db is None:
            client = AsyncIOMotorClient(self.mongo_url)
            self._db = client[self.db_name]
        return self._db
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")
        self.update_task_status(task_id, 'SUCCESS', progress=100, result=retval)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        self.update_task_status(task_id, 'FAILURE', error=str(exc))
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying: {exc}")
        self.update_task_status(task_id, 'RETRY', error=str(exc))
        
    def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        progress: int = None,
        result: Dict[str, Any] = None,
        error: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Update task status in database"""
        try:
            import asyncio
            
            async def _update():
                update_data = {
                    'status': status.lower(),
                    'last_updated': datetime.utcnow()
                }
                
                if progress is not None:
                    update_data['progress'] = progress
                if result is not None:
                    update_data['result'] = result
                if error is not None:
                    update_data['error'] = error
                if metadata is not None:
                    update_data['metadata'] = metadata
                    
                if status.upper() == 'STARTED':
                    update_data['started_at'] = datetime.utcnow()
                elif status.upper() in ['SUCCESS', 'FAILURE']:
                    update_data['completed_at'] = datetime.utcnow()
                
                await self.db.task_status.update_one(
                    {'task_id': task_id},
                    {'$set': update_data}
                )
            
            # Run async update in current event loop or create new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task for running loop
                    asyncio.create_task(_update())
                else:
                    loop.run_until_complete(_update())
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(_update())
                
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    def update_progress(self, task_id: str, progress: int, message: str = None):
        """Update task progress"""
        metadata = {'message': message} if message else None
        self.update_task_status(task_id, 'PROGRESS', progress=progress, metadata=metadata)