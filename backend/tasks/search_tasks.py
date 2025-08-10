"""
Search and matching tasks
"""
import logging
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime
from celery import shared_task
from tasks.base_task import BaseJobMatcherTask

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseJobMatcherTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def search_candidates_async(
    self,
    task_id: str,
    job_id: str,
    k: int = 10,
    blind_screening: bool = False,
    user_id: str = "",
    session_id: str = ""
) -> Dict[str, Any]:
    """
    Asynchronously search and rank candidates for a job
    """
    logger.info(f"Starting async candidate search for job {job_id}, task {task_id}")
    
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_search_candidates_internal(
            self, task_id, job_id, k, blind_screening, user_id, session_id
        ))
        return result
        
    except Exception as e:
        logger.error(f"Candidate search failed for task {task_id}: {e}")
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _search_candidates_internal(
    task_instance,
    task_id: str,
    job_id: str,
    k: int,
    blind_screening: bool,
    user_id: str,
    session_id: str
) -> Dict[str, Any]:
    """Internal async candidate search logic"""
    
    try:
        from models import JobPosting, Candidate, MatchResult, AsyncSearchResult
        import numpy as np
        
        start_time = time.time()
        
        # Step 1: Get job posting (10% progress)
        task_instance.update_progress(task_id, 10, "Loading job posting...")
        
        job = await task_instance.db.job_postings.find_one({"id": job_id})
        if not job:
            raise ValueError("Job posting not found")
        
        job_obj = JobPosting(**job)
        
        # Step 2: Get optimal weights (20% progress)
        task_instance.update_progress(task_id, 20, "Getting ML-optimized weights...")
        
        weights = await _get_optimal_weights(task_instance, job_obj, user_id)
        
        # Step 3: Get all candidates (30% progress)
        task_instance.update_progress(task_id, 30, "Loading candidates...")
        
        candidates_cursor = task_instance.db.candidates.find()
        candidates = await candidates_cursor.to_list(10000)
        
        if not candidates:
            return AsyncSearchResult(
                matches=[], 
                total_candidates_searched=0, 
                search_time_ms=0,
                weights_used=weights
            ).dict()
        
        # Step 4: Calculate scores (40-80% progress)
        task_instance.update_progress(task_id, 40, f"Calculating scores for {len(candidates)} candidates...")
        
        matches = []
        total_candidates = len(candidates)
        
        for i, candidate_data in enumerate(candidates):
            candidate = Candidate(**candidate_data)
            
            # Log access for compliance
            await _log_candidate_access(
                task_instance, user_id, candidate, job_obj, blind_screening, session_id
            )
            
            # Calculate scores
            scores = await _calculate_candidate_scores(
                task_instance, candidate, job_obj, weights
            )
            
            # Create match result
            match_result = MatchResult.from_candidate_and_scores(
                candidate=candidate,
                total_score=scores['total'],
                semantic_score=scores['semantic'],
                skill_overlap_score=scores['skill'],
                experience_score=scores['experience'],
                score_breakdown=scores['breakdown'],
                blind_screening=blind_screening
            )
            
            matches.append(match_result)
            
            # Update progress every 10% of candidates
            if i % max(1, total_candidates // 4) == 0:
                progress = min(80, 40 + int((i + 1) / total_candidates * 40))
                task_instance.update_progress(
                    task_id, progress,
                    f"Processed {i + 1}/{total_candidates} candidates"
                )
        
        # Step 5: Sort and limit results (90% progress)
        task_instance.update_progress(task_id, 90, "Ranking candidates...")
        
        matches.sort(key=lambda x: x.total_score, reverse=True)
        top_matches = matches[:k]
        
        # Step 6: Cache results (95% progress)
        task_instance.update_progress(task_id, 95, "Caching results...")
        
        await _cache_search_results(
            task_instance, job_id, session_id, top_matches, weights
        )
        
        # Complete
        search_time = int((time.time() - start_time) * 1000)
        task_instance.update_progress(task_id, 100, f"Search completed in {search_time}ms")
        
        result = AsyncSearchResult(
            matches=top_matches,
            total_candidates_searched=total_candidates,
            search_time_ms=search_time,
            weights_used=weights
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Candidate search error: {e}")
        task_instance.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _get_optimal_weights(task_instance, job_obj, user_id: str) -> Dict[str, float]:
    """Get ML-optimized weights for search"""
    try:
        from learning_to_rank import LearningToRankEngine
        
        learning_engine = LearningToRankEngine()
        optimal_weights = await learning_engine.get_optimal_weights(
            job_category=job_obj.title,
            recruiter_id=user_id
        )
        
        return {
            'semantic': optimal_weights.semantic_weight,
            'skill': optimal_weights.skill_weight,
            'experience': optimal_weights.experience_weight
        }
    except Exception as e:
        logger.error(f"Failed to get optimal weights: {e}")
        # Fallback to default weights
        return {'semantic': 0.4, 'skill': 0.4, 'experience': 0.2}

async def _calculate_candidate_scores(
    task_instance, candidate, job_obj, weights
) -> Dict[str, Any]:
    """Calculate all scores for a candidate"""
    
    # Calculate semantic similarity
    semantic_score = 0.0
    try:
        if candidate.embedding and job_obj.embedding:
            from server import calculate_similarity
            semantic_score = calculate_similarity(candidate.embedding, job_obj.embedding)
    except Exception as e:
        logger.error(f"Semantic score calculation failed: {e}")
    
    # Calculate skill overlap
    try:
        from server import calculate_skill_overlap
        skill_overlap = calculate_skill_overlap(candidate.skills, job_obj.required_skills)
    except Exception as e:
        logger.error(f"Skill overlap calculation failed: {e}")
        skill_overlap = 0.0
    
    # Calculate experience match
    try:
        from server import calculate_experience_match
        experience_match = calculate_experience_match(
            candidate.experience_years, 
            job_obj.min_experience_years
        )
    except Exception as e:
        logger.error(f"Experience match calculation failed: {e}")
        experience_match = 0.0
    
    # Calculate total score
    total_score = (
        semantic_score * weights['semantic'] +
        skill_overlap * weights['skill'] +
        experience_match * weights['experience']
    )
    
    score_breakdown = {
        "semantic_weight": weights['semantic'],
        "skill_overlap_weight": weights['skill'],
        "experience_weight": weights['experience'],
        "matched_skills": list(set(candidate.skills).intersection(set(job_obj.required_skills))),
        "missing_skills": list(set(job_obj.required_skills) - set(candidate.skills))
    }
    
    return {
        'total': total_score,
        'semantic': semantic_score,
        'skill': skill_overlap,
        'experience': experience_match,
        'breakdown': score_breakdown
    }

async def _log_candidate_access(
    task_instance, user_id: str, candidate, job_obj, blind_screening: bool, session_id: str
):
    """Log candidate access for compliance"""
    try:
        from models import AccessLog, AccessReason
        
        access_log = AccessLog(
            user_id=user_id,
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            reason=AccessReason.SEARCH,
            details=f"Search for job: {job_obj.title} at {job_obj.company}, blind_mode={blind_screening}",
            session_id=session_id,
            ip_address="async_task"
        )
        
        await task_instance.db.access_logs.insert_one(access_log.dict())
        
    except Exception as e:
        logger.error(f"Failed to log candidate access: {e}")

async def _cache_search_results(
    task_instance, job_id: str, session_id: str, matches: List, weights: Dict[str, float]
):
    """Cache search results for learning purposes"""
    try:
        cache_entry = {
            "session_id": session_id,
            "job_id": job_id,
            "timestamp": datetime.utcnow(),
            "weights_used": weights,
            "candidate_rankings": [
                {
                    "candidate_id": match.candidate_id,
                    "position": i + 1,
                    "total_score": match.total_score,
                    "semantic_score": match.semantic_score,
                    "skill_overlap_score": match.skill_overlap_score,
                    "experience_score": match.experience_score
                }
                for i, match in enumerate(matches)
            ]
        }
        
        await task_instance.db.search_cache.insert_one(cache_entry)
        
        # Set TTL for cache cleanup (30 minutes)
        await task_instance.db.search_cache.create_index(
            "timestamp", expireAfterSeconds=1800
        )
        
    except Exception as e:
        logger.error(f"Failed to cache search results: {e}")

@shared_task(bind=True, base=BaseJobMatcherTask)
def bulk_candidate_matching(
    self,
    task_id: str,
    job_ids: List[str],
    search_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run candidate matching for multiple jobs in bulk
    """
    logger.info(f"Starting bulk candidate matching for {len(job_ids)} jobs")
    
    self.update_task_status(task_id, 'STARTED', progress=5)
    
    try:
        result = asyncio.run(_bulk_matching_internal(
            self, task_id, job_ids, search_params
        ))
        return result
        
    except Exception as e:
        logger.error(f"Bulk matching failed for task {task_id}: {e}")
        self.update_task_status(task_id, 'FAILURE', error=str(e))
        raise

async def _bulk_matching_internal(
    task_instance,
    task_id: str,
    job_ids: List[str],
    search_params: Dict[str, Any]
) -> Dict[str, Any]:
    """Internal bulk matching logic"""
    
    results = {}
    total_jobs = len(job_ids)
    
    for i, job_id in enumerate(job_ids):
        try:
            search_result = await _search_candidates_internal(
                task_instance, f"{task_id}_job_{i}", job_id,
                search_params.get('k', 10),
                search_params.get('blind_screening', False),
                search_params.get('user_id', ''),
                search_params.get('session_id', '')
            )
            
            results[job_id] = search_result
            
            # Update progress
            progress = min(95, 5 + int((i + 1) / total_jobs * 90))
            task_instance.update_progress(
                task_id, progress,
                f"Completed matching for job {i + 1}/{total_jobs}"
            )
            
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            results[job_id] = {"error": str(e)}
    
    task_instance.update_progress(task_id, 100, "Bulk matching completed")
    
    return {
        "total_jobs": total_jobs,
        "successful_jobs": sum(1 for r in results.values() if "error" not in r),
        "failed_jobs": sum(1 for r in results.values() if "error" in r),
        "results": results
    }