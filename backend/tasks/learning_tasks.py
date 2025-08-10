"""
Learning-to-Rank training tasks
"""
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from celery import shared_task
from tasks.base_task import BaseJobMatcherTask

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseJobMatcherTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 120})
def retrain_learning_model(
    self,
    task_id: str,
    job_category: str = None,
    recruiter_id: str = None,
    force_retrain: bool = False
) -> Dict[str, Any]:
    """
    Retrain the Learning-to-Rank model with latest interaction data
    """
    logger.info(f"Starting learning model retraining for task {task_id}")
    
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_retrain_model_internal(
            self, task_id, job_category, recruiter_id, force_retrain
        ))
        return result
        
    except Exception as e:
        logger.error(f"Model retraining failed for task {task_id}: {e}")
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _retrain_model_internal(
    task_instance,
    task_id: str,
    job_category: str = None,
    recruiter_id: str = None,
    force_retrain: bool = False
) -> Dict[str, Any]:
    """Internal model retraining logic"""
    
    try:
        from learning_to_rank import LearningToRankEngine
        
        learning_engine = LearningToRankEngine()
        
        # Step 1: Check if retraining is needed (10% progress)
        task_instance.update_progress(task_id, 10, "Checking retraining requirements...")
        
        if not force_retrain:
            # Check interaction count and last training time
            interaction_count = await task_instance.db.recruiter_interactions.count_documents({})
            if interaction_count < 50:  # Minimum interactions needed
                return {
                    "status": "skipped",
                    "reason": f"Insufficient interactions ({interaction_count} < 50)",
                    "interaction_count": interaction_count
                }
        
        # Step 2: Load interaction data (30% progress)
        task_instance.update_progress(task_id, 30, "Loading interaction data...")
        
        # Get recent interactions (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        interactions = await task_instance.db.recruiter_interactions.find({
            "timestamp": {"$gte": cutoff_date}
        }).to_list(10000)
        
        if len(interactions) < 10:  # Need minimum interactions for meaningful training
            return {
                "status": "skipped",
                "reason": f"Insufficient recent interactions ({len(interactions)} < 10)",
                "interaction_count": len(interactions)
            }
        
        # Step 3: Prepare training data (50% progress)
        task_instance.update_progress(task_id, 50, "Preparing training data...")
        
        training_data = await _prepare_training_data(task_instance, interactions)
        
        # Step 4: Train model (70% progress)
        task_instance.update_progress(task_id, 70, "Training model...")
        
        training_result = await learning_engine.retrain_with_data(training_data)
        
        # Step 5: Validate model performance (85% progress)
        task_instance.update_progress(task_id, 85, "Validating model performance...")
        
        validation_metrics = await _validate_model_performance(
            task_instance, learning_engine, training_data
        )
        
        # Step 6: Update weights in database (95% progress)
        task_instance.update_progress(task_id, 95, "Updating optimal weights...")
        
        await _update_optimal_weights(
            task_instance, learning_engine, job_category, recruiter_id
        )
        
        task_instance.update_progress(task_id, 100, "Model retraining completed")
        
        result = {
            "status": "completed",
            "interaction_count": len(interactions),
            "training_samples": len(training_data),
            "model_performance": validation_metrics,
            "training_result": training_result,
            "retrained_at": datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Model retraining error: {e}")
        task_instance.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _prepare_training_data(task_instance, interactions) -> list:
    """Prepare training data from recruiter interactions"""
    training_data = []
    
    for interaction in interactions:
        try:
            # Get the original search context
            search_cache = await task_instance.db.search_cache.find_one({
                "session_id": interaction.get("session_id"),
                "job_id": interaction.get("job_id")
            })
            
            if search_cache:
                # Find the candidate's position in the search results
                candidate_ranking = None
                for rank in search_cache.get("candidate_rankings", []):
                    if rank["candidate_id"] == interaction["candidate_id"]:
                        candidate_ranking = rank
                        break
                
                if candidate_ranking:
                    # Create training sample
                    sample = {
                        "job_id": interaction["job_id"],
                        "candidate_id": interaction["candidate_id"],
                        "interaction_type": interaction["interaction_type"],
                        "reward": interaction["reward"],
                        "position": candidate_ranking["position"],
                        "semantic_score": candidate_ranking["semantic_score"],
                        "skill_overlap_score": candidate_ranking["skill_overlap_score"],
                        "experience_score": candidate_ranking["experience_score"],
                        "total_score": candidate_ranking["total_score"],
                        "weights_used": search_cache.get("weights_used", {}),
                        "timestamp": interaction["timestamp"]
                    }
                    training_data.append(sample)
                    
        except Exception as e:
            logger.error(f"Failed to prepare training sample: {e}")
            continue
    
    return training_data

async def _validate_model_performance(task_instance, learning_engine, training_data) -> Dict[str, float]:
    """Validate the performance of the retrained model"""
    
    try:
        # Calculate basic performance metrics
        total_samples = len(training_data)
        positive_interactions = sum(1 for sample in training_data if sample["reward"] > 0)
        negative_interactions = sum(1 for sample in training_data if sample["reward"] < 0)
        
        # Calculate average reward by position (to check ranking quality)
        position_rewards = {}
        for sample in training_data:
            pos = sample["position"]
            if pos not in position_rewards:
                position_rewards[pos] = []
            position_rewards[pos].append(sample["reward"])
        
        avg_reward_by_position = {
            pos: sum(rewards) / len(rewards) 
            for pos, rewards in position_rewards.items()
        }
        
        # Calculate model confidence (simplified)
        weights_variance = 0.0
        recent_weights = await task_instance.db.learning_weights.find().sort("last_updated", -1).limit(5).to_list(5)
        if len(recent_weights) > 1:
            # Calculate variance in recent weight updates as a confidence measure
            semantic_weights = [w["semantic_weight"] for w in recent_weights]
            skill_weights = [w["skill_weight"] for w in recent_weights]
            experience_weights = [w["experience_weight"] for w in recent_weights]
            
            import numpy as np
            weights_variance = (
                np.var(semantic_weights) + 
                np.var(skill_weights) + 
                np.var(experience_weights)
            ) / 3
        
        return {
            "total_samples": total_samples,
            "positive_interactions": positive_interactions,
            "negative_interactions": negative_interactions,
            "positive_ratio": positive_interactions / total_samples if total_samples > 0 else 0,
            "avg_reward_by_position": avg_reward_by_position,
            "weights_variance": float(weights_variance),
            "model_confidence": max(0.1, min(1.0, 1.0 - weights_variance)) if weights_variance > 0 else 0.8
        }
        
    except Exception as e:
        logger.error(f"Model validation error: {e}")
        return {"error": str(e)}

async def _update_optimal_weights(
    task_instance, learning_engine, job_category: str = None, recruiter_id: str = None
):
    """Update the optimal weights in the database"""
    
    try:
        # Get the newly trained optimal weights
        optimal_weights = await learning_engine.get_optimal_weights(
            job_category=job_category,
            recruiter_id=recruiter_id
        )
        
        # Update in database
        await task_instance.db.learning_weights.update_one(
            {
                "job_category": job_category,
                "recruiter_id": recruiter_id
            },
            {
                "$set": {
                    "semantic_weight": optimal_weights.semantic_weight,
                    "skill_weight": optimal_weights.skill_weight,
                    "experience_weight": optimal_weights.experience_weight,
                    "confidence_score": optimal_weights.confidence_score,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
        
    except Exception as e:
        logger.error(f"Failed to update optimal weights: {e}")

@shared_task(bind=True, base=BaseJobMatcherTask)
def periodic_retrain(self, task_id: str = None) -> Dict[str, Any]:
    """
    Periodic retraining task (called by Celery Beat)
    """
    if not task_id:
        task_id = f"periodic_retrain_{datetime.utcnow().isoformat()}"
    
    logger.info(f"Starting periodic model retraining")
    
    try:
        result = asyncio.run(_periodic_retrain_internal(self, task_id))
        return result
        
    except Exception as e:
        logger.error(f"Periodic retraining failed: {e}")
        raise

async def _periodic_retrain_internal(task_instance, task_id: str) -> Dict[str, Any]:
    """Internal periodic retraining logic"""
    
    try:
        # Check if we have enough new interactions since last training
        last_training = await task_instance.db.learning_weights.find_one(
            sort=[("last_updated", -1)]
        )
        
        cutoff_date = datetime.utcnow() - timedelta(hours=24)  # Last 24 hours
        if last_training:
            cutoff_date = max(cutoff_date, last_training["last_updated"])
        
        new_interactions = await task_instance.db.recruiter_interactions.count_documents({
            "timestamp": {"$gte": cutoff_date}
        })
        
        if new_interactions < 20:  # Need at least 20 new interactions
            return {
                "status": "skipped",
                "reason": f"Insufficient new interactions ({new_interactions} < 20)",
                "new_interactions": new_interactions
            }
        
        # Run retraining
        retrain_result = await _retrain_model_internal(
            task_instance, task_id, force_retrain=True
        )
        
        return {
            "status": "completed",
            "new_interactions": new_interactions,
            "retrain_result": retrain_result
        }
        
    except Exception as e:
        logger.error(f"Periodic retraining error: {e}")
        return {"status": "failed", "error": str(e)}

@shared_task(bind=True, base=BaseJobMatcherTask)
def cleanup_expired_tasks(self, task_id: str = None) -> Dict[str, Any]:
    """
    Clean up expired tasks and old data
    """
    if not task_id:
        task_id = f"cleanup_{datetime.utcnow().isoformat()}"
    
    logger.info("Starting cleanup of expired tasks")
    
    try:
        result = asyncio.run(_cleanup_internal(self, task_id))
        return result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}

async def _cleanup_internal(task_instance, task_id: str) -> Dict[str, Any]:
    """Internal cleanup logic"""
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=7)  # Keep data for 7 days
        
        # Clean up old task status records
        old_tasks = await task_instance.db.task_status.delete_many({
            "created_at": {"$lt": cutoff_date}
        })
        
        # Clean up old search cache (already has TTL, but double-check)
        old_cache = await task_instance.db.search_cache.delete_many({
            "timestamp": {"$lt": datetime.utcnow() - timedelta(hours=2)}
        })
        
        # Clean up very old access logs (keep for compliance but limit size)
        very_old_logs = await task_instance.db.access_logs.delete_many({
            "timestamp": {"$lt": datetime.utcnow() - timedelta(days=90)}
        })
        
        return {
            "status": "completed",
            "cleaned_tasks": old_tasks.deleted_count,
            "cleaned_cache": old_cache.deleted_count,
            "cleaned_logs": very_old_logs.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {"status": "failed", "error": str(e)}