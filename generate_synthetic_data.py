"""
Script to generate synthetic interaction data for Learning-to-Rank system testing
This creates realistic recruiter interaction patterns for initial algorithm training
"""

import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from typing import List, Dict
import uuid

# Add backend to path
sys.path.append('/app/backend')

from models import RecruiterInteraction, InteractionType

# Configuration
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# Interaction patterns (realistic recruiter behavior)
INTERACTION_PATTERNS = {
    # High-scoring candidates get more positive interactions
    'high_score': {
        InteractionType.CLICK: 0.9,
        InteractionType.SHORTLIST: 0.7,
        InteractionType.APPLICATION: 0.4,
        InteractionType.INTERVIEW: 0.2,
        InteractionType.HIRE: 0.1,
        InteractionType.REJECT: 0.05
    },
    'medium_score': {
        InteractionType.CLICK: 0.6,
        InteractionType.SHORTLIST: 0.3,
        InteractionType.APPLICATION: 0.15,
        InteractionType.INTERVIEW: 0.05,
        InteractionType.HIRE: 0.02,
        InteractionType.REJECT: 0.1
    },
    'low_score': {
        InteractionType.CLICK: 0.3,
        InteractionType.SHORTLIST: 0.1,
        InteractionType.APPLICATION: 0.05,
        InteractionType.INTERVIEW: 0.01,
        InteractionType.HIRE: 0.005,
        InteractionType.REJECT: 0.2
    }
}

class SyntheticDataGenerator:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    async def get_sample_data(self) -> Dict:
        """Get sample candidates and jobs for synthetic data generation"""
        try:
            # Get sample recruiters
            recruiters = await self.db.users.find({'role': 'recruiter'}).to_list(10)
            if not recruiters:
                print("No recruiters found in database. Please ensure users are seeded.")
                return {}
            
            # Get sample candidates
            candidates = await self.db.candidates.find().to_list(100)
            if not candidates:
                print("No candidates found in database. Please add some candidates first.")
                return {}
            
            # Get sample jobs
            jobs = await self.db.job_postings.find().to_list(50)
            if not jobs:
                print("No jobs found in database. Please add some job postings first.")
                return {}
            
            return {
                'recruiters': recruiters,
                'candidates': candidates,
                'jobs': jobs
            }
            
        except Exception as e:
            print(f"Error getting sample data: {e}")
            return {}
    
    def calculate_candidate_score_tier(self, candidate: Dict, job: Dict) -> str:
        """
        Calculate which score tier a candidate falls into for a job
        This simulates the current scoring algorithm
        """
        try:
            candidate_skills = set(candidate.get('skills', []))
            required_skills = set(job.get('required_skills', []))
            
            # Simple skill overlap calculation
            skill_overlap = len(candidate_skills.intersection(required_skills)) / max(len(required_skills), 1)
            
            # Simple experience match
            candidate_exp = candidate.get('experience_years', 0)
            required_exp = job.get('min_experience_years', 0)
            exp_match = min(candidate_exp / max(required_exp, 1), 2.0) / 2.0  # Cap at 2x requirement
            
            # Combine scores (simplified semantic similarity as random for synthetic data)
            semantic_sim = random.uniform(0.3, 0.9)  # Simulate semantic similarity
            
            total_score = (semantic_sim * 0.4) + (skill_overlap * 0.4) + (exp_match * 0.2)
            
            if total_score >= 0.7:
                return 'high_score'
            elif total_score >= 0.4:
                return 'medium_score'
            else:
                return 'low_score'
                
        except Exception as e:
            print(f"Error calculating score tier: {e}")
            return 'low_score'
    
    async def generate_interactions(self, num_interactions: int = 200) -> List[RecruiterInteraction]:
        """Generate synthetic recruiter interactions"""
        try:
            sample_data = await self.get_sample_data()
            if not sample_data:
                return []
            
            interactions = []
            
            for _ in range(num_interactions):
                # Random selections
                recruiter = random.choice(sample_data['recruiters'])
                candidate = random.choice(sample_data['candidates'])
                job = random.choice(sample_data['jobs'])
                
                # Calculate score tier for this candidate-job pair
                score_tier = self.calculate_candidate_score_tier(candidate, job)
                
                # Select interaction type based on score tier probabilities
                interaction_probs = INTERACTION_PATTERNS[score_tier]
                interaction_type = self.weighted_choice(interaction_probs)
                
                if interaction_type is None:  # No interaction
                    continue
                
                # Generate realistic search position (better candidates appear higher)
                if score_tier == 'high_score':
                    search_position = random.randint(1, 5)
                elif score_tier == 'medium_score':
                    search_position = random.randint(3, 8)
                else:
                    search_position = random.randint(5, 15)
                
                # Generate timestamp (last 30 days)
                timestamp = datetime.utcnow() - timedelta(
                    days=random.uniform(0, 30),
                    hours=random.uniform(0, 24),
                    minutes=random.uniform(0, 60)
                )
                
                # Calculate synthetic scores based on our score tier
                if score_tier == 'high_score':
                    semantic_score = random.uniform(0.7, 0.95)
                    skill_overlap_score = random.uniform(0.6, 1.0)
                    experience_match_score = random.uniform(0.5, 1.0)
                elif score_tier == 'medium_score':
                    semantic_score = random.uniform(0.4, 0.7)
                    skill_overlap_score = random.uniform(0.3, 0.7)
                    experience_match_score = random.uniform(0.2, 0.8)
                else:
                    semantic_score = random.uniform(0.1, 0.5)
                    skill_overlap_score = random.uniform(0.0, 0.4)
                    experience_match_score = random.uniform(0.0, 0.6)
                
                total_score = (semantic_score * 0.4) + (skill_overlap_score * 0.4) + (experience_match_score * 0.2)
                
                # Create interaction
                interaction = RecruiterInteraction(
                    recruiter_id=recruiter['id'],
                    candidate_id=candidate['id'],
                    job_id=job['id'],
                    interaction_type=interaction_type,
                    search_position=search_position,
                    original_score=total_score,
                    semantic_score=semantic_score,
                    skill_overlap_score=skill_overlap_score,
                    experience_match_score=experience_match_score,
                    timestamp=timestamp,
                    session_id=str(uuid.uuid4())
                )
                
                interactions.append(interaction)
            
            print(f"Generated {len(interactions)} synthetic interactions")
            return interactions
            
        except Exception as e:
            print(f"Error generating interactions: {e}")
            return []
    
    def weighted_choice(self, choices: Dict) -> InteractionType:
        """Select interaction type based on weighted probabilities"""
        total = sum(choices.values())
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices.items():
            if upto + weight >= r:
                return choice
            upto += weight
        return None
    
    async def insert_interactions(self, interactions: List[RecruiterInteraction]):
        """Insert interactions into database"""
        try:
            if not interactions:
                print("No interactions to insert")
                return
            
            # Convert to dictionaries for insertion
            interaction_dicts = []
            for interaction in interactions:
                interaction_dict = interaction.dict()
                
                # Calculate reward value based on interaction type (same as in learning engine)
                reward_values = {
                    InteractionType.CLICK: 0.1,
                    InteractionType.SHORTLIST: 0.3,
                    InteractionType.APPLICATION: 0.7,
                    InteractionType.INTERVIEW: 0.9,
                    InteractionType.HIRE: 1.0,
                    InteractionType.REJECT: -0.5
                }
                
                interaction_dict['feedback_value'] = reward_values.get(interaction.interaction_type, 0.0)
                
                # Add position bonus
                if interaction.search_position:
                    position_bonus = max(0, (10 - interaction.search_position) / 10 * 0.2)
                    interaction_dict['feedback_value'] += position_bonus
                
                interaction_dicts.append(interaction_dict)
            
            # Insert into database
            await self.db.recruiter_interactions.insert_many(interaction_dicts)
            print(f"Successfully inserted {len(interaction_dicts)} interactions into database")
            
            # Print summary statistics
            interaction_types = {}
            for interaction in interactions:
                interaction_types[interaction.interaction_type] = interaction_types.get(interaction.interaction_type, 0) + 1
            
            print("\nInteraction summary:")
            for interaction_type, count in interaction_types.items():
                print(f"  {interaction_type}: {count}")
            
        except Exception as e:
            print(f"Error inserting interactions: {e}")

async def main():
    """Main function to generate synthetic data"""
    print("Generating synthetic interaction data for Learning-to-Rank system...")
    
    generator = SyntheticDataGenerator()
    
    try:
        await generator.connect()
        
        # Generate interactions
        interactions = await generator.generate_interactions(num_interactions=300)
        
        if interactions:
            await generator.insert_interactions(interactions)
            print("\n✅ Synthetic data generation completed successfully!")
            print("The Learning-to-Rank system now has training data to optimize weights.")
        else:
            print("\n❌ Failed to generate synthetic data")
            
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        await generator.close()

if __name__ == "__main__":
    asyncio.run(main())