"""
Entity Extractor for NLP Service.

Extracts compliance-related entities from text using regex patterns,
contextual analysis, and heuristics.
"""
import re
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract compliance entities from product text."""
    
    def __init__(self):
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Initialize regex patterns for entity extraction."""
        
        # FSSAI patterns
        self.fssai_patterns = [
            (r'FSSAI\s*(?:Lic(?:ense)?\.?\s*(?:No\.?)?|No\.?|Number)?\s*[:.]?\s*(\d{14})', 'high'),
            (r'Lic(?:ense)?\s*No\.?\s*[:.]?\s*(\d{14})', 'medium'),
            (r'\b(\d{14})\b', 'low'),  # Generic 14-digit
        ]
        
        # Price patterns
        self.price_patterns = [
            (r'MRP\s*[:.]?\s*(?:Rs\.?|₹|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)', 'high'),
            (r'(?:Rs\.?|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)', 'medium'),
            (r'Price\s*[:.]?\s*([0-9,]+(?:\.[0-9]{1,2})?)', 'medium'),
        ]
        
        # Date formats
        self.date_patterns = [
            r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})',
            r'(\d{1,2})\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*[,\s]?(\d{2,4})',
            r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*[,\s]?(\d{2,4})',
        ]
        
        # Manufacturing date context
        self.mfg_contexts = [
            'MFG', 'MFD', 'MANUFACTURED', 'PKD', 'PACKED', 'DOM', 'PRODUCTION'
        ]
        
        # Expiry date context
        self.exp_contexts = [
            'EXP', 'EXPIRY', 'BEST BEFORE', 'BB', 'USE BY', 'USE BEFORE', 
            'VALID TILL', 'VALID UNTIL', 'CONSUME BEFORE'
        ]
        
        # Weight patterns
        self.weight_patterns = [
            (r'Net\s*(?:Wt\.?|Weight|Qty\.?)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l|ltr)', 'high'),
            (r'(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l|ltr)\s*(?:NET|net)', 'high'),
            (r'CONTENTS?\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|l)', 'medium'),
        ]
        
        # Address patterns
        self.address_patterns = [
            r'(?:Mfg\.?\s*(?:by|at)|Manufactured\s*(?:by|at)|Marketed\s*by|Packed\s*(?:by|at)|Importer)\s*[:.]?\s*(.+?)(?=\.|MRP|Batch|Net|$)',
            r'(?:Address|Regd\.?\s*Office)\s*[:.]?\s*(.+?)(?=\.|MRP|Net|$)',
        ]
        
        # Contact patterns
        self.contact_patterns = [
            (r'(?:Customer\s*Care|Helpline|Toll\s*Free)\s*[:.]?\s*([0-9\-\s]{10,})', 'high'),
            (r'(?:Tel|Phone|Ph)\s*[:.]?\s*([0-9\-\s+()]{10,})', 'medium'),
            (r'(?:Email)\s*[:.]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 'high'),
        ]
        
        # Batch patterns
        self.batch_patterns = [
            (r'(?:Batch|Lot|B\.?\s*No\.?|L\.?\s*No\.?)\s*[:.]?\s*([A-Z0-9\-/]+)', 'high'),
        ]
        
        # Country patterns
        self.country_patterns = [
            (r'(?:Country\s*of\s*Origin|Made\s*in|Product\s*of)\s*[:.]?\s*([A-Za-z\s]+)', 'high'),
        ]
    
    def extract_fssai(self, text: str) -> Optional[dict]:
        """Extract FSSAI license number."""
        for pattern, confidence in self.fssai_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                if self._validate_fssai(number):
                    return {
                        'value': number,
                        'confidence': confidence,
                        'valid': True,
                        'state_code': number[:2],
                        'license_type': self._get_fssai_type(number[2]),
                    }
        return None
    
    def _validate_fssai(self, number: str) -> bool:
        """Validate FSSAI number format."""
        if len(number) != 14 or not number.isdigit():
            return False
        
        state_code = int(number[:2])
        if state_code < 1 or state_code > 37:
            return False
        
        license_type = int(number[2])
        if license_type not in [1, 2, 3]:
            return False
        
        return True
    
    def _get_fssai_type(self, type_code: str) -> str:
        """Get FSSAI license type name."""
        types = {
            '1': 'Central License',
            '2': 'State License',
            '3': 'Registration',
        }
        return types.get(type_code, 'Unknown')
    
    def extract_price(self, text: str) -> Optional[dict]:
        """Extract MRP/price from text."""
        for pattern, confidence in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 0 < price < 100000:
                        return {
                            'value': price,
                            'currency': 'INR',
                            'formatted': f'₹{price:,.2f}',
                            'confidence': confidence,
                        }
                except ValueError:
                    continue
        return None
    
    def extract_dates(self, text: str) -> dict:
        """Extract manufacturing and expiry dates."""
        result = {
            'manufacturing_date': None,
            'expiry_date': None,
            'best_before_months': None,
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line_upper = line.upper()
            
            # Check for manufacturing context
            if any(ctx in line_upper for ctx in self.mfg_contexts):
                date = self._find_date_in_text(line)
                if date and not result['manufacturing_date']:
                    result['manufacturing_date'] = date
            
            # Check for expiry context
            if any(ctx in line_upper for ctx in self.exp_contexts):
                # Check for "X months" format
                months_match = re.search(r'(\d+)\s*(?:months?|M)', line, re.IGNORECASE)
                if months_match:
                    result['best_before_months'] = int(months_match.group(1))
                
                date = self._find_date_in_text(line)
                if date and not result['expiry_date']:
                    result['expiry_date'] = date
        
        return result
    
    def _find_date_in_text(self, text: str) -> Optional[dict]:
        """Find and parse date in text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                parsed = self._parse_date(date_str)
                if parsed:
                    return {
                        'raw': date_str,
                        'parsed': parsed.strftime('%Y-%m-%d'),
                        'confidence': 'high',
                    }
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%d %b %Y', '%d %B %Y', '%d%b%Y',
            '%b %Y', '%B %Y',
        ]
        
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.upper(), fmt.upper())
            except ValueError:
                continue
        
        return None
    
    def extract_weight(self, text: str) -> Optional[dict]:
        """Extract net weight/quantity."""
        for pattern, confidence in self.weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()
                
                # Normalize units
                unit_map = {
                    'g': 'g', 'gm': 'g', 'gms': 'g',
                    'kg': 'kg', 'kgs': 'kg',
                    'ml': 'ml', 'l': 'L', 'ltr': 'L',
                }
                normalized_unit = unit_map.get(unit, unit)
                
                return {
                    'value': value,
                    'unit': normalized_unit,
                    'formatted': f'{value} {normalized_unit}',
                    'confidence': confidence,
                }
        return None
    
    def extract_batch(self, text: str) -> Optional[dict]:
        """Extract batch/lot number."""
        for pattern, confidence in self.batch_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                batch = match.group(1).strip()
                if len(batch) >= 4:
                    return {
                        'value': batch,
                        'confidence': confidence,
                    }
        return None
    
    def extract_address(self, text: str) -> Optional[dict]:
        """Extract manufacturer/packer address."""
        for pattern in self.address_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                # Clean up address
                address = re.sub(r'\s+', ' ', address)
                address = address.strip('.,;')
                
                if len(address) > 20:
                    return {
                        'value': address,
                        'confidence': 'medium',
                    }
        return None
    
    def extract_contact(self, text: str) -> Optional[dict]:
        """Extract customer care / contact info."""
        contacts = {}
        
        for pattern, confidence in self.contact_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                if '@' in value:
                    contacts['email'] = {
                        'value': value,
                        'confidence': confidence,
                    }
                else:
                    # Clean phone number
                    phone = re.sub(r'[\s\-()]', '', value)
                    if len(phone) >= 10:
                        contacts['phone'] = {
                            'value': phone,
                            'confidence': confidence,
                        }
        
        return contacts if contacts else None
    
    def extract_country(self, text: str) -> Optional[dict]:
        """Extract country of origin."""
        for pattern, confidence in self.country_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                country = re.sub(r'\s+', ' ', country)
                country = country.title()
                
                if len(country) >= 4 and len(country) <= 50:
                    return {
                        'value': country,
                        'confidence': confidence,
                    }
        return None
    
    def extract_all(self, text: str) -> dict:
        """Extract all compliance entities from text."""
        return {
            'fssai': self.extract_fssai(text),
            'price': self.extract_price(text),
            'dates': self.extract_dates(text),
            'weight': self.extract_weight(text),
            'batch': self.extract_batch(text),
            'address': self.extract_address(text),
            'contact': self.extract_contact(text),
            'country': self.extract_country(text),
        }
