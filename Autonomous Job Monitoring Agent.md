# Autonomous Job Monitoring Agent

An intelligent agent that continuously discovers, filters, scores, and notifies you about newly posted U.S.-based early-career data and quantitative finance jobs suitable for international students requiring H-1B sponsorship.

## Overview

This autonomous agent operates 24/7 to help international students find relevant job opportunities by monitoring multiple job boards, analyzing H-1B sponsorship likelihood, and delivering a curated daily digest of the top opportunities.

### Key Features

**Intelligent Discovery**: Monitors multiple job sources including Indeed, Glassdoor, LinkedIn, and company career pages for jobs posted within the last 24 hours.

**Smart Classification**: Uses advanced language models to classify jobs into Data Scientist, Data Analyst, Quantitative Finance, and Data Engineer categories, while validating entry-level fit.

**H-1B Sponsorship Analysis**: Employs a three-step process to infer sponsorship likelihood by checking for hard exclusions, analyzing company history, and performing textual analysis of job descriptions.

**Sophisticated Scoring**: Ranks jobs based on role priority, sponsor confidence, freshness, and entry-level fit clarity to surface the most relevant opportunities.

**Deduplication**: Maintains a persistent database to prevent duplicate notifications across sources and time periods.

**Daily Email Digest**: Sends a beautifully formatted HTML email at 5:00 PM daily with up to 12 top-ranked jobs, grouped by category.

## Architecture

The system consists of seven core modules that work together in a coordinated workflow.

### Module Overview

| Module | Purpose | Key Functionality |
|--------|---------|-------------------|
| `job_discovery.py` | Job Discovery | Searches job boards, extracts metadata, validates US location and 24-hour freshness |
| `job_classifier.py` | Classification | Uses LLM to classify jobs and validate entry-level criteria (0-2 years experience) |
| `sponsorship_analyzer.py` | Sponsorship Analysis | Three-step inference: hard exclusion, company-level signal, textual analysis |
| `job_scorer.py` | Scoring & Ranking | Scores based on role priority, sponsor confidence, freshness, and clarity |
| `deduplicator.py` | Deduplication | SQLite database management, duplicate detection, sent job tracking |
| `email_sender.py` | Email Digest | Generates HTML emails, groups by category, sends via Outlook SMTP |
| `main.py` | Orchestration | Coordinates all modules, handles scheduling, error recovery |

### Data Flow

```
Job Sources → Discovery → Classification → Sponsorship Analysis → Scoring → Deduplication → Email Digest
                                                                                              ↓
                                                                                         User Inbox
```

## Installation

### Prerequisites

The system requires Python 3.11 or higher, an OpenAI API key (already configured in your environment), and an Outlook/Office 365 email account for sending digests.

### Setup Steps

First, install the required Python packages:

```bash
cd /home/ubuntu/job_monitor
sudo pip3 install -r requirements.txt
```

Next, configure your email settings by copying the template and filling in your credentials:

```bash
cp config.env.template config.env
nano config.env  # Edit with your email credentials
```

For Outlook users, you may need to generate an App Password at https://account.microsoft.com/security instead of using your regular password.

Finally, load the configuration and test the setup:

```bash
source config.env
python3 main.py
```

## Configuration

### Environment Variables

The agent uses the following environment variables for configuration:

**JOB_MONITOR_DB_PATH**: Path to SQLite database file (default: `/home/ubuntu/job_monitor/jobs.db`)

**SMTP_SERVER**: SMTP server address (default: `smtp-mail.outlook.com`)

**SMTP_PORT**: SMTP port number (default: `587`)

**SENDER_EMAIL**: Your Outlook email address for sending digests

**SENDER_PASSWORD**: Your Outlook password or App Password

**RECIPIENT_EMAIL**: Email address to receive daily digests

**OPENAI_API_KEY**: OpenAI API key (already configured in system environment)

### Email Configuration

For Outlook/Office 365 accounts, use the default SMTP settings. If you have two-factor authentication enabled, you must generate an App Password at https://account.microsoft.com/security and use that instead of your regular password.

For other email providers, update the SMTP server and port accordingly. Common alternatives include Gmail (smtp.gmail.com:587) and custom SMTP servers.

## Usage

### Running the Agent

To start the autonomous agent in the foreground:

```bash
cd /home/ubuntu/job_monitor
source config.env
python3 main.py
```

The agent will immediately run an initial discovery cycle, then operate on the following schedule:

- **Discovery runs**: Every 6 hours (00:00, 06:00, 12:00, 18:00)
- **Daily digest**: Once per day at 17:00 (5:00 PM)

### Running as a Background Service

For production deployment, run the agent as a background service using systemd or screen:

**Using screen:**

```bash
screen -S job_monitor
cd /home/ubuntu/job_monitor
source config.env
python3 main.py
# Press Ctrl+A then D to detach
```

To reattach later:

```bash
screen -r job_monitor
```

**Using systemd (recommended for production):**

Create a service file at `/etc/systemd/system/job-monitor.service`:

```ini
[Unit]
Description=Job Monitor Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/job_monitor
EnvironmentFile=/home/ubuntu/job_monitor/config.env
ExecStart=/usr/bin/python3 /home/ubuntu/job_monitor/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable job-monitor
sudo systemctl start job-monitor
sudo systemctl status job-monitor
```

### Preview Mode

If you want to test the system without sending emails, simply leave `RECIPIENT_EMAIL` empty in your configuration. The agent will generate HTML preview files in the job_monitor directory instead of sending emails.

## Workflow Details

### Discovery Cycle

Each discovery cycle follows this workflow:

1. **Source Scanning**: Queries multiple job boards with targeted keywords combining role types (data scientist, data analyst, quantitative analyst, data engineer) and experience levels (entry level, new grad, junior, associate).

2. **Location Filtering**: Validates that jobs are in the United States, including remote positions, by checking for US state codes and location indicators.

3. **Freshness Validation**: Ensures jobs were posted within the last 24 hours based on posting timestamps or conservative inference when exact times are unavailable.

4. **Description Fetching**: Retrieves full job descriptions from source URLs for detailed analysis.

5. **Classification**: Uses GPT-4.1-mini to classify jobs into one of four categories (Data Scientist, Data Analyst, Quantitative Finance, Data Engineer) or discard as "Other".

6. **Entry-Level Validation**: Checks if jobs meet at least one criterion: title includes entry-level indicators, experience requirement ≤ 2 years, early-career scope, or degree-focused hiring.

7. **Sponsorship Analysis**: Three-step process checking for hard exclusions, company-level sponsorship history, and textual signals indicating openness to international candidates.

8. **Scoring**: Calculates total score based on role priority (DS=100, DA=80, Quant=60, DE=40), sponsor confidence (High=50, Medium=25), freshness (0-20 points), and clarity (0-10 points).

9. **Deduplication**: Generates SHA256 hash from company + title to detect duplicates across sources and time periods.

10. **Storage**: Saves new jobs to SQLite database with full metadata for future reference and digest generation.

### Daily Digest

At 5:00 PM each day, the agent generates and sends an email digest containing:

- **Subject**: [Daily H1B-Eligible Data & Quant Jobs | Last 24h]
- **Content**: Up to 12 top-scored jobs grouped by category in priority order
- **Job Details**: Title, company, location type (Remote/Hybrid/Onsite), sponsor confidence, hours since posting, entry-level fit reasoning, and direct application link
- **Format**: Responsive HTML email with professional styling and clear visual hierarchy

If no qualifying jobs are found, a brief notification email is sent instead.

## Job Filtering Criteria

### Location Requirements

Jobs must be located in the United States, including remote positions available to US-based candidates. The system accepts hybrid and onsite roles across all 50 states.

### Freshness Requirements

Only jobs posted within the last 24 hours are included. When exact posting times are unavailable, the system infers freshness conservatively based on job board metadata.

### Experience Level

Jobs must meet at least one of the following criteria to qualify as entry-level:

- Title includes "New Grad", "Entry Level", "Junior", "I", or "Associate"
- Experience requirement is 0-2 years
- Job description emphasizes early-career responsibilities
- Explicitly targets BS/MS/PhD students or recent graduates

Jobs with senior, staff, principal, lead, manager, or director titles are automatically excluded.

### Job Categories

The system prioritizes jobs in the following order:

1. **Data Scientist**: Machine learning engineers, data scientists, ML researchers
2. **Data Analyst**: Business analysts, analytics specialists, data analysts
3. **Quantitative Finance**: Quantitative analysts, quant researchers, quant traders (junior/new grad), financial engineers, quant risk analysts (entry-level)
4. **Data Engineer**: Data engineers, ETL developers, data pipeline engineers

### H-1B Sponsorship

The system uses a probabilistic three-step approach to assess sponsorship likelihood:

**Step 1 - Hard Exclusion**: Immediately discards jobs explicitly stating "no visa sponsorship", "must be authorized to work without sponsorship", "US citizenship required", or similar restrictions.

**Step 2 - Company-Level Signal**: Evaluates company sponsorship history based on known sponsor-friendly employers (major tech companies, financial institutions, trading firms) and industry characteristics.

**Step 3 - Textual Analysis**: Uses LLM to detect positive signals like "open to international candidates", "visa sponsorship available", or absence of restrictive language.

Final confidence levels are assigned as HIGH, MEDIUM, or LOW. Jobs with LOW confidence are discarded unless they have exceptional quality scores (>150 points).

## Database Schema

The system uses SQLite to persist job data with the following schema:

```sql
CREATE TABLE jobs (
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
);
```

The `job_hash` field is a SHA256 hash of company + title, ensuring deduplication across sources. The `sent_in_digest` flag tracks which jobs have been included in previous digests to prevent duplicate notifications.

## Customization

### Adjusting Job Priorities

To change role priorities, edit the `role_weights` dictionary in `job_scorer.py`:

```python
self.role_weights = {
    'Data Scientist': 100,
    'Data Analyst': 80,
    'Quantitative Finance': 60,
    'Data Engineer': 40,
    'Other': 0
}
```

### Adding Job Sources

To add new job sources, extend the `JobDiscovery` class in `job_discovery.py`:

```python
def _discover_new_source(self) -> List[Dict]:
    """Discover jobs from new source."""
    jobs = []
    # Implement scraping logic
    return jobs
```

Then call it in the `discover_jobs()` method:

```python
all_jobs.extend(self._discover_new_source())
```

### Modifying Schedule

To change the discovery or digest schedule, edit the schedule configuration in `main.py`:

```python
# Run discovery every 4 hours instead of 6
schedule.every(4).hours.do(self.run_discovery_cycle)

# Send digest at 6:00 PM instead of 5:00 PM
schedule.every().day.at("18:00").do(self.send_daily_digest)
```

### Adjusting Maximum Jobs

To change the maximum number of jobs in the daily digest, modify the `max_count` parameter in `main.py`:

```python
jobs_for_digest = self.deduplicator.get_jobs_for_digest(max_count=20)
```

## Troubleshooting

### Email Not Sending

If emails are not being sent, check the following:

1. Verify your email credentials are correct in `config.env`
2. For Outlook with 2FA, ensure you're using an App Password
3. Check that port 587 is not blocked by your firewall
4. Review the console output for specific SMTP error messages
5. Test with a simple Python SMTP script to isolate the issue

### No Jobs Discovered

If no jobs are being discovered, consider:

1. Job boards may have changed their HTML structure (update selectors in `job_discovery.py`)
2. Rate limiting may be blocking requests (increase delays between requests)
3. User-Agent header may need updating to avoid bot detection
4. Try running discovery manually to see detailed error messages

### Classification Errors

If job classification is inaccurate:

1. Check that your OpenAI API key is properly configured
2. Verify you have sufficient API credits
3. Review the classification prompts in `job_classifier.py`
4. Consider adjusting the temperature parameter for more consistent results

### Database Issues

If you encounter database errors:

1. Ensure the database file has proper write permissions
2. Check disk space availability
3. Try deleting the database file to recreate from scratch
4. Run `sqlite3 jobs.db "PRAGMA integrity_check;"`

## Limitations and Considerations

### Rate Limiting

The system implements conservative rate limiting to avoid aggressive crawling. Discovery is limited to 20 jobs per cycle to prevent API rate limits and respect job board terms of service.

### Scraping Reliability

Job board HTML structures change frequently. The discovery module may require periodic updates to maintain compatibility with source websites. Consider using official APIs where available.

### LLM Costs

The system uses GPT-4.1-mini for classification and analysis, which incurs API costs. Each discovery cycle processes approximately 20-40 LLM requests. Monitor your OpenAI usage and adjust the model or frequency as needed.

### Sponsorship Accuracy

H-1B sponsorship inference is probabilistic and not guaranteed. The system provides best-effort estimates based on available signals. Always verify sponsorship availability directly with employers.

### Legal Compliance

Ensure your use of web scraping complies with job board terms of service and applicable laws. Consider using official APIs or partnerships where available.

## Future Enhancements

Potential improvements to consider:

- **API Integration**: Replace web scraping with official job board APIs for better reliability
- **Company Database**: Integrate with H-1B LCA disclosure data for more accurate sponsorship predictions
- **Machine Learning**: Train custom models on historical job data for improved classification
- **User Preferences**: Add configurable filters for location, salary, company size, etc.
- **Slack/Discord Integration**: Support alternative notification channels beyond email
- **Application Tracking**: Track application status and interview progress
- **Resume Matching**: Score jobs based on resume fit using semantic similarity

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

## License

This project is provided as-is for personal use. Ensure compliance with all applicable terms of service and regulations when deploying.
