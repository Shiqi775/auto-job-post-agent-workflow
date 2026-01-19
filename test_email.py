"""
Quick test to verify email sending works.
"""
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load config
config_path = Path(__file__).parent / 'config.env'
load_dotenv(config_path)
print(f"Loaded config from {config_path}\n")

from email_sender import EmailDigest
import os

# Create test jobs
test_jobs = [
    {
        'title': 'Data Scientist - New Grad (TEST)',
        'company': 'Google',
        'location': 'Mountain View, CA',
        'category': 'Data Scientist',
        'url': 'https://example.com/job1',
        'posted_date': datetime.now().isoformat(),
        'sponsor_confidence': 'HIGH',
        'entry_level_reasoning': 'New grad position with 0-1 years experience'
    },
    {
        'title': 'Junior Data Analyst (TEST)',
        'company': 'Microsoft',
        'location': 'Remote',
        'category': 'Data Analyst',
        'url': 'https://example.com/job2',
        'posted_date': datetime.now().isoformat(),
        'sponsor_confidence': 'MEDIUM',
        'entry_level_reasoning': 'Junior level role'
    }
]

# Get config from environment
smtp_server = os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
sender_email = os.getenv('SENDER_EMAIL', '')
sender_password = os.getenv('SENDER_PASSWORD', '')
recipient_email = os.getenv('RECIPIENT_EMAIL', '')

print(f"Sender: {sender_email}")
print(f"Recipient: {recipient_email}")
print(f"SMTP: {smtp_server}:{smtp_port}")
print()

# Create email sender
email_sender = EmailDigest(
    smtp_server=smtp_server,
    smtp_port=smtp_port,
    sender_email=sender_email,
    sender_password=sender_password
)

# Send test email
print("Sending test email...")
success = email_sender.send_email(recipient_email, test_jobs)

if success:
    print("\n[OK] Test email sent successfully!")
    print(f"Check your inbox at: {recipient_email}")
else:
    print("\n[FAIL] Failed to send email.")
    print("If you have 2FA on Outlook, you need an App Password.")
    print("Generate one at: https://account.microsoft.com/security")
