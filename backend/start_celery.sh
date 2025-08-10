#!/bin/bash
# Celery startup script

cd /app/backend

echo "Starting Celery worker..."
python -m celery -A celery_app worker --loglevel=info --concurrency=2 --queues=resume,embeddings,search,learning,celery --detach

echo "Starting Celery beat scheduler..."
python -m celery -A celery_app beat --loglevel=info --detach

echo "Starting Flower monitoring dashboard..."
python -m celery -A celery_app flower --port=5555 --detach

echo "Celery services started successfully!"
echo "Flower dashboard: http://localhost:5555"