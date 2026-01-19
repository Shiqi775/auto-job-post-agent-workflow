# Autonomous Job Monitoring Agent - Project Overview

## What This System Does

This is a fully autonomous agent that runs 24/7 to help international students find H-1B eligible entry-level positions in data science, data analysis, quantitative finance, and data engineering. It continuously monitors job boards, intelligently filters opportunities, and delivers a curated daily email digest.

## Core Capabilities

### Autonomous Operation

The agent operates independently without manual intervention. It runs discovery cycles every 6 hours and sends daily email digests at 5:00 PM. All filtering, classification, scoring, and notification decisions are made automatically using advanced language models and rule-based systems.

### Intelligent Job Discovery

The system monitors multiple sources including Indeed, Glassdoor, LinkedIn, and company career pages. It specifically targets jobs posted within the last 24 hours and validates that positions are located in the United States or available remotely to US-based candidates.

### Smart Classification & Filtering

Using GPT-4.1-mini, the agent classifies jobs into four priority categories: Data Scientist (highest), Data Analyst, Quantitative Finance, and Data Engineer (lowest). It validates entry-level fit by checking for indicators like "new grad", "junior", or 0-2 years experience requirements, while automatically excluding senior, staff, and managerial positions.

### H-1B Sponsorship Inference

The system employs a sophisticated three-step approach to assess sponsorship likelihood. First, it performs hard exclusion by filtering jobs that explicitly state no visa sponsorship. Second, it evaluates company-level signals based on known sponsor-friendly employers like major tech companies and financial institutions. Third, it uses LLM-based textual analysis to detect positive signals or absence of restrictive language. Jobs are assigned HIGH, MEDIUM, or LOW confidence ratings.

### Advanced Scoring & Ranking

Each job receives a comprehensive score based on multiple factors: role priority (Data Scientist = 100 points, Data Analyst = 80, Quantitative Finance = 60, Data Engineer = 40), sponsor confidence (HIGH = 50 points, MEDIUM = 25), freshness (up to 20 points for jobs posted within hours), and entry-level fit clarity (up to 10 points). Jobs are ranked by total score to surface the most relevant opportunities.

### Deduplication & Persistence

The system maintains a SQLite database to track all discovered jobs and prevent duplicate notifications. Jobs are deduplicated across sources using SHA256 hashes of company + title combinations. The database tracks which jobs have been sent in previous digests to ensure you never receive the same opportunity twice.

### Beautiful Email Digests

Daily emails are formatted as responsive HTML with professional styling. Jobs are grouped by category in priority order, with each listing showing the title, company, location type (Remote/Hybrid/Onsite), sponsor confidence badge, posting time, entry-level fit reasoning, and a direct application link. If no qualifying jobs are found, a brief notification is sent instead.

## Project Structure

```
job_monitor/
├── main.py                      # Orchestrator with scheduling
├── job_discovery.py             # Multi-source job discovery
├── job_classifier.py            # LLM-based classification
├── sponsorship_analyzer.py      # H-1B sponsorship inference
├── job_scorer.py                # Scoring and ranking system
├── deduplicator.py              # Database and deduplication
├── email_sender.py              # Email digest generation
├── test_workflow.py             # Comprehensive test suite
├── requirements.txt             # Python dependencies
├── config.env.template          # Configuration template
├── ARCHITECTURE.md              # System architecture details
├── README.md                    # Complete documentation
├── QUICKSTART.md                # 5-minute setup guide
└── PROJECT_OVERVIEW.md          # This file
```

## Key Files Explained

**main.py** is the orchestrator that coordinates all modules and handles scheduling. It runs discovery cycles every 6 hours, manages the complete workflow from discovery to email delivery, and includes comprehensive error handling and logging.

**job_discovery.py** discovers jobs from multiple sources including Indeed, Glassdoor, and LinkedIn. It validates US locations and 24-hour freshness, extracts job metadata (title, company, location, description, URL), and implements rate limiting to respect source terms of service.

**job_classifier.py** uses GPT-4.1-mini for intelligent classification into Data Scientist, Data Analyst, Quantitative Finance, Data Engineer, or Other categories. It validates entry-level criteria (0-2 years experience) and provides reasoning for classification decisions.

**sponsorship_analyzer.py** implements three-step H-1B sponsorship inference: hard exclusion filtering, company-level signal analysis using known sponsor-friendly employers, and LLM-based textual analysis. It assigns confidence levels (HIGH/MEDIUM/LOW) with detailed reasoning.

**job_scorer.py** calculates comprehensive scores based on role priority, sponsor confidence, freshness, and entry-level fit clarity. It ranks jobs in descending order and filters top N jobs for digest inclusion.

**deduplicator.py** manages SQLite database persistence, generates SHA256 hashes for duplicate detection, tracks sent jobs to prevent repeat notifications, and provides database statistics and cleanup utilities.

**email_sender.py** generates responsive HTML email digests with professional styling, groups jobs by category in priority order, formats job cards with all relevant details, and sends via Outlook SMTP or generates preview files.

**test_workflow.py** provides comprehensive testing of all modules, validates core functionality with assertions, generates test output for inspection, and confirms the system is ready for deployment.

## Workflow Summary

### Discovery Cycle (Every 6 Hours)

1. **Source Scanning**: Query job boards with targeted keywords
2. **Location Filtering**: Validate US locations and remote positions
3. **Freshness Check**: Ensure jobs posted within last 24 hours
4. **Description Fetching**: Retrieve full job descriptions
5. **Classification**: Categorize jobs using LLM
6. **Entry-Level Validation**: Verify 0-2 years experience requirement
7. **Sponsorship Analysis**: Assess H-1B sponsorship likelihood
8. **Scoring**: Calculate comprehensive quality scores
9. **Deduplication**: Filter out previously seen jobs
10. **Storage**: Save to database for digest generation

### Daily Digest (5:00 PM)

1. **Retrieve Unsent Jobs**: Query database for jobs not yet sent
2. **Select Top 12**: Filter highest-scored opportunities
3. **Group by Category**: Organize in priority order
4. **Generate HTML**: Create beautifully formatted email
5. **Send Email**: Deliver via Outlook SMTP
6. **Mark as Sent**: Update database to prevent duplicates

## Configuration Requirements

To run the agent, you need:

- **Python 3.11+** (already available)
- **OpenAI API Key** (already configured in environment)
- **Outlook Email Account** with SMTP access
- **App Password** if using two-factor authentication

Configuration is managed through environment variables in `config.env`:

```bash
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAIL=where-to-receive-digests@example.com
```

## Getting Started

The fastest way to start is:

```bash
cd /home/ubuntu/job_monitor
cp config.env.template config.env
nano config.env  # Add your email credentials
source config.env
python3 main.py
```

See **QUICKSTART.md** for detailed setup instructions.

## Testing & Validation

The project includes a comprehensive test suite that validates all core functionality:

```bash
python3 test_workflow.py
```

This tests job discovery, classification, sponsorship analysis, scoring, deduplication, and email generation. All tests pass successfully, confirming the system is production-ready.

## Customization Options

The system is highly customizable:

- **Job Priorities**: Adjust role weights in `job_scorer.py`
- **Discovery Schedule**: Modify schedule in `main.py` (default: every 6 hours)
- **Digest Time**: Change daily email time in `main.py` (default: 5:00 PM)
- **Maximum Jobs**: Adjust digest limit in `main.py` (default: 12 jobs)
- **Job Sources**: Add new sources in `job_discovery.py`
- **Classification Logic**: Customize prompts in `job_classifier.py`
- **Sponsorship Rules**: Update company lists in `sponsorship_analyzer.py`

## Production Deployment

For continuous operation, run the agent as a background service using screen or systemd:

**Using screen (simple):**
```bash
screen -S job_monitor
cd /home/ubuntu/job_monitor
source config.env
python3 main.py
# Ctrl+A then D to detach
```

**Using systemd (recommended):**
Create `/etc/systemd/system/job-monitor.service` and enable the service. See README.md for complete instructions.

## Monitoring & Maintenance

The agent provides detailed console logging for all operations. You can monitor database statistics:

```bash
sqlite3 jobs.db "SELECT COUNT(*) FROM jobs WHERE sent_in_digest = 0;"
```

The system automatically cleans up old jobs (30+ days) to maintain database performance.

## Future Enhancements

Potential improvements include:

- Integration with official job board APIs for better reliability
- H-1B LCA disclosure data integration for more accurate sponsorship predictions
- Custom machine learning models trained on historical job data
- User preference configuration for location, salary, company size filters
- Alternative notification channels (Slack, Discord, SMS)
- Application tracking and interview progress management
- Resume matching using semantic similarity scoring

## Support & Documentation

- **Quick Setup**: See QUICKSTART.md
- **Complete Guide**: See README.md
- **Architecture**: See ARCHITECTURE.md
- **Testing**: Run test_workflow.py

## License & Compliance

This project is provided for personal use. Ensure compliance with job board terms of service and applicable regulations when deploying. Consider using official APIs where available to avoid scraping restrictions.

---

**Status**: ✅ Production Ready

All modules tested and validated. The system is ready for autonomous operation.
