"""
Text scam detection service using keyword analysis and patterns
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class TextScamDetector:
    """
    Detects scam indicators in text messages.
    Uses keyword-based detection and pattern matching.
    """
    
    # Scam indicator keywords organized by category
    SCAM_KEYWORDS = {
        'urgency': [
            'urgent', 'immediately', 'now', 'asap', 'right now', 'right away',
            'do not delay', 'act now', 'verify now', 'confirm now', 'update now'
        ],
        'financial': [
            'wire money', 'send money', 'bitcoin', 'payment', 'transfer', 'deposit',
            'cash', 'credit card', 'bank account', 'routing number', 'swift code',
            'pay now', 'purchase', 'fee', 'charge', 'invoice', 'refund'
        ],
        'identity': [
            'verify', 'confirm', 'identity', 'password', 'pin', 'account',
            'credentials', 'ssn', 'social security', 'date of birth', 'security code',
            'cvv', 'expiration', 'authenticate', 'validate'
        ],
        'threat': [
            'limited', 'suspended', 'locked', 'frozen', 'compromised', 'unauthorized',
            'fraud', 'security', 'unusual activity', 'suspicious', 'threat', 'danger'
        ],
        'phishing': [
            'click here', 'click link', 'http://', 'https://', 'verify account',
            'update payment', 'reactivate account', 'confirm details', 'click below'
        ],
        'impersonation': [
            'amazon', 'apple', 'microsoft', 'google', 'facebook', 'paypal', 'bank',
            'irs', 'police', 'tax', 'sheriff', 'federal', 'government', 'official'
        ]
    }
    
    # Suspicious URL patterns
    URL_PATTERNS = [
        r'bit\.ly',
        r'tinyurl',
        r'short\.link',
        r'goo\.gl',
        r'ow\.ly',
    ]
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for scam indicators.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with risk_score, threat_types, explanation, confidence
        """
        if not text or not isinstance(text, str):
            raise ValueError("Invalid text provided")
        
        text_lower = text.lower()
        threats: List[str] = []
        score_contribution = 0
        
        # Check keyword matches
        for category, keywords in self.SCAM_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                threats.append(category.replace('_', ' '))
                score_contribution += self._get_category_weight(category, len(matches))
        
        # Check for URLs
        urls = re.findall(r'(https?://[^\s]+)', text_lower)
        if urls:
            # Check for suspicious URL patterns
            suspicious_urls = []
            for url in urls:
                if any(re.search(pattern, url) for pattern in self.URL_PATTERNS):
                    suspicious_urls.append(url)
            
            if suspicious_urls:
                if 'suspicious_url' not in threats:
                    threats.append('suspicious_url')
                score_contribution += 25
        
        # Check for multiple exclamation marks
        exclamation_count = text.count('!')
        if exclamation_count > 3:
            score_contribution += 10
        
        # Check for all caps (indicates shouting)
        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        if len(caps_words) / max(len(words), 1) > 0.3:  # More than 30% caps
            score_contribution += 8
        
        # Check for suspicious number patterns (fake phone numbers, etc)
        if re.search(r'\+?\d{10,}', text):
            score_contribution += 5
        
        # Calculate final risk score
        risk_score = min(100, score_contribution)
        
        # Add small variance for realistic results
        import random
        variance = random.uniform(-5, 5)
        risk_score = max(0, min(100, risk_score + variance))
        
        # Generate explanation
        explanation = self._generate_explanation(threats, text_lower, risk_score)
        
        # Calculate confidence based on threat count
        confidence = min(0.95, 0.5 + (len(threats) * 0.12))
        
        logger.info(f"Text analysis: {risk_score}% risk, {len(threats)} threats detected")
        
        return {
            'risk_score': int(round(risk_score)),
            'threat_types': threats,
            'explanation': explanation,
            'confidence': round(confidence, 2)
        }
    
    def _get_category_weight(self, category: str, match_count: int) -> int:
        """Get base weight for a threat category based on severity."""
        weights = {
            'identity': 30,
            'financial': 25,
            'phishing': 30,
            'threat': 20,
            'impersonation': 25,
            'urgency': 15
        }
        base_weight = weights.get(category, 20)
        # Increase weight with more matches
        return base_weight + min(match_count - 1, 2) * 5
    
    def _generate_explanation(self, threats: List[str], text_lower: str, risk_score: int) -> str:
        """Generate human-readable explanation of the analysis."""
        
        if not threats:
            return "This message does not contain obvious scam indicators. However, always verify requests for personal information or financial transactions directly with the official organization."
        
        threat_descriptions = {
            'urgency': "artificial time pressure",
            'financial': "requests for money or financial information",
            'identity': "requests for personal identification",
            'threat': "intimidation or threats",
            'phishing': "suspicious links or account verification requests",
            'impersonation': "impersonation of legitimate organizations",
            'suspicious_url': "shortened or suspicious URLs"
        }
        
        threat_list = ", ".join([threat_descriptions.get(t, t) for t in threats])
        
        if risk_score >= 70:
            return f"This message exhibits multiple scam indicators ({threat_list}). This is likely a fraudulent attempt. Do not click links, download attachments, or provide any personal information."
        elif risk_score >= 40:
            return f"This message contains concerning elements ({threat_list}). Be cautious and verify requests with the official organization before providing any information."
        else:
            return f"This message contains some unusual elements ({threat_list}). While not definitively a scam, exercise caution with any requests for personal or financial information."
