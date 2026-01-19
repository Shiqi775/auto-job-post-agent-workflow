# Quick Start Guide

Get your autonomous job monitoring agent running in 5 minutes.

## Step 1: Configure Email Settings

Copy the configuration template and add your email credentials:

```bash
cd /home/ubuntu/job_monitor
cp config.env.template config.env
nano config.env
```

Edit these fields in `config.env`:

```bash
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAIL=where-to-receive-digests@example.com
```

**Important**: For Outlook with two-factor authentication, generate an App Password at https://account.microsoft.com/security

## Step 2: Load Configuration

```bash
source config.env
```

## Step 3: Start the Agent

```bash
python3 main.py
```

The agent will:
- Run an immediate discovery cycle
- Schedule discovery every 6 hours (00:00, 06:00, 12:00, 18:00)
- Send daily digest at 5:00 PM

## Preview Mode (No Email)

To test without sending emails, leave `RECIPIENT_EMAIL` empty. The agent will generate HTML preview files instead.

## Running in Background

Use screen to keep the agent running:

```bash
screen -S job_monitor
cd /home/ubuntu/job_monitor
source config.env
python3 main.py
# Press Ctrl+A then D to detach
```

Reattach later with:

```bash
screen -r job_monitor
```

## Verify It's Working

Check the console output for:
- ✓ Jobs discovered from sources
- ✓ Jobs classified and scored
- ✓ Database updates
- ✓ Email sent (or preview generated)

View the database:

```bash
sqlite3 jobs.db "SELECT COUNT(*) FROM jobs;"
```

## Troubleshooting

**No jobs discovered?** Job boards may have changed their structure. The system will still work once you add custom sources or use APIs.

**Email not sending?** Verify your Outlook credentials and ensure you're using an App Password if 2FA is enabled.

**Want to customize?** See the full README.md for detailed configuration options.

## What's Next?

The agent is now autonomous and will:
1. Discover new jobs every 6 hours
2. Classify and score them automatically
3. Send you a daily digest at 5:00 PM with the top 12 opportunities

You can leave it running 24/7 and receive curated job opportunities daily!
