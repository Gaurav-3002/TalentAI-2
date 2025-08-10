"""
Embedding generation tasks
"""
import logging
import asyncio
from typing import List, Dict, Any
from celery import shared_task
from tasks.base_task import BaseJobMatcherTask

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseJobMatcherTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def generate_embedding_batch(
    self,
    task_id: str,
    texts: List[str],
    batch_name: str = "batch"
) -> Dict[str, Any]:
    """
    Generate embeddings for a batch of texts asynchronously
    """
    logger.info(f"Starting batch embedding generation for task {task_id} - {batch_name}")
    
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_generate_batch_embeddings_internal(
            self, task_id, texts, batch_name
        ))
        return result
        
    except Exception as e:
        logger.error(f"Batch embedding generation failed for task {task_id}: {e}")
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _generate_batch_embeddings_internal(
    task_instance,
    task_id: str,
    texts: List[str],
    batch_name: str
) -> Dict[str, Any]:
    """Internal batch embedding generation logic"""
    
    try:
        from embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        embeddings = []
        total_texts = len(texts)
        
        task_instance.update_progress(task_id, 10, f"Processing {total_texts} texts...")
        
        # Process embeddings with progress updates
        for i, text in enumerate(texts):
            try:
                embedding = await embedding_service.generate_single_embedding(text)
                embeddings.append(embedding or [])
                
                # Update progress every 10% or every 10 items
                if i % max(1, total_texts // 10) == 0 or i % 10 == 0:
                    progress = min(90, 10 + int((i + 1) / total_texts * 80))
                    task_instance.update_progress(
                        task_id, progress, 
                        f"Generated {i + 1}/{total_texts} embeddings"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i}: {e}")
                embeddings.append([])  # Empty embedding on failure
        
        task_instance.update_progress(task_id, 100, "Batch embedding generation completed")
        
        result = {
            "batch_name": batch_name,
            "total_processed": len(texts),
            "successful_embeddings": sum(1 for emb in embeddings if emb),
            "failed_embeddings": sum(1 for emb in embeddings if not emb),
            "embeddings": embeddings
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Batch embedding generation error: {e}")
        task_instance.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

@shared_task(bind=True, base=BaseJobMatcherTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 60})
def regenerate_all_embeddings(
    self,
    task_id: str,
    collection_name: str = "candidates"
) -> Dict[str, Any]:
    """
    Regenerate embeddings for all documents in a collection
    """
    logger.info(f"Starting full embedding regeneration for {collection_name}")
    
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_regenerate_embeddings_internal(
            self, task_id, collection_name
        ))
        return result
        
    except Exception as e:
        logger.error(f"Embedding regeneration failed for task {task_id}: {e}")
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _regenerate_embeddings_internal(
    task_instance,
    task_id: str,
    collection_name: str
) -> Dict[str, Any]:
    """Internal embedding regeneration logic"""
    
    try:
        from embedding_service import EmbeddingService
        from models import Candidate, JobPosting
        
        embedding_service = EmbeddingService()
        collection = getattr(task_instance.db, collection_name)
        
        # Get all documents
        documents = await collection.find().to_list(10000)
        total_docs = len(documents)
        
        if total_docs == 0:
            return {"message": f"No documents found in {collection_name}"}
        
        task_instance.update_progress(
            task_id, 10, 
            f"Found {total_docs} documents to process in {collection_name}"
        )
        
        updated_count = 0
        failed_count = 0
        
        for i, doc in enumerate(documents):
            try:
                # Get text content based on collection type
                if collection_name == "candidates":
                    candidate = Candidate(**doc)
                    text_content = candidate.resume_text
                    doc_id = candidate.id
                elif collection_name == "job_postings":
                    job = JobPosting(**doc)
                    text_content = f"{job.title} {job.company} {job.description} {' '.join(job.required_skills)} {job.location}"
                    doc_id = job.id
                else:
                    continue
                
                # Generate new embedding
                new_embedding = await embedding_service.generate_single_embedding(text_content)
                
                if new_embedding:
                    # Update document with new embedding
                    await collection.update_one(
                        {"id": doc_id},
                        {"$set": {"embedding": new_embedding}}
                    )
                    updated_count += 1
                else:
                    failed_count += 1
                
                # Update progress
                if i % max(1, total_docs // 20) == 0:
                    progress = min(90, 10 + int((i + 1) / total_docs * 80))
                    task_instance.update_progress(
                        task_id, progress,
                        f"Updated {updated_count} embeddings, {failed_count} failed"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to update embedding for document {i}: {e}")
                failed_count += 1
        
        task_instance.update_progress(task_id, 100, "Embedding regeneration completed")
        
        result = {
            "collection": collection_name,
            "total_documents": total_docs,
            "updated_embeddings": updated_count,
            "failed_embeddings": failed_count,
            "success_rate": (updated_count / total_docs * 100) if total_docs > 0 else 0
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Embedding regeneration error: {e}")
        task_instance.update_task_status(task_id, 'FAILURE', error=str(e))
        raise