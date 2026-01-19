"""
Deduplication Module

Manages job persistence and prevents duplicate notifications.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import json


class JobDatabase:
    """Manages job storage and deduplication."""
    
    def __init__(self, db_path: str = 'jobs.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                category TEXT,
                source TEXT,
                url TEXT,
                description TEXT,
                posted_date TEXT,
                discovered_date TEXT NOT NULL,
                sponsor_confidence TEXT,
                entry_level_reasoning TEXT,
                score REAL,
                sent_in_digest INTEGER DEFAULT 0,
                sent_date TEXT
            )
        ''')
        
        # Create index on job_hash for fast lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_job_hash ON jobs(job_hash)
        ''')
        
        # Create index on sent_in_digest for filtering
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sent_digest ON jobs(sent_in_digest)
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_job_hash(self, job: Dict) -> str:
        """
        Generate unique hash for a job based on company and title.
        
        Args:
            job: Job dictionary
            
        Returns:
            SHA256 hash string
        """
        # Normalize company and title
        company = job.get('company', '').lower().strip()
        title = job.get('title', '').lower().strip()
        
        # Create hash from company + title
        hash_input = f"{company}|{title}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def is_duplicate(self, job: Dict) -> bool:
        """
        Check if job already exists in database.
        
        Args:
            job: Job dictionary
            
        Returns:
            True if job is a duplicate
        """
        job_hash = self._generate_job_hash(job)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM jobs WHERE job_hash = ?', (job_hash,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
    
    def add_job(self, job: Dict) -> Optional[int]:
        """
        Add job to database if not duplicate.
        
        Args:
            job: Job dictionary
            
        Returns:
            Job ID if added, None if duplicate
        """
        if self.is_duplicate(job):
            return None
        
        job_hash = self._generate_job_hash(job)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO jobs (
                    job_hash, title, company, location, category, source, url,
                    description, posted_date, discovered_date, sponsor_confidence,
                    entry_level_reasoning, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_hash,
                job.get('title', ''),
                job.get('company', ''),
                job.get('location', ''),
                job.get('category', ''),
                job.get('source', ''),
                job.get('url', ''),
                job.get('description', ''),
                job.get('posted_date', ''),
                datetime.now().isoformat(),
                job.get('sponsor_confidence', ''),
                job.get('entry_level_reasoning', ''),
                job.get('score', 0.0)
            ))
            
            job_id = cursor.lastrowid
            conn.commit()
            
            return job_id
            
        except sqlite3.IntegrityError:
            # Duplicate hash
            return None
        finally:
            conn.close()
    
    def get_unsent_jobs(self) -> List[Dict]:
        """
        Get all jobs that haven't been sent in a digest.
        
        Returns:
            List of job dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE sent_in_digest = 0 
            ORDER BY score DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            job = dict(row)
            jobs.append(job)
        
        return jobs
    
    def mark_as_sent(self, job_ids: List[int]):
        """
        Mark jobs as sent in digest.
        
        Args:
            job_ids: List of job IDs to mark as sent
        """
        if not job_ids:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(job_ids))
        cursor.execute(f'''
            UPDATE jobs 
            SET sent_in_digest = 1, sent_date = ? 
            WHERE id IN ({placeholders})
        ''', [datetime.now().isoformat()] + job_ids)
        
        conn.commit()
        conn.close()
    
    def cleanup_old_jobs(self, days: int = 30):
        """
        Remove jobs older than specified days.
        
        Args:
            days: Number of days to keep jobs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM jobs 
            WHERE discovered_date < ?
        ''', (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"Cleaned up {deleted_count} old jobs")
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE sent_in_digest = 1')
        sent_jobs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE sent_in_digest = 0')
        unsent_jobs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_jobs': total_jobs,
            'sent_jobs': sent_jobs,
            'unsent_jobs': unsent_jobs
        }


class Deduplicator:
    """High-level deduplication interface."""
    
    def __init__(self, db_path: str = 'jobs.db'):
        self.db = JobDatabase(db_path)
    
    def filter_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter out duplicate jobs and add new ones to database.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of non-duplicate jobs
        """
        new_jobs = []
        
        for job in jobs:
            job_id = self.db.add_job(job)
            if job_id is not None:
                job['db_id'] = job_id
                new_jobs.append(job)
        
        return new_jobs
    
    def get_jobs_for_digest(self, max_count: int = 12) -> List[Dict]:
        """
        Get top jobs for daily digest.
        
        Args:
            max_count: Maximum number of jobs to include
            
        Returns:
            List of top-scored unsent jobs
        """
        unsent_jobs = self.db.get_unsent_jobs()
        return unsent_jobs[:max_count]
    
    def mark_digest_sent(self, jobs: List[Dict]):
        """Mark jobs as sent in digest."""
        job_ids = [job.get('id') for job in jobs if job.get('id')]
        self.db.mark_as_sent(job_ids)


if __name__ == '__main__':
    # Test the deduplicator
    from datetime import timedelta
    
    dedup = Deduplicator('test_jobs.db')
    
    test_jobs = [
        {
            'title': 'Data Scientist - New Grad',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'category': 'Data Scientist',
            'source': 'Indeed',
            'url': 'https://example.com/job1',
            'description': 'Test job description',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'HIGH',
            'score': 150.0
        },
        {
            'title': 'Data Scientist - New Grad',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'category': 'Data Scientist',
            'source': 'Glassdoor',
            'url': 'https://example.com/job2',
            'description': 'Same job, different source',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'HIGH',
            'score': 150.0
        }
    ]
    
    new_jobs = dedup.filter_duplicates(test_jobs)
    print(f"New jobs: {len(new_jobs)} (should be 1, duplicate filtered)")
    
    stats = dedup.db.get_stats()
    print(f"Database stats: {stats}")
