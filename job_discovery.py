"""
Job Discovery Module

Discovers job postings using JSearch API (RapidAPI).
Focuses on entry-level data science, analytics, and quant finance roles.
"""

import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dateutil import parser as date_parser


class JobDiscovery:
    """Discovers and extracts job postings using JSearch API."""

    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY', '')
        self.api_host = 'jsearch.p.rapidapi.com'
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }
        # Search queries for target job types (6 queries to fit 200 requests/month)
        self.search_queries = [
            'entry level data scientist',
            'junior data analyst',
            'entry level quantitative analyst',
            'junior data engineer',
            'new grad data science',
            'entry level machine learning'
        ]
        # Job aggregators to filter out (these require paid subscriptions)
        self.blocked_employers = [
            'virtualvocations', 'ziprecruiter', 'aborfy', 'talent.com',
            'jobrapido', 'jooble', 'neuvoo', 'adzuna', 'glassdoor',
            'careerbuilder', 'snagajob', 'upward.net', 'lensa',
            'bebee', 'jobget', 'climatebase'
        ]

    def discover_jobs(self) -> List[Dict]:
        """
        Main discovery method that fetches jobs from JSearch API.

        Returns:
            List of job dictionaries with metadata
        """
        if not self.api_key or self.api_key == 'YOUR_RAPIDAPI_KEY_HERE':
            print("  [ERROR] RapidAPI key not configured. Please add your key to config.env")
            return []

        all_jobs = []
        seen_ids = set()  # Avoid duplicates across queries
        filtered_count = 0

        for query in self.search_queries:
            print(f"  Searching: {query}")
            jobs = self._search_jobs(query)

            for job in jobs:
                job_id = job.get('job_id', '')
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    # Filter out job aggregators
                    if self._is_blocked_employer(job.get('company', '')):
                        filtered_count += 1
                        continue
                    all_jobs.append(job)

        print(f"  Total unique jobs found: {len(all_jobs)} (filtered out {filtered_count} aggregator listings)")
        return all_jobs

    def _is_blocked_employer(self, company: str) -> bool:
        """Check if employer is a job aggregator that should be filtered out."""
        if not company:
            return False
        company_lower = company.lower()
        return any(blocked in company_lower for blocked in self.blocked_employers)

    def _search_jobs(self, query: str, num_pages: int = 1) -> List[Dict]:
        """
        Search for jobs using JSearch API.

        Args:
            query: Search query string
            num_pages: Number of pages to fetch (default 1 to conserve API calls)

        Returns:
            List of job dictionaries
        """
        jobs = []
        url = "https://jsearch.p.rapidapi.com/search"

        params = {
            'query': f'{query} in United States',
            'page': '1',
            'num_pages': str(num_pages),
            'date_posted': 'week',  # Jobs from past week (more results)
            'remote_jobs_only': 'false',
            'employment_types': 'FULLTIME'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                raw_jobs = data.get('data', [])

                for raw_job in raw_jobs:
                    job = self._parse_job(raw_job)
                    if job:
                        jobs.append(job)

            elif response.status_code == 403:
                print(f"    [ERROR] API access denied. Check your RapidAPI key.")
            elif response.status_code == 429:
                print(f"    [WARNING] Rate limit reached. Try again later.")
            else:
                print(f"    [ERROR] API returned status {response.status_code}")

        except Exception as e:
            print(f"    [ERROR] Failed to fetch jobs: {e}")

        return jobs

    def _parse_job(self, raw_job: Dict) -> Optional[Dict]:
        """
        Parse raw job data from JSearch API into standard format.

        Args:
            raw_job: Raw job data from API

        Returns:
            Parsed job dictionary or None
        """
        try:
            # Parse posted date
            posted_str = raw_job.get('job_posted_at_datetime_utc', '')
            if posted_str:
                try:
                    posted_date = date_parser.parse(posted_str)
                except:
                    posted_date = datetime.now()
            else:
                posted_date = datetime.now()

            # Build location string
            city = raw_job.get('job_city', '')
            state = raw_job.get('job_state', '')
            country = raw_job.get('job_country', 'US')
            is_remote = raw_job.get('job_is_remote', False)

            if is_remote:
                location = 'Remote'
            elif city and state:
                location = f"{city}, {state}"
            elif state:
                location = state
            else:
                location = country

            return {
                'job_id': raw_job.get('job_id', ''),
                'title': raw_job.get('job_title', 'Unknown'),
                'company': raw_job.get('employer_name', 'Unknown'),
                'location': location,
                'source': 'JSearch',
                'url': raw_job.get('job_apply_link', '') or raw_job.get('job_google_link', ''),
                'posted_date': posted_date,
                'description': raw_job.get('job_description', ''),
                'job_type': raw_job.get('job_employment_type', ''),
                'is_remote': is_remote,
                'min_salary': raw_job.get('job_min_salary'),
                'max_salary': raw_job.get('job_max_salary'),
                'salary_currency': raw_job.get('job_salary_currency', 'USD'),
                'employer_logo': raw_job.get('employer_logo', ''),
                'job_highlights': raw_job.get('job_highlights', {})
            }

        except Exception as e:
            print(f"    [ERROR] Failed to parse job: {e}")
            return None

    def fetch_job_description(self, job: Dict) -> str:
        """
        Get job description (already included in JSearch results).

        Args:
            job: Job dictionary

        Returns:
            Job description text
        """
        return job.get('description', '')

    def is_within_24_hours(self, posted_date) -> bool:
        """Check if job was posted within last 3 days (72 hours)."""
        if not posted_date:
            return True  # Assume recent if no date

        if isinstance(posted_date, str):
            try:
                posted_date = date_parser.parse(posted_date)
            except:
                return True

        cutoff = datetime.now(posted_date.tzinfo) if posted_date.tzinfo else datetime.now()
        cutoff = cutoff - timedelta(hours=72)  # Extended to 3 days for more results

        # Handle timezone-aware vs naive datetime comparison
        if posted_date.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=None)

        return posted_date >= cutoff

    def is_us_location(self, location: str) -> bool:
        """Check if location is in the United States."""
        if not location:
            return True  # Assume US if no location (API filtered to US)

        location_lower = location.lower()

        # Check for non-US indicators
        non_us_indicators = ['canada', 'uk', 'united kingdom', 'india', 'germany',
                            'france', 'australia', 'singapore', 'china', 'japan']

        if any(indicator in location_lower for indicator in non_us_indicators):
            return False

        # Check for US indicators
        us_indicators = ['united states', 'usa', 'u.s.', 'remote']

        # US state abbreviations
        us_states = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga',
                     'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md',
                     'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
                     'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc',
                     'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy', 'dc']

        if any(indicator in location_lower for indicator in us_indicators):
            return True

        # Check for state codes (as separate words)
        words = location_lower.replace(',', ' ').split()
        if any(word in us_states for word in words):
            return True

        return True  # Default to True since API is filtered to US


if __name__ == '__main__':
    # Test the discovery module
    from pathlib import Path
    from dotenv import load_dotenv

    config_path = Path(__file__).parent / 'config.env'
    load_dotenv(config_path)

    discovery = JobDiscovery()
    jobs = discovery.discover_jobs()

    print(f"\nDiscovered {len(jobs)} jobs")
    for job in jobs[:5]:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url'][:60]}..." if len(job.get('url', '')) > 60 else f"URL: {job.get('url', 'N/A')}")
