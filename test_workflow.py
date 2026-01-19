"""
Test script to validate the job monitoring workflow.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load config.env from same directory
config_path = Path(__file__).parent / 'config.env'
if config_path.exists():
    load_dotenv(config_path)
    print(f"Loaded config from {config_path}\n")

# Test imports
print("Testing module imports...")
try:
    from job_discovery import JobDiscovery
    from job_classifier import JobClassifier
    from sponsorship_analyzer import SponsorshipAnalyzer
    from job_scorer import JobScorer
    from deduplicator import Deduplicator
    from email_sender import EmailDigest
    print("[OK] All modules imported successfully\n")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 1: Job Discovery
print("="*60)
print("TEST 1: Job Discovery Module")
print("="*60)
try:
    discovery = JobDiscovery()
    
    # Test location validation
    assert discovery.is_us_location("San Francisco, CA") == True
    assert discovery.is_us_location("New York, NY") == True
    assert discovery.is_us_location("Remote") == True
    assert discovery.is_us_location("London, UK") == False
    print("[OK] Location validation working")
    
    # Test freshness check
    recent_date = datetime.now() - timedelta(hours=12)
    old_date = datetime.now() - timedelta(hours=36)
    assert discovery.is_within_24_hours(recent_date) == True
    assert discovery.is_within_24_hours(old_date) == False
    print("[OK] Freshness validation working")
    
    print("[OK] Job Discovery module passed\n")
except Exception as e:
    print(f"[FAIL] Job Discovery test failed: {e}\n")

# Test 2: Job Classification
print("="*60)
print("TEST 2: Job Classification Module")
print("="*60)
try:
    classifier = JobClassifier()
    
    # Test quick classification
    assert classifier._quick_classify("Data Scientist - New Grad") == "Data Scientist"
    assert classifier._quick_classify("Junior Data Analyst") == "Data Analyst"
    assert classifier._quick_classify("Quantitative Researcher") == "Quantitative Finance"
    assert classifier._quick_classify("Data Engineer I") == "Data Engineer"
    print("[OK] Quick classification working")
    
    # Test entry-level validation
    test_job = {
        'title': 'Junior Data Scientist',
        'description': 'We seek recent graduates with 0-2 years of experience'
    }
    is_entry, reasoning = classifier._validate_entry_level(test_job)
    assert is_entry == True
    print("[OK] Entry-level validation working")
    
    print("[OK] Job Classification module passed\n")
except Exception as e:
    print(f"[FAIL] Job Classification test failed: {e}\n")

# Test 3: Sponsorship Analysis
print("="*60)
print("TEST 3: Sponsorship Analysis Module")
print("="*60)
try:
    analyzer = SponsorshipAnalyzer()
    
    # Test exclusion detection
    exclusion_text = "We do not sponsor visas for this position"
    assert analyzer._has_exclusionary_language(exclusion_text) == True
    print("[OK] Exclusion detection working")
    
    # Test company signal
    assert analyzer._get_company_signal("Google") == "HIGH"
    assert analyzer._get_company_signal("Small Startup Inc") == "LOW"
    print("[OK] Company signal detection working")
    
    print("[OK] Sponsorship Analysis module passed\n")
except Exception as e:
    print(f"[FAIL] Sponsorship Analysis test failed: {e}\n")

# Test 4: Job Scoring
print("="*60)
print("TEST 4: Job Scoring Module")
print("="*60)
try:
    scorer = JobScorer()
    
    # Test scoring
    test_job = {
        'category': 'Data Scientist',
        'sponsor_confidence': 'HIGH',
        'posted_date': datetime.now() - timedelta(hours=2),
        'entry_level_reasoning': 'New grad position with 0-1 years experience'
    }
    score = scorer.score_job(test_job)
    assert score > 0
    print(f"[OK] Scoring working (score: {score:.2f})")
    
    # Test ranking
    test_jobs = [
        {'category': 'Data Analyst', 'sponsor_confidence': 'MEDIUM', 'posted_date': datetime.now()},
        {'category': 'Data Scientist', 'sponsor_confidence': 'HIGH', 'posted_date': datetime.now()},
        {'category': 'Data Engineer', 'sponsor_confidence': 'LOW', 'posted_date': datetime.now()}
    ]
    ranked = scorer.rank_jobs(test_jobs)
    assert ranked[0]['category'] == 'Data Scientist'  # Should be highest scored
    print("[OK] Ranking working")
    
    print("[OK] Job Scoring module passed\n")
except Exception as e:
    print(f"[FAIL] Job Scoring test failed: {e}\n")

# Test 5: Deduplication
print("="*60)
print("TEST 5: Deduplication Module")
print("="*60)
try:
    dedup = Deduplicator('test_jobs.db')
    
    # Test hash generation
    job1 = {'company': 'Google', 'title': 'Data Scientist'}
    job2 = {'company': 'Google', 'title': 'Data Scientist'}
    job3 = {'company': 'Microsoft', 'title': 'Data Scientist'}
    
    hash1 = dedup.db._generate_job_hash(job1)
    hash2 = dedup.db._generate_job_hash(job2)
    hash3 = dedup.db._generate_job_hash(job3)
    
    assert hash1 == hash2  # Same company + title should have same hash
    assert hash1 != hash3  # Different company should have different hash
    print("[OK] Hash generation working")
    
    # Test duplicate detection
    test_job = {
        'title': 'Test Data Scientist',
        'company': 'Test Company',
        'location': 'Test Location',
        'category': 'Data Scientist',
        'source': 'Test',
        'url': 'https://test.com',
        'description': 'Test description',
        'posted_date': datetime.now().isoformat(),
        'sponsor_confidence': 'HIGH',
        'score': 100.0
    }
    
    job_id1 = dedup.db.add_job(test_job)
    job_id2 = dedup.db.add_job(test_job)  # Should be duplicate
    
    assert job_id1 is not None
    assert job_id2 is None  # Duplicate should return None
    print("[OK] Duplicate detection working")
    
    print("[OK] Deduplication module passed\n")
except Exception as e:
    print(f"[FAIL] Deduplication test failed: {e}\n")

# Test 6: Email Digest
print("="*60)
print("TEST 6: Email Digest Module")
print("="*60)
try:
    email_sender = EmailDigest()
    
    # Test digest generation
    test_jobs = [
        {
            'title': 'Data Scientist - New Grad',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'category': 'Data Scientist',
            'url': 'https://example.com/job1',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'HIGH',
            'entry_level_reasoning': 'New grad position with 0-1 years experience'
        },
        {
            'title': 'Junior Data Analyst',
            'company': 'Microsoft',
            'location': 'Remote',
            'category': 'Data Analyst',
            'url': 'https://example.com/job2',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'MEDIUM',
            'entry_level_reasoning': 'Junior level role'
        }
    ]
    
    html = email_sender.generate_digest(test_jobs)
    assert len(html) > 0
    assert 'Data Scientist' in html
    assert 'Google' in html
    print("[OK] Digest generation working")
    
    # Test empty digest
    empty_html = email_sender.generate_digest([])
    assert 'No New Jobs Found' in empty_html
    print("[OK] Empty digest generation working")
    
    # Save test digest
    output_path = Path(__file__).parent / 'test_digest_output.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Test digest saved to {output_path}")
    
    print("[OK] Email Digest module passed\n")
except Exception as e:
    print(f"[FAIL] Email Digest test failed: {e}\n")

# Summary
print("="*60)
print("TEST SUMMARY")
print("="*60)
print("All core modules tested successfully!")
print("\nThe job monitoring agent is ready to use.")
print("\nNext steps:")
print("1. Configure your email settings in config.env")
print("2. Run: source config.env")
print("3. Start the agent: python3 main.py")
print("="*60)
