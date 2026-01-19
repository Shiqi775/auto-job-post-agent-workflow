"""
Email Digest Module

Generates and sends daily job digest emails via Outlook/SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime
from collections import defaultdict


class EmailDigest:
    """Generates and sends job digest emails."""
    
    def __init__(self, smtp_server: str = 'smtp-mail.outlook.com', 
                 smtp_port: int = 587,
                 sender_email: str = '',
                 sender_password: str = ''):
        """
        Initialize email sender.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            sender_email: Sender email address
            sender_password: Sender email password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def generate_digest(self, jobs: List[Dict]) -> str:
        """
        Generate HTML email digest from jobs.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            HTML formatted email body
        """
        if not jobs:
            return self._generate_empty_digest()
        
        # Group jobs by category
        grouped_jobs = self._group_jobs_by_category(jobs)
        
        # Build HTML email
        html = self._build_html_header()
        
        # Add job sections in priority order
        category_order = ['Data Scientist', 'Data Analyst', 'Quantitative Finance', 'Data Engineer']
        
        for category in category_order:
            if category in grouped_jobs:
                html += self._build_category_section(category, grouped_jobs[category])
        
        html += self._build_html_footer()
        
        return html
    
    def _group_jobs_by_category(self, jobs: List[Dict]) -> Dict[str, List[Dict]]:
        """Group jobs by category."""
        grouped = defaultdict(list)
        for job in jobs:
            category = job.get('category', 'Other')
            grouped[category].append(job)
        return dict(grouped)
    
    def _build_html_header(self) -> str:
        """Build HTML email header."""
        today = datetime.now().strftime('%B %d, %Y')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .category {{
            margin-bottom: 40px;
        }}
        .category-title {{
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .job-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .job-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .job-company {{
            font-size: 16px;
            color: #34495e;
            margin-bottom: 8px;
        }}
        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 10px;
            font-size: 14px;
            color: #7f8c8d;
        }}
        .job-meta span {{
            display: inline-block;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-high {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        .job-reason {{
            font-style: italic;
            color: #555;
            margin: 10px 0;
            font-size: 14px;
        }}
        .apply-button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .apply-button:hover {{
            background: #5568d3;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Daily H1B-Eligible Data & Quant Jobs</h1>
        <p>Last 24 Hours | {today}</p>
    </div>
"""
    
    def _build_category_section(self, category: str, jobs: List[Dict]) -> str:
        """Build HTML section for a job category."""
        html = f'<div class="category">\n'
        html += f'<div class="category-title">{category} ({len(jobs)})</div>\n'
        
        for job in jobs:
            html += self._build_job_card(job)
        
        html += '</div>\n'
        return html
    
    def _build_job_card(self, job: Dict) -> str:
        """Build HTML card for a single job."""
        title = job.get('title', 'Unknown Title')
        company = job.get('company', 'Unknown Company')
        location = job.get('location', 'Unknown Location')
        sponsor_conf = job.get('sponsor_confidence', 'MEDIUM')
        reasoning = job.get('entry_level_reasoning', 'Entry-level position')
        url = job.get('url', '#')
        
        # Calculate hours ago
        posted_date = job.get('posted_date')
        hours_ago = self._calculate_hours_ago(posted_date)
        
        # Determine location type
        location_type = self._determine_location_type(location)
        
        # Badge class
        badge_class = 'badge-high' if sponsor_conf == 'HIGH' else 'badge-medium'
        
        html = f"""
<div class="job-card">
    <div class="job-title">{title}</div>
    <div class="job-company">🏢 {company}</div>
    <div class="job-meta">
        <span>📍 {location} ({location_type})</span>
        <span>⏰ {hours_ago}</span>
        <span class="badge {badge_class}">Sponsor: {sponsor_conf}</span>
    </div>
    <div class="job-reason">💡 {reasoning}</div>
    <a href="{url}" class="apply-button" target="_blank">Apply Now →</a>
</div>
"""
        return html
    
    def _calculate_hours_ago(self, posted_date) -> str:
        """Calculate hours ago from posted date."""
        if not posted_date:
            return 'Recently posted'
        
        try:
            if isinstance(posted_date, str):
                posted_dt = datetime.fromisoformat(posted_date)
            else:
                posted_dt = posted_date
            
            hours = (datetime.now() - posted_dt).total_seconds() / 3600
            
            if hours < 1:
                return 'Less than 1 hour ago'
            elif hours < 24:
                return f'{int(hours)} hours ago'
            else:
                return f'{int(hours/24)} days ago'
        except:
            return 'Recently posted'
    
    def _determine_location_type(self, location: str) -> str:
        """Determine if location is Remote, Hybrid, or Onsite."""
        location_lower = location.lower()
        
        if 'remote' in location_lower:
            return 'Remote'
        elif 'hybrid' in location_lower:
            return 'Hybrid'
        else:
            return 'Onsite'
    
    def _build_html_footer(self) -> str:
        """Build HTML email footer."""
        return """
    <div class="footer">
        <p>This is an automated digest of H1B-eligible entry-level data and quantitative finance jobs.</p>
        <p>Jobs are filtered for international students and ranked by relevance.</p>
    </div>
</body>
</html>
"""
    
    def _generate_empty_digest(self) -> str:
        """Generate email for when no jobs are found."""
        today = datetime.now().strftime('%B %d, %Y')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .message {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Daily H1B-Eligible Data & Quant Jobs</h1>
        <p>Last 24 Hours | {today}</p>
    </div>
    <div class="message">
        <h2>No New Jobs Found</h2>
        <p>No strong new postings matching your criteria were found in the last 24 hours.</p>
        <p>We'll continue monitoring and notify you when new opportunities arise.</p>
    </div>
</body>
</html>
"""
    
    def send_email(self, recipient_email: str, jobs: List[Dict]) -> bool:
        """
        Send email digest to recipient.
        
        Args:
            recipient_email: Recipient email address
            jobs: List of jobs to include in digest
            
        Returns:
            True if email sent successfully
        """
        subject = '[Daily H1B-Eligible Data & Quant Jobs | Last 24h]'
        html_body = self.generate_digest(jobs)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False


if __name__ == '__main__':
    # Test email generation
    email_sender = EmailDigest()
    
    test_jobs = [
        {
            'title': 'Data Scientist - New Grad',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'category': 'Data Scientist',
            'url': 'https://example.com/job1',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'HIGH',
            'entry_level_reasoning': 'New grad position with 0-1 years experience requirement'
        },
        {
            'title': 'Junior Data Analyst',
            'company': 'Microsoft',
            'location': 'Remote',
            'category': 'Data Analyst',
            'url': 'https://example.com/job2',
            'posted_date': datetime.now().isoformat(),
            'sponsor_confidence': 'MEDIUM',
            'entry_level_reasoning': 'Junior level role, entry position'
        }
    ]
    
    html = email_sender.generate_digest(test_jobs)
    
    # Save to file for preview
    with open('/home/ubuntu/job_monitor/test_digest.html', 'w') as f:
        f.write(html)
    
    print("Test digest generated: test_digest.html")
