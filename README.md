# Job Monitor Agent

An autonomous job monitoring agent that discovers, classifies, and delivers curated entry-level data science and quant finance job opportunities via daily email digests.

## Features

- **Automated Job Discovery**: Fetches jobs from JSearch API (RapidAPI) for data science, analytics, and quant finance roles
- **Smart Filtering**: Filters for US locations and jobs posted within 24 hours
- **AI Classification**: Uses OpenAI to classify jobs and validate entry-level fit
- **H-1B Sponsorship Analysis**: Analyzes likelihood of visa sponsorship based on company history
- **Job Scoring**: Ranks opportunities based on relevance and quality
- **Deduplication**: SQLite database prevents duplicate alerts
- **Email Digests**: Sends formatted HTML email with top 12 opportunities daily

## Requirements

- Python 3.8+
- OpenAI API key
- RapidAPI key (for JSearch API)
- SMTP email account (Outlook/Gmail)

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install python-dotenv python-dateutil
   ```

2. **Configure environment**:
   ```bash
   cp config.env.template config.env
   ```

3. **Edit `config.env`** with your credentials:
   ```
   RAPIDAPI_KEY=your-rapidapi-key
   OPENAI_API_KEY=your-openai-key
   SENDER_EMAIL=your-email@outlook.com
   SENDER_PASSWORD=your-app-password
   RECIPIENT_EMAIL=where-to-receive@example.com
   ```

   For Outlook with 2FA, generate an App Password at https://account.microsoft.com/security

## Usage

### Run Once (Manual)
Discover jobs and send email immediately:
```bash
python run_once.py
```

### Run Continuously (Scheduled)
Start the agent with automatic scheduling:
```bash
python main.py
```

Schedule:
- Discovery: Daily at 4:30 PM
- Email digest: Daily at 5:00 PM

### Preview Mode
Leave `RECIPIENT_EMAIL` empty to generate HTML preview files instead of sending emails.

### Windows Quick Run
Double-click `Get_Jobs.bat` to run a discovery cycle.

## Project Structure

```
├── main.py              # Main orchestrator with scheduling
├── run_once.py          # Single run script
├── job_discovery.py     # JSearch API integration
├── job_classifier.py    # AI job classification
├── sponsorship_analyzer.py  # H-1B sponsorship analysis
├── job_scorer.py        # Job ranking algorithm
├── deduplicator.py      # SQLite storage and deduplication
├── email_sender.py      # HTML email generation and sending
├── config.env.template  # Configuration template
└── jobs.db              # SQLite database (auto-created)
```

## License

MIT
