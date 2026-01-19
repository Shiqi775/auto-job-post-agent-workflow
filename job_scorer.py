"""
Job Scoring Module

Scores and ranks jobs based on multiple criteria.
"""

from typing import Dict, List
from datetime import datetime, timedelta


class JobScorer:
    """Scores and ranks jobs based on priority, sponsorship, and freshness."""
    
    def __init__(self):
        # Role priority weights (higher is better)
        self.role_weights = {
            'Data Scientist': 100,
            'Data Analyst': 80,
            'Quantitative Finance': 60,
            'Data Engineer': 40,
            'Other': 0
        }
        
        # Sponsor confidence weights
        self.sponsor_weights = {
            'HIGH': 50,
            'MEDIUM': 25,
            'LOW': 5
        }
    
    def score_job(self, job: Dict) -> float:
        """
        Calculate total score for a job.
        
        Args:
            job: Job dictionary with category, sponsor_confidence, posted_date
            
        Returns:
            Total score (higher is better)
        """
        score = 0.0
        
        # Role priority score
        category = job.get('category', 'Other')
        score += self.role_weights.get(category, 0)
        
        # Sponsor confidence score
        sponsor_conf = job.get('sponsor_confidence', 'LOW')
        score += self.sponsor_weights.get(sponsor_conf, 0)
        
        # Freshness score (0-20 points based on hours ago)
        freshness_score = self._calculate_freshness_score(job.get('posted_date'))
        score += freshness_score
        
        # Entry-level fit clarity bonus (0-10 points)
        if job.get('entry_level_reasoning'):
            clarity_score = self._calculate_clarity_score(job.get('entry_level_reasoning', ''))
            score += clarity_score
        
        return score
    
    def _calculate_freshness_score(self, posted_date) -> float:
        """Calculate freshness score based on posting time."""
        if not posted_date:
            return 0.0

        if isinstance(posted_date, str):
            try:
                posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
            except:
                return 0.0

        # Handle timezone-aware vs naive datetime
        now = datetime.now()
        if posted_date.tzinfo is not None:
            posted_date = posted_date.replace(tzinfo=None)

        hours_ago = (now - posted_date).total_seconds() / 3600

        # Linear decay: 20 points at 0 hours, 0 points at 24 hours
        if hours_ago <= 24:
            return max(0, 20 - (hours_ago * 20 / 24))

        return 0.0
    
    def _calculate_clarity_score(self, reasoning: str) -> float:
        """Calculate entry-level fit clarity score."""
        if not reasoning:
            return 0.0
        
        # Simple heuristic: longer, more detailed reasoning = higher clarity
        clarity_indicators = [
            'new grad',
            'entry level',
            'junior',
            'recent graduate',
            '0-2 years',
            'bs/ms',
            'phd'
        ]
        
        reasoning_lower = reasoning.lower()
        matches = sum(1 for indicator in clarity_indicators if indicator in reasoning_lower)
        
        # Up to 10 points based on clarity indicators
        return min(10, matches * 3)
    
    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Score and rank jobs in descending order.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Sorted list of jobs with scores
        """
        # Score each job
        for job in jobs:
            job['score'] = self.score_job(job)
        
        # Sort by score (descending)
        ranked_jobs = sorted(jobs, key=lambda x: x.get('score', 0), reverse=True)
        
        return ranked_jobs
    
    def filter_top_jobs(self, jobs: List[Dict], max_count: int = 12) -> List[Dict]:
        """
        Filter top N jobs after ranking.
        
        Args:
            jobs: List of job dictionaries
            max_count: Maximum number of jobs to return
            
        Returns:
            Top N jobs
        """
        ranked_jobs = self.rank_jobs(jobs)
        return ranked_jobs[:max_count]
    
    def should_include(self, job: Dict) -> bool:
        """
        Determine if job should be included in final list.
        
        Args:
            job: Job dictionary with score and sponsor_confidence
            
        Returns:
            True if job should be included
        """
        # Discard LOW confidence unless exceptional quality
        if job.get('sponsor_confidence') == 'LOW':
            # Only include if score is exceptionally high (>150)
            return job.get('score', 0) > 150
        
        return True


if __name__ == '__main__':
    # Test the scorer
    scorer = JobScorer()
    
    test_jobs = [
        {
            'title': 'Data Scientist - New Grad',
            'category': 'Data Scientist',
            'sponsor_confidence': 'HIGH',
            'posted_date': datetime.now() - timedelta(hours=2),
            'entry_level_reasoning': 'New grad position, 0-1 years experience'
        },
        {
            'title': 'Junior Data Analyst',
            'category': 'Data Analyst',
            'sponsor_confidence': 'MEDIUM',
            'posted_date': datetime.now() - timedelta(hours=12),
            'entry_level_reasoning': 'Junior level, entry position'
        },
        {
            'title': 'Quantitative Researcher',
            'category': 'Quantitative Finance',
            'sponsor_confidence': 'HIGH',
            'posted_date': datetime.now() - timedelta(hours=20),
            'entry_level_reasoning': 'PhD students welcome'
        }
    ]
    
    ranked = scorer.rank_jobs(test_jobs)
    
    print("Ranked Jobs:")
    for i, job in enumerate(ranked, 1):
        print(f"{i}. {job['title']} - Score: {job['score']:.2f}")
