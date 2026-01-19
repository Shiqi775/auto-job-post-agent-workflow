"""
Job Classification Module

Classifies jobs into categories and validates entry-level criteria using LLM.
"""

from openai import OpenAI
from typing import Dict, Optional, Tuple
import json
import re


class JobClassifier:
    """Classifies jobs and validates entry-level fit."""
    
    def __init__(self):
        self.client = OpenAI()
        self.categories = [
            'Data Scientist',
            'Data Analyst',
            'Quantitative Finance',
            'Data Engineer',
            'Other'
        ]
    
    def classify_job(self, job: Dict) -> Tuple[str, bool, str]:
        """
        Classify a job into a category and validate entry-level fit.
        
        Args:
            job: Job dictionary with title, company, location, description
            
        Returns:
            Tuple of (category, is_entry_level, reasoning)
        """
        title = job.get('title', '')
        description = job.get('description', '')
        
        # Quick title-based classification for efficiency
        category = self._quick_classify(title)
        
        # If uncertain or need validation, use LLM
        if category == 'Other' or not description:
            category, is_entry_level, reasoning = self._llm_classify(job)
        else:
            is_entry_level, reasoning = self._validate_entry_level(job)
        
        return category, is_entry_level, reasoning
    
    def _quick_classify(self, title: str) -> str:
        """Quick rule-based classification from job title."""
        title_lower = title.lower()
        
        # Data Scientist patterns
        if any(keyword in title_lower for keyword in ['data scientist', 'ml engineer', 'machine learning']):
            return 'Data Scientist'
        
        # Data Analyst patterns
        if any(keyword in title_lower for keyword in ['data analyst', 'business analyst', 'analytics']):
            return 'Data Analyst'
        
        # Quantitative Finance patterns
        quant_keywords = ['quant', 'quantitative', 'financial engineer', 'trading', 'risk analyst']
        if any(keyword in title_lower for keyword in quant_keywords):
            return 'Quantitative Finance'
        
        # Data Engineer patterns
        if any(keyword in title_lower for keyword in ['data engineer', 'etl', 'data pipeline']):
            return 'Data Engineer'
        
        return 'Other'
    
    def _llm_classify(self, job: Dict) -> Tuple[str, bool, str]:
        """Use LLM to classify job and validate entry-level fit."""
        title = job.get('title', '')
        company = job.get('company', '')
        description = job.get('description', '')[:2000]  # Limit description length
        
        prompt = f"""Analyze this job posting and provide:
1. Category: One of [Data Scientist, Data Analyst, Quantitative Finance, Data Engineer, Other]
2. Is it entry-level? (0-2 years experience required)
3. Brief reasoning

Job Title: {title}
Company: {company}
Description: {description}

Quantitative Finance includes: Quantitative Analyst, Quantitative Researcher, Quant Trader (Junior/New Grad), Financial Engineer, Quant Risk/Model Validation (entry-level).

Entry-level criteria (at least ONE must be met):
- Title includes: "New Grad", "Entry Level", "Junior", "I", "Associate"
- Experience requirement ≤ 2 years
- Early-career responsibility and scope
- Degree-focused hiring (BS/MS/PhD students or recent graduates)

Respond in JSON format:
{{
  "category": "...",
  "is_entry_level": true/false,
  "reasoning": "..."
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a job classification expert specializing in data and quantitative finance roles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                category = result.get('category', 'Other')
                is_entry_level = result.get('is_entry_level', False)
                reasoning = result.get('reasoning', '')
                
                return category, is_entry_level, reasoning
            
        except Exception as e:
            print(f"Error in LLM classification: {e}")
        
        # Fallback to quick classification
        return self._quick_classify(job.get('title', '')), False, 'Classification failed'
    
    def _validate_entry_level(self, job: Dict) -> Tuple[bool, str]:
        """Validate if job meets entry-level criteria."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        # Check title for entry-level indicators
        entry_indicators = ['new grad', 'entry level', 'junior', ' i ', 'associate', 'early career']
        title_match = any(indicator in title for indicator in entry_indicators)
        
        # Check for experience requirements
        exp_pattern = r'(\d+)\+?\s*years?\s*(of)?\s*experience'
        exp_matches = re.findall(exp_pattern, description)
        
        max_exp = 0
        if exp_matches:
            max_exp = max(int(match[0]) for match in exp_matches)
        
        # Check for exclusionary senior terms
        senior_terms = ['senior', 'staff', 'principal', 'lead', 'manager', 'director']
        has_senior_term = any(term in title for term in senior_terms)
        
        # Determine if entry-level
        is_entry_level = (title_match or max_exp <= 2) and not has_senior_term
        
        reasoning = []
        if title_match:
            reasoning.append("Title indicates entry-level")
        if max_exp <= 2 and max_exp > 0:
            reasoning.append(f"Requires {max_exp} years experience")
        if has_senior_term:
            reasoning.append("Contains senior-level terminology")
        
        return is_entry_level, '; '.join(reasoning) if reasoning else 'Entry-level validation'
    
    def should_discard(self, category: str, is_entry_level: bool) -> bool:
        """Determine if job should be discarded."""
        if category == 'Other':
            return True
        if not is_entry_level:
            return True
        return False


if __name__ == '__main__':
    # Test the classifier
    classifier = JobClassifier()
    
    test_job = {
        'title': 'Junior Data Scientist - New Grad',
        'company': 'Tech Corp',
        'location': 'San Francisco, CA',
        'description': 'We are seeking a recent graduate with a BS/MS in Computer Science or related field. 0-1 years of experience required. You will work on machine learning models and data analysis.'
    }
    
    category, is_entry_level, reasoning = classifier.classify_job(test_job)
    print(f"Category: {category}")
    print(f"Entry Level: {is_entry_level}")
    print(f"Reasoning: {reasoning}")
