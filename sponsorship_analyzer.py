"""
H-1B Sponsorship Analyzer Module

Infers H-1B sponsorship likelihood using company data and textual analysis.
"""

from openai import OpenAI
from typing import Dict, Tuple, Optional
import json
import re


class SponsorshipAnalyzer:
    """Analyzes H-1B sponsorship likelihood for job postings."""
    
    def __init__(self):
        self.client = OpenAI()
        
        # Known sponsor-friendly companies (can be expanded)
        self.high_sponsor_companies = {
            'google', 'microsoft', 'amazon', 'meta', 'apple', 'netflix',
            'goldman sachs', 'jpmorgan', 'morgan stanley', 'citadel',
            'jane street', 'two sigma', 'de shaw', 'jump trading',
            'databricks', 'snowflake', 'stripe', 'airbnb', 'uber',
            'capital one', 'american express', 'visa', 'mastercard'
        }
        
        # Hard exclusion patterns
        self.exclusion_patterns = [
            r'no\s+visa\s+sponsorship',
            r'must\s+be\s+authorized\s+to\s+work\s+without\s+sponsorship',
            r'we\s+do\s+not\s+sponsor\s+visas',
            r'cannot\s+sponsor\s+work\s+authorization',
            r'us\s+citizenship\s+required',
            r'must\s+be\s+a\s+us\s+citizen',
            r'security\s+clearance\s+required'
        ]
        
        # Positive signal patterns
        self.positive_patterns = [
            r'open\s+to\s+international\s+candidates',
            r'visa\s+sponsorship\s+available',
            r'eligible\s+for\s+(future\s+)?visa\s+sponsorship',
            r'h-?1b\s+sponsorship',
            r'work\s+authorization\s+provided'
        ]
    
    def analyze_sponsorship(self, job: Dict) -> Tuple[str, str]:
        """
        Analyze H-1B sponsorship likelihood for a job.
        
        Args:
            job: Job dictionary with company, title, description
            
        Returns:
            Tuple of (confidence_level, reasoning)
            confidence_level: 'HIGH', 'MEDIUM', or 'LOW'
        """
        company = job.get('company', '').lower()
        description = job.get('description', '').lower()
        title = job.get('title', '').lower()
        
        # STEP 1: Hard exclusion check
        if self._has_exclusionary_language(description):
            return 'EXCLUDED', 'Job explicitly states no visa sponsorship'
        
        # STEP 2: Company-level signal
        company_signal = self._get_company_signal(company)
        
        # STEP 3: Textual signal (LLM analysis)
        text_signal, text_reasoning = self._analyze_text_signals(job)
        
        # Combine signals to determine final confidence
        confidence, reasoning = self._combine_signals(company_signal, text_signal, text_reasoning)
        
        return confidence, reasoning
    
    def _has_exclusionary_language(self, description: str) -> bool:
        """Check if description contains hard exclusion patterns."""
        for pattern in self.exclusion_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True
        return False
    
    def _get_company_signal(self, company: str) -> str:
        """Get company-level sponsorship signal."""
        company_lower = company.lower()
        
        # Check against known sponsor-friendly companies
        for known_sponsor in self.high_sponsor_companies:
            if known_sponsor in company_lower:
                return 'HIGH'
        
        # Check for company characteristics that suggest sponsorship
        # Large tech companies, financial institutions, consulting firms
        sponsor_indicators = [
            'technologies', 'tech', 'software', 'systems',
            'capital', 'financial', 'bank', 'securities',
            'consulting', 'analytics', 'data', 'research'
        ]
        
        if any(indicator in company_lower for indicator in sponsor_indicators):
            return 'MEDIUM'
        
        return 'LOW'
    
    def _analyze_text_signals(self, job: Dict) -> Tuple[str, str]:
        """Use LLM to analyze textual signals for sponsorship likelihood."""
        title = job.get('title', '')
        company = job.get('company', '')
        description = job.get('description', '')[:2000]  # Limit length
        
        # Check for positive patterns first
        description_lower = description.lower()
        has_positive_signal = any(
            re.search(pattern, description_lower) 
            for pattern in self.positive_patterns
        )
        
        if has_positive_signal:
            return 'HIGH', 'Job description explicitly mentions visa sponsorship'
        
        # Use LLM for nuanced analysis
        prompt = f"""Analyze this job posting for H-1B visa sponsorship likelihood.

Job Title: {title}
Company: {company}
Description: {description}

Assess the likelihood that this employer would sponsor H-1B visas for international candidates.

Consider:
1. Explicit mentions of visa sponsorship or international candidates
2. Language that suggests openness to diverse candidates
3. Absence of restrictive citizenship requirements
4. Company size and industry (tech/finance typically sponsor)
5. Role seniority and specialization

Respond in JSON format:
{{
  "signal": "HIGH/MEDIUM/LOW",
  "reasoning": "Brief explanation"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in H-1B visa sponsorship patterns and employer practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                signal = result.get('signal', 'LOW')
                reasoning = result.get('reasoning', '')
                return signal, reasoning
                
        except Exception as e:
            print(f"Error in LLM sponsorship analysis: {e}")
        
        return 'LOW', 'Unable to determine sponsorship likelihood'
    
    def _combine_signals(self, company_signal: str, text_signal: str, text_reasoning: str) -> Tuple[str, str]:
        """Combine company and text signals to determine final confidence."""
        signal_scores = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        
        company_score = signal_scores.get(company_signal, 1)
        text_score = signal_scores.get(text_signal, 1)
        
        # Weighted average (company signal weighted slightly higher)
        combined_score = (company_score * 0.6 + text_score * 0.4)
        
        # Determine final confidence
        if combined_score >= 2.5:
            confidence = 'HIGH'
        elif combined_score >= 1.8:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Build reasoning
        reasoning_parts = []
        if company_signal == 'HIGH':
            reasoning_parts.append('Known sponsor-friendly company')
        elif company_signal == 'MEDIUM':
            reasoning_parts.append('Company profile suggests potential sponsorship')
        
        if text_reasoning:
            reasoning_parts.append(text_reasoning)
        
        reasoning = '; '.join(reasoning_parts) if reasoning_parts else 'Limited sponsorship signals'
        
        return confidence, reasoning
    
    def should_discard(self, confidence: str, job_score: float = 0) -> bool:
        """
        Determine if job should be discarded based on sponsorship confidence.

        Args:
            confidence: Sponsorship confidence level
            job_score: Overall job quality score

        Returns:
            True if job should be discarded
        """
        # Only discard jobs that explicitly say "no sponsorship"
        if confidence == 'EXCLUDED':
            return True

        # Include all other jobs (HIGH, MEDIUM, LOW)
        return False


if __name__ == '__main__':
    # Test the analyzer
    analyzer = SponsorshipAnalyzer()
    
    test_job = {
        'title': 'Data Scientist - New Grad',
        'company': 'Google',
        'description': 'We are seeking recent graduates for our data science team. We welcome applications from international students and provide visa sponsorship for qualified candidates.'
    }
    
    confidence, reasoning = analyzer.analyze_sponsorship(test_job)
    print(f"Sponsorship Confidence: {confidence}")
    print(f"Reasoning: {reasoning}")
