"""
Learning-to-Rank Algorithm Implementation
Implements reinforcement learning for dynamic weight optimization in candidate matching
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import (
    RecruiterInteraction, 
    LearningWeights, 
    InteractionType, 
    JobPosting, 
    Candidate
)
import asyncio

logger = logging.getLogger(__name__)

class LearningToRankEngine:
    """
    Learning-to-Rank engine that optimizes matching weights based on recruiter feedback
    Uses reinforcement learning principles to adapt to recruiter preferences
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=0.1)
        
        # Default weights (fallback when insufficient data)
        self.default_weights = {
            'semantic_weight': 0.4,
            'skill_weight': 0.4, 
            'experience_weight': 0.2
        }
        
        # Reward values for different interaction types
        self.reward_values = {
            InteractionType.CLICK: 0.1,
            InteractionType.SHORTLIST: 0.3,
            InteractionType.APPLICATION: 0.7,
            InteractionType.INTERVIEW: 0.9,
            InteractionType.HIRE: 1.0,
            InteractionType.REJECT: -0.5
        }
        
        # Minimum interactions needed before learning weights
        self.min_interactions_threshold = 50
        
    async def record_interaction(
        self, 
        interaction: RecruiterInteraction
    ) -> bool:
        """Record a recruiter interaction for learning"""
        try:
            # Calculate reward value based on interaction type
            interaction.feedback_value = self.reward_values.get(
                interaction.interaction_type, 0.0
            )
            
            # Adjust reward based on search position (higher positions get bonus)
            if interaction.search_position is not None:
                position_bonus = max(0, (10 - interaction.search_position) / 10 * 0.2)
                interaction.feedback_value += position_bonus
            
            # Store interaction
            await self.db.recruiter_interactions.insert_one(interaction.dict())
            
            logger.info(f"Recorded interaction: {interaction.interaction_type} "
                       f"for candidate {interaction.candidate_id} "
                       f"with reward {interaction.feedback_value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
            return False
    
    async def get_optimal_weights(
        self, 
        job_category: Optional[str] = None,
        recruiter_id: Optional[str] = None
    ) -> LearningWeights:
        """
        Get optimal weights using reinforcement learning
        Falls back to default weights if insufficient data
        """
        try:
            # Try to get existing learned weights
            query = {}
            if job_category:
                query['job_category'] = job_category
                
            existing_weights = await self.db.learning_weights.find_one(
                query, sort=[('last_updated', -1)]
            )
            
            # Check if we have enough interactions to learn from
            interaction_count = await self.db.recruiter_interactions.count_documents({})
            
            if interaction_count < self.min_interactions_threshold:
                logger.info(f"Insufficient interactions ({interaction_count} < {self.min_interactions_threshold}), "
                           "using default weights")
                return LearningWeights(**self.default_weights)
            
            # If existing weights are recent and confident, use them
            if existing_weights and self._is_weights_fresh(existing_weights):
                return LearningWeights(**existing_weights)
            
            # Learn new weights from interactions
            learned_weights = await self._learn_weights_from_interactions(
                job_category, recruiter_id
            )
            
            # Save learned weights
            await self._save_weights(learned_weights, job_category)
            
            return learned_weights
            
        except Exception as e:
            logger.error(f"Failed to get optimal weights: {e}")
            return LearningWeights(**self.default_weights)
    
    async def _learn_weights_from_interactions(
        self, 
        job_category: Optional[str] = None,
        recruiter_id: Optional[str] = None
    ) -> LearningWeights:
        """Learn optimal weights using reinforcement learning approach"""
        try:
            # Get recent interactions (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            query = {'timestamp': {'$gte': cutoff_date}}
            
            if recruiter_id:
                query['recruiter_id'] = recruiter_id
            
            interactions = await self.db.recruiter_interactions.find(query).to_list(1000)
            
            if len(interactions) < self.min_interactions_threshold:
                logger.info("Insufficient recent interactions for learning")
                return LearningWeights(**self.default_weights)
            
            # Prepare training data
            features = []
            rewards = []
            
            for interaction in interactions:
                if all(score is not None for score in [
                    interaction.get('semantic_score'),
                    interaction.get('skill_overlap_score'),
                    interaction.get('experience_match_score')
                ]):
                    features.append([
                        interaction['semantic_score'],
                        interaction['skill_overlap_score'],
                        interaction['experience_match_score']
                    ])
                    rewards.append(interaction['feedback_value'])
            
            if len(features) < 10:  # Minimum samples for ML
                logger.info("Insufficient valid interaction data for ML")
                return LearningWeights(**self.default_weights)
            
            # Train model to predict reward based on score components
            X = np.array(features)
            y = np.array(rewards)
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Fit Ridge regression model
            self.model.fit(X_scaled, y)
            
            # Extract learned weights (coefficients represent importance)
            raw_weights = np.abs(self.model.coef_)
            
            # Normalize weights to sum to 1
            weight_sum = np.sum(raw_weights)
            if weight_sum > 0:
                normalized_weights = raw_weights / weight_sum
            else:
                # Fallback if all weights are zero
                normalized_weights = np.array([0.4, 0.4, 0.2])
            
            # Calculate confidence based on R² score
            confidence = max(0.0, self.model.score(X_scaled, y))
            
            learned_weights = LearningWeights(
                semantic_weight=float(normalized_weights[0]),
                skill_weight=float(normalized_weights[1]),
                experience_weight=float(normalized_weights[2]),
                confidence_score=confidence,
                interaction_count=len(interactions),
                job_category=job_category,
                performance_metrics={
                    'r2_score': confidence,
                    'training_samples': len(features),
                    'avg_reward': float(np.mean(y))
                }
            )
            
            logger.info(f"Learned weights: semantic={normalized_weights[0]:.3f}, "
                       f"skill={normalized_weights[1]:.3f}, "
                       f"experience={normalized_weights[2]:.3f}, "
                       f"confidence={confidence:.3f}")
            
            return learned_weights
            
        except Exception as e:
            logger.error(f"Failed to learn weights from interactions: {e}")
            return LearningWeights(**self.default_weights)
    
    async def _save_weights(self, weights: LearningWeights, job_category: Optional[str] = None):
        """Save learned weights to database"""
        try:
            weights_dict = weights.dict()
            weights_dict['job_category'] = job_category
            
            await self.db.learning_weights.insert_one(weights_dict)
            logger.info(f"Saved learned weights with confidence {weights.confidence_score:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to save weights: {e}")
    
    def _is_weights_fresh(self, weights_doc: dict) -> bool:
        """Check if existing weights are fresh enough to use"""
        if not weights_doc:
            return False
            
        # Consider weights fresh if updated within last 7 days and have good confidence
        last_updated = weights_doc.get('last_updated', datetime.min)
        confidence = weights_doc.get('confidence_score', 0)
        
        is_recent = (datetime.utcnow() - last_updated).days < 7
        is_confident = confidence > 0.3
        
        return is_recent and is_confident
    
    async def update_weights_with_feedback(
        self, 
        candidate_id: str, 
        job_id: str,
        feedback_type: InteractionType,
        search_scores: Dict[str, float]
    ) -> bool:
        """
        Update the learning model with immediate feedback
        This allows for real-time learning adaptation
        """
        try:
            # Create interaction record
            interaction = RecruiterInteraction(
                recruiter_id="system",  # System-generated feedback
                candidate_id=candidate_id,
                job_id=job_id,
                interaction_type=feedback_type,
                semantic_score=search_scores.get('semantic_score'),
                skill_overlap_score=search_scores.get('skill_overlap_score'),
                experience_match_score=search_scores.get('experience_match_score'),
                original_score=search_scores.get('total_score')
            )
            
            # Record the interaction
            success = await self.record_interaction(interaction)
            
            if success:
                # Trigger incremental learning if we have enough interactions
                interaction_count = await self.db.recruiter_interactions.count_documents({})
                
                if interaction_count > self.min_interactions_threshold:
                    # Periodically retrain (every 10 interactions)
                    if interaction_count % 10 == 0:
                        await self.get_optimal_weights()  # This will retrain
                        logger.info(f"Triggered retraining after {interaction_count} interactions")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update weights with feedback: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, any]:
        """Get performance metrics of the learning system"""
        try:
            # Get latest weights
            latest_weights = await self.db.learning_weights.find_one(
                {}, sort=[('last_updated', -1)]
            )
            
            # Get interaction statistics
            total_interactions = await self.db.recruiter_interactions.count_documents({})
            
            # Get recent performance (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_interactions = await self.db.recruiter_interactions.count_documents({
                'timestamp': {'$gte': recent_cutoff}
            })
            
            # Calculate average rewards by interaction type
            pipeline = [
                {'$group': {
                    '_id': '$interaction_type',
                    'avg_reward': {'$avg': '$feedback_value'},
                    'count': {'$sum': 1}
                }}
            ]
            
            interaction_stats = await self.db.recruiter_interactions.aggregate(pipeline).to_list(100)
            
            metrics = {
                'total_interactions': total_interactions,
                'recent_interactions': recent_interactions,
                'current_weights': latest_weights or self.default_weights,
                'interaction_breakdown': {stat['_id']: {
                    'count': stat['count'],
                    'avg_reward': stat['avg_reward']
                } for stat in interaction_stats},
                'learning_status': 'active' if total_interactions >= self.min_interactions_threshold else 'insufficient_data'
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}