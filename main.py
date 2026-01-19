"""
Main Orchestrator

Coordinates all modules and handles scheduling.
"""

import time
import schedule
from datetime import datetime
from typing import List, Dict
import traceback
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config.env in the same directory as this script
config_path = Path(__file__).parent / 'config.env'
if config_path.exists():
    load_dotenv(config_path)
    print(f"Loaded configuration from {config_path}")

from job_discovery import JobDiscovery
from job_classifier import JobClassifier
from sponsorship_analyzer import SponsorshipAnalyzer
from job_scorer import JobScorer
from deduplicator import Deduplicator
from email_sender import EmailDigest


class JobMonitorAgent:
    """Main autonomous job monitoring agent."""
    
    def __init__(self, config: Dict):
        """
        Initialize the job monitoring agent.
        
        Args:
            config: Configuration dictionary with email settings
        """
        self.config = config
        
        # Initialize modules
        self.discovery = JobDiscovery()
        self.classifier = JobClassifier()
        self.sponsor_analyzer = SponsorshipAnalyzer()
        self.scorer = JobScorer()
        self.deduplicator = Deduplicator(config.get('db_path', 'jobs.db'))
        
        # Initialize email sender
        self.email_sender = EmailDigest(
            smtp_server=config.get('smtp_server', 'smtp-mail.outlook.com'),
            smtp_port=config.get('smtp_port', 587),
            sender_email=config.get('sender_email', ''),
            sender_password=config.get('sender_password', '')
        )
        
        self.recipient_email = config.get('recipient_email', '')
        
        print("Job Monitor Agent initialized")
    
    def run_discovery_cycle(self):
        """
        Run a complete discovery cycle.
        
        This is the main workflow that:
        1. Discovers jobs from sources
        2. Filters and classifies them
        3. Analyzes sponsorship likelihood
        4. Scores and deduplicates
        5. Stores in database
        """
        print(f"\n{'='*60}")
        print(f"Starting discovery cycle at {datetime.now()}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Discover jobs
            print("Step 1: Discovering jobs from sources...")
            raw_jobs = self.discovery.discover_jobs()
            print(f"  → Found {len(raw_jobs)} raw job postings")
            
            if not raw_jobs:
                print("  → No jobs discovered, ending cycle")
                return
            
            # Step 2: Filter for US locations and 24-hour freshness
            print("\nStep 2: Filtering for US locations and freshness...")
            us_jobs = [
                job for job in raw_jobs 
                if self.discovery.is_us_location(job.get('location', ''))
                and self.discovery.is_within_24_hours(job.get('posted_date'))
            ]
            print(f"  → {len(us_jobs)} jobs meet location and freshness criteria")
            
            if not us_jobs:
                print("  → No jobs passed filters, ending cycle")
                return
            
            # Step 3: Fetch full descriptions and classify
            print("\nStep 3: Classifying jobs and validating entry-level fit...")
            classified_jobs = []
            
            for i, job in enumerate(us_jobs[:20], 1):  # Limit to avoid rate limits
                print(f"  Processing job {i}/{min(len(us_jobs), 20)}: {job.get('title')}")
                
                # Fetch full description if needed
                if not job.get('description'):
                    job['description'] = self.discovery.fetch_job_description(job)
                
                # Classify and validate
                category, is_entry_level, reasoning = self.classifier.classify_job(job)
                
                job['category'] = category
                job['is_entry_level'] = is_entry_level
                job['entry_level_reasoning'] = reasoning
                
                # Discard if not relevant
                if not self.classifier.should_discard(category, is_entry_level):
                    classified_jobs.append(job)
                    print(f"    ✓ {category} | Entry-level: {is_entry_level}")
                else:
                    print(f"    ✗ Discarded: {category} | Entry-level: {is_entry_level}")
            
            print(f"  → {len(classified_jobs)} jobs classified as relevant")
            
            if not classified_jobs:
                print("  → No relevant jobs found, ending cycle")
                return
            
            # Step 4: Analyze H-1B sponsorship
            print("\nStep 4: Analyzing H-1B sponsorship likelihood...")
            sponsored_jobs = []
            
            for job in classified_jobs:
                confidence, reasoning = self.sponsor_analyzer.analyze_sponsorship(job)
                
                job['sponsor_confidence'] = confidence
                job['sponsor_reasoning'] = reasoning
                
                # Discard excluded or low-confidence jobs
                if confidence != 'EXCLUDED' and not self.sponsor_analyzer.should_discard(confidence):
                    sponsored_jobs.append(job)
                    print(f"  ✓ {job.get('company')}: {confidence}")
                else:
                    print(f"  ✗ {job.get('company')}: {confidence}")
            
            print(f"  → {len(sponsored_jobs)} jobs have acceptable sponsorship likelihood")
            
            if not sponsored_jobs:
                print("  → No jobs with sponsorship potential, ending cycle")
                return
            
            # Step 5: Score and rank jobs
            print("\nStep 5: Scoring and ranking jobs...")
            scored_jobs = self.scorer.rank_jobs(sponsored_jobs)
            
            for i, job in enumerate(scored_jobs[:5], 1):
                print(f"  {i}. {job.get('title')} at {job.get('company')} - Score: {job.get('score', 0):.2f}")
            
            # Step 6: Deduplicate and store
            print("\nStep 6: Deduplicating and storing in database...")
            new_jobs = self.deduplicator.filter_duplicates(scored_jobs)
            print(f"  → {len(new_jobs)} new jobs added to database")
            
            # Print statistics
            stats = self.deduplicator.db.get_stats()
            print(f"\nDatabase Statistics:")
            print(f"  Total jobs: {stats['total_jobs']}")
            print(f"  Unsent jobs: {stats['unsent_jobs']}")
            print(f"  Sent jobs: {stats['sent_jobs']}")
            
        except Exception as e:
            print(f"\n❌ Error in discovery cycle: {e}")
            traceback.print_exc()
        
        print(f"\nDiscovery cycle completed at {datetime.now()}")
        print(f"{'='*60}\n")
    
    def send_daily_digest(self):
        """
        Send daily email digest with top jobs.
        """
        print(f"\n{'='*60}")
        print(f"Sending daily digest at {datetime.now()}")
        print(f"{'='*60}\n")
        
        try:
            # Get unsent jobs for digest
            jobs_for_digest = self.deduplicator.get_jobs_for_digest(max_count=12)
            
            print(f"Found {len(jobs_for_digest)} jobs for digest")
            
            # Send email
            if self.recipient_email:
                success = self.email_sender.send_email(self.recipient_email, jobs_for_digest)
                
                if success:
                    # Mark jobs as sent
                    self.deduplicator.mark_digest_sent(jobs_for_digest)
                    print(f"✓ Digest sent successfully to {self.recipient_email}")
                else:
                    print(f"✗ Failed to send digest")
            else:
                print("⚠ No recipient email configured, skipping email send")
                print("Generating digest preview...")
                
                # Save preview to file
                html = self.email_sender.generate_digest(jobs_for_digest)
                preview_path = str(Path(__file__).parent / f"digest_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                with open(preview_path, 'w') as f:
                    f.write(html)
                print(f"  → Preview saved to {preview_path}")
            
        except Exception as e:
            print(f"\n❌ Error sending digest: {e}")
            traceback.print_exc()
        
        print(f"\nDigest process completed at {datetime.now()}")
        print(f"{'='*60}\n")
    
    def start(self):
        """
        Start the autonomous agent with scheduled tasks.
        """
        print("\n" + "="*60)
        print("JOB MONITOR AGENT STARTING")
        print("="*60)
        print(f"Current time: {datetime.now()}")
        print(f"Recipient email: {self.recipient_email or 'Not configured (preview mode)'}")
        print("\nSchedule:")
        print("  - Discovery runs: Once daily at 16:30 (4:30 PM)")
        print("  - Daily digest: 17:00 (5:00 PM) - sent after discovery")
        print("="*60 + "\n")

        # Schedule discovery once per day at 4:30 PM (before digest)
        schedule.every().day.at("16:30").do(self.run_discovery_cycle)

        # Schedule daily digest at 5:00 PM (after discovery completes)
        schedule.every().day.at("17:00").do(self.send_daily_digest)
        
        # Run initial discovery immediately
        print("Running initial discovery cycle...")
        self.run_discovery_cycle()
        
        # Main loop
        print("\nAgent is now running. Press Ctrl+C to stop.\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\nAgent stopped by user")
            print("="*60)


def load_config() -> Dict:
    """
    Load configuration from environment variables or config file.

    Returns:
        Configuration dictionary
    """
    # Default db_path to same directory as script
    default_db_path = str(Path(__file__).parent / 'jobs.db')

    config = {
        'db_path': os.getenv('JOB_MONITOR_DB_PATH', default_db_path),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'sender_email': os.getenv('SENDER_EMAIL', ''),
        'sender_password': os.getenv('SENDER_PASSWORD', ''),
        'recipient_email': os.getenv('RECIPIENT_EMAIL', '')
    }
    
    return config


if __name__ == '__main__':
    # Load configuration
    config = load_config()
    
    # Create and start agent
    agent = JobMonitorAgent(config)
    agent.start()
