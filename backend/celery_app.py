"""
Celery configuration for async processing
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Celery broker URL
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB + 1}"

# Create Celery application
celery_app = Celery(
    "job_matcher_workers",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "tasks.resume_tasks",
        "tasks.embedding_tasks", 
        "tasks.search_tasks",
        "tasks.learning_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing and execution
    task_routes={
        'tasks.resume_tasks.*': {'queue': 'resume'},
        'tasks.embedding_tasks.*': {'queue': 'embeddings'},
        'tasks.search_tasks.*': {'queue': 'search'},
        'tasks.learning_tasks.*': {'queue': 'learning'},
    },
    
    # Task result expiration
    result_expires=3600,  # 1 hour
    
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    task_track_started=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-tasks': {
            'task': 'tasks.maintenance_tasks.cleanup_expired_tasks',
            'schedule': 3600.0,  # Every hour
        },
        'retrain-learning-models': {
            'task': 'tasks.learning_tasks.periodic_retrain',
            'schedule': 86400.0,  # Daily
        },
    },
)

# Task priority configuration
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_disable_rate_limits = True

if __name__ == '__main__':
    celery_app.start()