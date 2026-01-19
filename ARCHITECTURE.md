# Job Monitoring Agent - System Architecture

## Overview

This autonomous agent continuously monitors job postings for early-career data and quantitative finance positions suitable for international students requiring H-1B sponsorship.

## System Components

### 1. Job Discovery Module (`job_discovery.py`)
- Searches multiple job boards (Indeed, Glassdoor, LinkedIn, company career pages)
- Filters for jobs posted within last 24 hours
- Extracts job metadata: title, company, location, description, posting date, URL

### 2. Job Classification Module (`job_classifier.py`)
- Uses LLM to classify jobs into categories:
  - Data Scientist
  - Data Analyst
  - Quantitative Finance
  - Data Engineer
  - Other (discard)
- Validates entry-level criteria (0-2 years experience)

### 3. H-1B Sponsorship Inference Module (`sponsorship_analyzer.py`)
- **Hard exclusion**: Filters out explicit "no sponsorship" statements
- **Company-level analysis**: Checks H-1B LCA disclosure data
- **Textual analysis**: Uses LLM to assess sponsorship likelihood
- Assigns confidence: HIGH, MEDIUM, LOW

### 4. Scoring & Ranking Module (`job_scorer.py`)
- Scores based on:
  - Role priority (DS > DA > Quant > DE)
  - Sponsor confidence (High > Medium)
  - Freshness (newer = higher score)
  - Entry-level fit clarity
- Ranks jobs by total score

### 5. Deduplication Module (`deduplicator.py`)
- Maintains persistent job database
- Prevents duplicate notifications
- Tracks previously sent jobs

### 6. Email Digest Module (`email_sender.py`)
- Generates Markdown-formatted email
- Groups jobs by category
- Sends via Outlook at 5:00 PM daily
- Limits to top 12 jobs

### 7. Scheduler & Orchestrator (`main.py`)
- Runs discovery every 6 hours
- Triggers daily email at 5:00 PM
- Maintains state between runs
- Handles errors and retries

## Data Flow

```
Job Sources → Discovery → Classification → Sponsorship Analysis → Scoring → Deduplication → Email Digest
                                                                                              ↓
                                                                                         User Inbox
```

## Persistence

- **SQLite database** (`jobs.db`): Stores all discovered jobs with metadata
- **Sent jobs log**: Prevents duplicate notifications
- **Company H-1B cache**: Caches sponsorship likelihood data

## Scheduling

- **Discovery runs**: Every 6 hours (00:00, 06:00, 12:00, 18:00)
- **Email delivery**: Once daily at 17:00 (5:00 PM)

## Technology Stack

- **Python 3.11**
- **OpenAI API**: For LLM-based classification and analysis
- **BeautifulSoup**: Web scraping
- **SQLite**: Persistence
- **SMTP/Outlook**: Email delivery
- **Schedule library**: Task scheduling
