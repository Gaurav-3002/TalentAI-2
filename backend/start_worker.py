#!/usr/bin/env python3
"""
Celery worker startup script
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from celery_app import celery_app

if __name__ == '__main__':
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Adjust based on your needs
        '--queues=resume,embeddings,search,learning,celery',
        '--hostname=worker@%h'
    ])