"""
Run Once - Discover jobs and send email immediately, then exit.
Just run this script whenever you want to see the latest jobs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load config
config_path = Path(__file__).parent / 'config.env'
load_dotenv(config_path)
print(f"Loaded config from {config_path}\n")

from job_discovery import JobDiscovery
from job_classifier import JobClassifier
from sponsorship_analyzer import SponsorshipAnalyzer
from job_scorer import JobScorer
from deduplicator import Deduplicator
from email_sender import EmailDigest


def run_once():
    """Discover jobs and send email once, then exit."""

    print("="*60)
    print("JOB MONITOR - ONE TIME RUN")
    print(f"Time: {datetime.now()}")
    print("="*60 + "\n")

    # Initialize modules
    db_path = os.getenv('JOB_MONITOR_DB_PATH', str(Path(__file__).parent / 'jobs.db'))

    discovery = JobDiscovery()
    classifier = JobClassifier()
    sponsor_analyzer = SponsorshipAnalyzer()
    scorer = JobScorer()
    deduplicator = Deduplicator(db_path)

    email_sender = EmailDigest(
        smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        sender_email=os.getenv('SENDER_EMAIL', ''),
        sender_password=os.getenv('SENDER_PASSWORD', '')
    )
    recipient_email = os.getenv('RECIPIENT_EMAIL', '')

    # Step 1: Discover jobs
    print("Step 1: Discovering jobs from sources...")
    raw_jobs = discovery.discover_jobs()
    print(f"  Found {len(raw_jobs)} raw job postings")

    if not raw_jobs:
        print("  No jobs discovered from sources")
        # Still send email with any unsent jobs from database
        jobs_for_digest = deduplicator.get_jobs_for_digest(max_count=12)
        if jobs_for_digest:
            print(f"\nFound {len(jobs_for_digest)} unsent jobs in database")
        else:
            print("\nNo jobs to send")
            return
    else:
        # Step 2: Filter for US locations and 24-hour freshness
        print("\nStep 2: Filtering for US locations and freshness...")
        us_jobs = [
            job for job in raw_jobs
            if discovery.is_us_location(job.get('location', ''))
            and discovery.is_within_24_hours(job.get('posted_date'))
        ]
        print(f"  {len(us_jobs)} jobs meet location and freshness criteria")

        if us_jobs:
            # Step 3: Classify jobs
            print("\nStep 3: Classifying jobs...")
            classified_jobs = []

            for i, job in enumerate(us_jobs[:20], 1):
                print(f"  Processing {i}/{min(len(us_jobs), 20)}: {job.get('title', 'Unknown')[:50]}")

                if not job.get('description'):
                    job['description'] = discovery.fetch_job_description(job)

                category, is_entry_level, reasoning = classifier.classify_job(job)
                job['category'] = category
                job['is_entry_level'] = is_entry_level
                job['entry_level_reasoning'] = reasoning

                if not classifier.should_discard(category, is_entry_level):
                    classified_jobs.append(job)
                    print(f"    [OK] {category}")
                else:
                    print(f"    [SKIP] {category}, Entry-level: {is_entry_level}")

            print(f"  {len(classified_jobs)} relevant jobs found")

            if classified_jobs:
                # Step 4: Analyze sponsorship
                print("\nStep 4: Analyzing H-1B sponsorship...")
                sponsored_jobs = []

                for job in classified_jobs:
                    confidence, reasoning = sponsor_analyzer.analyze_sponsorship(job)
                    job['sponsor_confidence'] = confidence
                    job['sponsor_reasoning'] = reasoning

                    if confidence != 'EXCLUDED' and not sponsor_analyzer.should_discard(confidence):
                        sponsored_jobs.append(job)
                        print(f"  [OK] {job.get('company')}: {confidence}")
                    else:
                        print(f"  [SKIP] {job.get('company')}: {confidence}")

                print(f"  {len(sponsored_jobs)} jobs with sponsorship potential")

                if sponsored_jobs:
                    # Step 5: Score and store
                    print("\nStep 5: Scoring and storing...")
                    scored_jobs = scorer.rank_jobs(sponsored_jobs)
                    new_jobs = deduplicator.filter_duplicates(scored_jobs)
                    print(f"  {len(new_jobs)} new jobs added to database")

        # Get jobs for digest (including any from previous runs)
        jobs_for_digest = deduplicator.get_jobs_for_digest(max_count=12)

    # Step 6: Send email
    print("\n" + "="*60)
    print(f"SENDING DIGEST: {len(jobs_for_digest)} jobs")
    print("="*60)

    if not jobs_for_digest:
        print("No new jobs to send.")
        return

    for i, job in enumerate(jobs_for_digest[:5], 1):
        print(f"  {i}. {job.get('title', 'Unknown')[:40]} at {job.get('company', 'Unknown')}")
    if len(jobs_for_digest) > 5:
        print(f"  ... and {len(jobs_for_digest) - 5} more")

    print(f"\nSending to: {recipient_email}")
    success = email_sender.send_email(recipient_email, jobs_for_digest)

    if success:
        deduplicator.mark_digest_sent(jobs_for_digest)
        print("\n[OK] Email sent successfully!")
    else:
        print("\n[FAIL] Failed to send email")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == '__main__':
    run_once()
