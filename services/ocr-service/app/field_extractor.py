"""
Field Extractor for identifying regulatory fields from OCR text.

Extracts key compliance fields:
- FSSAI License Number
- MRP (Maximum Retail Price)
- Manufacturing Date
- Expiry Date / Best Before
- Net Weight/Quantity
- Manufacturer/Packer Address
- Country of Origin
- Nutritional Information
- Batch/Lot Number
- Customer Care Details
"""
import logging
import re
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extract regulatory and compliance fields from OCR text."""
    
    def __init__(self):
        # FSSAI patterns
        self.fssai_patterns = [
            r'(?:FSSAI|fssai)\s*(?:Lic(?:ense)?\.?\s*(?:No\.?)?|No\.?|Number)?\s*[:.]?\s*(\d{14})',
            r'(?:License|Lic)\s*(?:No\.?)?\s*[:.]?\s*(\d{14})',
            r'(\d{14})(?=\s*(?:FSSAI|fssai))',
            r'(?:भारतीय खाद्य सुरक्षा)\s*[:.]?\s*(\d{14})',  # Hindi
            r'\b(\d{14})\b',  # Fallback - 14 digit number
        ]
        
        # MRP patterns (Indian format)
        self.mrp_patterns = [
            r'(?:MRP|M\.R\.P|Maximum\s*Retail\s*Price|अधि\.\s*खु\.\s*मू)[:\s]*(?:Rs\.?|₹|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
            r'(?:Rs\.?|₹|INR)\s*([0-9,]+(?:\.[0-9]{1,2})?)(?:\s*/\-|\s*only)?',
            r'Price\s*[:.]?\s*(?:Rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
            r'([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:Rs\.?|₹|INR)',
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})',  # DD/MM/YYYY or DD-MM-YY
            r'(\d{1,2})\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*[,\s]?\s*(\d{2,4})',
            r'(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s*[,\s]?\s*(\d{2,4})',
            r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # YYYY/MM/DD
        ]
        
        # Manufacturing date keywords
        self.mfg_keywords = [
            r'(?:M(?:FG|anufactur(?:ed?|ing))\s*(?:Date)?|MFD|Mfd\.?|DOM|Date\s*of\s*Mfg\.?|Packed\s*(?:Date|On)|PKD|विनिर्माण)',
            r'(?:Best\s*Before|BB|Use\s*By)\s*(\d+)\s*(?:months?|M)\s*from',  # "Best Before X months from MFG"
        ]
        
        # Expiry date keywords
        self.exp_keywords = [
            r'(?:EXP(?:IRY)?(?:\s*DATE)?|Best\s*Before|BB|Use\s*By|Use\s*Before|Valid\s*(?:Till|Until|Upto)|समापन\s*तिथि)',
        ]
        
        # Net weight patterns
        self.weight_patterns = [
            r'(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity)|NW|N\.W\.|नेट\s*वजन)\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|kg|kgs|ml|l|ltr|litre)',
            r'(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|kg|kgs|ml|l|ltr|litre)(?:\s*(?:NET|net|\.))',
            r'CONTENTS?\s*[:.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|kg|kgs|ml|l|ltr|litre)',
        ]
        
        # Batch/Lot patterns
        self.batch_patterns = [
            r'(?:Batch|Lot|B\.?\s*No\.?|L\.?\s*No\.?|बैच)\s*[:.]?\s*([A-Z0-9\-/]+)',
            r'(?:B|L)\s*[:.]?\s*([A-Z0-9]{4,})',
        ]
        
        # Country of Origin
        self.origin_patterns = [
            r'(?:Country\s*of\s*Origin|Made\s*in|Product\s*of|Manufactured\s*in|उत्पादक\s*देश)\s*[:.]?\s*([A-Za-z\s]+)',
            r'(?:MADE|PRODUCT)\s*(?:IN|OF)\s+([A-Z][A-Za-z\s]+)',
        ]
        
        # Customer care patterns
        self.customer_care_patterns = [
            r'(?:Customer\s*Care|Consumer\s*(?:Helpline|Care)|Toll\s*Free|Helpline)\s*[:.]?\s*([0-9\-\s]{10,})',
            r'(?:\+91|0)[\s\-]?([0-9\s\-]{10,12})',
        ]
        
        # Allergen patterns
        self.allergen_patterns = [
            r'(?:Contains?|May\s*Contain|Allergen)\s*[:.]?\s*([A-Za-z,\s]+)',
            r'(?:WARNING|CAUTION)\s*[:.]?\s*(?:Contains?)?\s*([A-Za-z,\s]+)',
        ]
    
    def extract_fssai(self, text: str) -> Optional[dict]:
        """Extract FSSAI license number."""
        for pattern in self.fssai_patterns[:-1]:  # Skip generic 14-digit fallback
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                if self._validate_fssai(number):
                    return {
                        'value': number,
                        'valid': True,
                        'confidence': 'high',
                    }
        
        # Try fallback pattern
        matches = re.findall(r'\b(\d{14})\b', text)
        for match in matches:
            if self._validate_fssai(match):
                return {
                    'value': match,
                    'valid': True,
                    'confidence': 'medium',
                }
        
        return None
    
    def _validate_fssai(self, number: str) -> bool:
        """Validate FSSAI number format."""
        if len(number) != 14:
            return False
        
        # FSSAI format: First 2 digits are state code (01-37)
        state_code = int(number[:2])
        if state_code < 1 or state_code > 37:
            return False
        
        # Third digit: Type (1=Central, 2=State, 3=Registration)
        license_type = int(number[2])
        if license_type not in [1, 2, 3]:
            return False
        
        return True
    
    def extract_mrp(self, text: str) -> Optional[dict]:
        """Extract MRP (Maximum Retail Price)."""
        for pattern in self.mrp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 0 < price < 100000:  # Reasonable price range
                        return {
                            'value': price,
                            'currency': 'INR',
                            'formatted': f'₹{price:,.2f}',
                            'confidence': 'high' if 'MRP' in text.upper() else 'medium',
                        }
                except ValueError:
                    continue
        return None
    
    def extract_dates(self, text: str) -> dict:
        """Extract manufacturing and expiry dates."""
        result = {
            'manufacturing_date': None,
            'expiry_date': None,
        }
        
        # Split text into lines for context-aware extraction
        lines = text.split('\n')
        
        for line in lines:
            line_upper = line.upper()
            
            # Check for manufacturing date
            for keyword_pattern in self.mfg_keywords:
                if re.search(keyword_pattern, line_upper, re.IGNORECASE):
                    date = self._extract_date_from_text(line)
                    if date:
                        result['manufacturing_date'] = date
                        break
            
            # Check for expiry date
            for keyword_pattern in self.exp_keywords:
                if re.search(keyword_pattern, line_upper, re.IGNORECASE):
                    date = self._extract_date_from_text(line)
                    if date:
                        result['expiry_date'] = date
                        break
        
        # If we have MFG date but no expiry, look for "Best Before X months"
        if result['manufacturing_date'] and not result['expiry_date']:
            months_match = re.search(
                r'(?:Best\s*Before|BB|Use\s*(?:By|Within))\s*(\d+)\s*(?:months?|M)',
                text, re.IGNORECASE
            )
            if months_match:
                result['shelf_life_months'] = int(months_match.group(1))
        
        return result
    
    def _extract_date_from_text(self, text: str) -> Optional[dict]:
        """Extract date from text line."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Parse the matched date
                    date_str = match.group(0)
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        return {
                            'raw': date_str,
                            'parsed': parsed_date.strftime('%Y-%m-%d'),
                            'confidence': 'high',
                        }
                except Exception:
                    continue
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d %b %Y', '%d %B %Y',
            '%b %Y', '%B %Y',
        ]
        
        # Normalize date string
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def extract_net_weight(self, text: str) -> Optional[dict]:
        """Extract net weight/quantity."""
        for pattern in self.weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()
                
                # Normalize units
                unit_map = {
                    'g': 'g', 'gm': 'g', 'gms': 'g', 'gram': 'g',
                    'kg': 'kg', 'kgs': 'kg',
                    'ml': 'ml', 'l': 'L', 'ltr': 'L', 'litre': 'L',
                }
                normalized_unit = unit_map.get(unit, unit)
                
                return {
                    'value': value,
                    'unit': normalized_unit,
                    'formatted': f'{value} {normalized_unit}',
                    'confidence': 'high',
                }
        return None
    
    def extract_batch_number(self, text: str) -> Optional[dict]:
        """Extract batch/lot number."""
        for pattern in self.batch_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                batch = match.group(1).strip()
                if len(batch) >= 4:  # Minimum length for validity
                    return {
                        'value': batch,
                        'confidence': 'high',
                    }
        return None
    
    def extract_country_of_origin(self, text: str) -> Optional[dict]:
        """Extract country of origin."""
        for pattern in self.origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                # Clean up country name
                country = re.sub(r'\s+', ' ', country)
                country = country.title()
                
                if len(country) >= 4:
                    return {
                        'value': country,
                        'confidence': 'medium',
                    }
        return None
    
    def extract_customer_care(self, text: str) -> Optional[dict]:
        """Extract customer care contact."""
        for pattern in self.customer_care_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = re.sub(r'[\s\-]', '', match.group(1))
                if len(number) >= 10:
                    return {
                        'value': number,
                        'formatted': self._format_phone(number),
                        'confidence': 'medium',
                    }
        return None
    
    def _format_phone(self, number: str) -> str:
        """Format phone number for display."""
        if len(number) == 10:
            return f'{number[:5]}-{number[5:]}'
        elif len(number) == 11:
            return f'{number[:4]}-{number[4:7]}-{number[7:]}'
        return number
    
    def extract_allergens(self, text: str) -> Optional[dict]:
        """Extract allergen information."""
        for pattern in self.allergen_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                allergens_text = match.group(1).strip()
                # Split into individual allergens
                allergens = [
                    a.strip().lower() 
                    for a in re.split(r'[,;&]', allergens_text)
                    if a.strip()
                ]
                
                if allergens:
                    return {
                        'allergens': allergens,
                        'raw': allergens_text,
                        'confidence': 'medium',
                    }
        return None
    
    def extract_all_fields(self, text: str) -> dict:
        """
        Extract all regulatory fields from OCR text.
        
        Returns a comprehensive dict with all identified fields.
        """
        result = {
            'fssai': self.extract_fssai(text),
            'mrp': self.extract_mrp(text),
            'dates': self.extract_dates(text),
            'net_weight': self.extract_net_weight(text),
            'batch_number': self.extract_batch_number(text),
            'country_of_origin': self.extract_country_of_origin(text),
            'customer_care': self.extract_customer_care(text),
            'allergens': self.extract_allergens(text),
            'raw_text': text,
        }
        
        # Calculate completeness score
        fields_found = sum(1 for k, v in result.items() 
                         if v is not None and k not in ['raw_text', 'dates'])
        
        # Check dates separately
        if result['dates'].get('manufacturing_date'):
            fields_found += 1
        if result['dates'].get('expiry_date'):
            fields_found += 1
        
        total_fields = 9  # Total expected fields
        result['completeness_score'] = round(fields_found / total_fields * 100, 1)
        result['fields_found'] = fields_found
        result['fields_missing'] = total_fields - fields_found
        
        return result
