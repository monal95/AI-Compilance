"""
Pattern Matcher for NLP Service.

Provides comprehensive regex pattern matching for
Indian product compliance requirements.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Match compliance patterns in text."""
    
    def __init__(self):
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Initialize compliance patterns."""
        
        self.patterns = {
            # FSSAI License Number - 14 digits with validation
            'fssai': {
                'patterns': [
                    r'(?:FSSAI|fssai)\s*(?:Lic(?:ense)?\.?\s*(?:No\.?)?|No\.?|Number)?\s*[:.]?\s*(\d{14})',
                    r'(?:License|Lic)\s*(?:No\.?)?\s*[:.]?\s*(\d{14})',
                    r'\b([1-3][0-9]\d{12})\b',  # 14 digits starting with state code
                ],
                'description': 'FSSAI License Number (14 digits)',
                'required': True,
            },
            
            # MRP - Maximum Retail Price
            'mrp': {
                'patterns': [
                    r'MRP\s*[:.]?\s*(?:Rs\.?|₹|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
                    r'(?:M\.?R\.?P\.?|Maximum\s*Retail\s*Price)\s*[:.]?\s*(?:Rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
                    r'(?:Rs\.?|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:only|/-)?',
                ],
                'description': 'Maximum Retail Price',
                'required': True,
            },
            
            # Manufacturing Date
            'mfg_date': {
                'patterns': [
                    r'(?:M(?:FG|anufactur(?:ed?|ing))\s*(?:Date)?|MFD|Mfd\.?|DOM)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?:Packed\s*(?:Date|On)|PKD)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?:MFG|MFD|PKD)\s*[:.]?\s*(\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*\d{2,4})',
                ],
                'description': 'Manufacturing/Packing Date',
                'required': True,
            },
            
            # Expiry Date
            'exp_date': {
                'patterns': [
                    r'(?:EXP(?:IRY)?(?:\s*DATE)?|Best\s*Before|BB|Use\s*By)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?:Valid\s*(?:Till|Until|Upto)|Use\s*Before)\s*[:.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?:EXP|BB)\s*[:.]?\s*(\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*\d{2,4})',
                ],
                'description': 'Expiry/Best Before Date',
                'required': True,
            },
            
            # Net Weight/Quantity
            'net_weight': {
                'patterns': [
                    r'(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity)|NW|N\.W\.)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l|ltr)',
                    r'(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l|ltr)\s*(?:NET|net)',
                    r'CONTENTS?\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l)',
                ],
                'description': 'Net Weight/Quantity',
                'required': True,
            },
            
            # Batch/Lot Number
            'batch': {
                'patterns': [
                    r'(?:Batch|Lot|B\.?\s*No\.?|L\.?\s*No\.?)\s*[:.]?\s*([A-Z0-9\-/]{4,20})',
                ],
                'description': 'Batch/Lot Number',
                'required': False,
            },
            
            # Country of Origin
            'country': {
                'patterns': [
                    r'(?:Country\s*of\s*Origin|Made\s*in|Product\s*of)\s*[:.]?\s*([A-Za-z\s]+?)(?=\.|,|MRP|Net|$)',
                    r'(?:MADE|PRODUCT)\s*(?:IN|OF)\s+([A-Z][A-Za-z\s]+?)(?=\.|,|$)',
                ],
                'description': 'Country of Origin',
                'required': True,
            },
            
            # Customer Care
            'customer_care': {
                'patterns': [
                    r'(?:Customer\s*Care|Consumer\s*(?:Helpline|Care)|Toll\s*Free)\s*[:.]?\s*([0-9\-\s]{10,})',
                    r'(?:Helpline|Contact)\s*[:.]?\s*(?:\+91|0)?[\s\-]?([0-9\s\-]{10,12})',
                ],
                'description': 'Customer Care Contact',
                'required': False,
            },
            
            # Allergen Information
            'allergens': {
                'patterns': [
                    r'(?:Contains?|May\s*Contain)\s*[:.]?\s*([A-Za-z,\s&]+)',
                    r'(?:ALLERGEN|WARNING)\s*[:.]?\s*(?:Contains?)?\s*([A-Za-z,\s&]+)',
                ],
                'description': 'Allergen Information',
                'required': False,
            },
            
            # Ingredients
            'ingredients': {
                'patterns': [
                    r'(?:Ingredients?)\s*[:.]?\s*(.+?)(?=\.|Nutritional|Net|MRP|$)',
                ],
                'description': 'Ingredients List',
                'required': False,
            },
            
            # Nutritional Information
            'nutrition': {
                'patterns': [
                    r'(?:Energy|Calories)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(?:kcal|kJ)',
                    r'(?:Protein|Carbohydrate|Fat)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*g',
                ],
                'description': 'Nutritional Information',
                'required': False,
            },
            
            # ISI/BIS Mark
            'isi_mark': {
                'patterns': [
                    r'(?:ISI|BIS|IS)\s*[:.]?\s*(\d{3,})',
                    r'(?:IS|ISI)\s*(\d{3,})\s*[:.]?\s*(?:\d{4})?',
                ],
                'description': 'ISI/BIS Certification',
                'required': False,
            },
            
            # Veg/Non-Veg Mark
            'veg_status': {
                'patterns': [
                    r'(?:100\s*%?\s*)?(?:VEGETARIAN|VEG(?:\.)?)',
                    r'NON[\s\-]?VEG(?:ETARIAN)?',
                    r'(?:CONTAINS?\s*)?(?:EGG|MEAT|FISH|CHICKEN)',
                ],
                'description': 'Vegetarian/Non-Vegetarian Status',
                'required': True,
            },
        }
    
    def match_pattern(self, text: str, pattern_name: str) -> Optional[dict]:
        """Match a specific pattern in text."""
        if pattern_name not in self.patterns:
            return None
        
        pattern_config = self.patterns[pattern_name]
        
        for pattern in pattern_config['patterns']:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return {
                    'found': True,
                    'value': match.group(1) if match.groups() else match.group(0),
                    'full_match': match.group(0),
                    'position': (match.start(), match.end()),
                    'pattern_used': pattern,
                }
        
        return {
            'found': False,
            'value': None,
            'description': pattern_config['description'],
            'required': pattern_config.get('required', False),
        }
    
    def match_all_patterns(self, text: str) -> dict:
        """Match all predefined patterns against text."""
        results = {}
        
        for name in self.patterns:
            results[name] = self.match_pattern(text, name)
        
        # Add summary
        total = len(self.patterns)
        found = sum(1 for r in results.values() if r and r.get('found'))
        required_total = sum(1 for p in self.patterns.values() if p.get('required'))
        required_found = sum(
            1 for name, result in results.items()
            if result and result.get('found') and self.patterns[name].get('required')
        )
        
        results['_summary'] = {
            'total_patterns': total,
            'patterns_matched': found,
            'match_percentage': round(found / total * 100, 1),
            'required_total': required_total,
            'required_found': required_found,
            'required_missing': required_total - required_found,
            'compliant': required_found == required_total,
        }
        
        return results
    
    def match_custom_patterns(
        self,
        text: str,
        patterns: list[str]
    ) -> dict:
        """Match custom regex patterns."""
        results = {}
        
        for i, pattern in enumerate(patterns):
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    results[f'pattern_{i}'] = {
                        'found': True,
                        'value': match.group(1) if match.groups() else match.group(0),
                        'full_match': match.group(0),
                        'pattern': pattern,
                    }
                else:
                    results[f'pattern_{i}'] = {
                        'found': False,
                        'pattern': pattern,
                    }
            except re.error as e:
                results[f'pattern_{i}'] = {
                    'found': False,
                    'error': str(e),
                    'pattern': pattern,
                }
        
        return results
    
    def get_missing_required(self, text: str) -> list[dict]:
        """Get list of missing required fields."""
        results = self.match_all_patterns(text)
        missing = []
        
        for name, config in self.patterns.items():
            if config.get('required'):
                result = results.get(name, {})
                if not result.get('found'):
                    missing.append({
                        'field': name,
                        'description': config['description'],
                        'required': True,
                    })
        
        return missing
    
    def validate_compliance(self, text: str) -> dict:
        """Validate text against compliance requirements."""
        results = self.match_all_patterns(text)
        summary = results.get('_summary', {})
        
        missing_required = self.get_missing_required(text)
        
        return {
            'compliant': summary.get('compliant', False),
            'score': summary.get('match_percentage', 0),
            'required_found': summary.get('required_found', 0),
            'required_total': summary.get('required_total', 0),
            'missing_required': missing_required,
            'details': {
                name: result for name, result in results.items()
                if not name.startswith('_')
            },
        }
    
    def get_pattern_descriptions(self) -> dict:
        """Get descriptions of all patterns."""
        return {
            name: {
                'description': config['description'],
                'required': config.get('required', False),
            }
            for name, config in self.patterns.items()
        }
