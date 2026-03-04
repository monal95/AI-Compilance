"""
Text Normalizer for NLP Service.

Handles text cleaning, normalization, and preprocessing for
multiple languages used in Indian product labels.
"""
import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextNormalizer:
    """Normalize and clean text for NLP processing."""
    
    SUPPORTED_LANGUAGES = [
        "english", "hindi", "tamil", "telugu", "kannada",
        "marathi", "bengali", "gujarati", "punjabi", "malayalam"
    ]
    
    def __init__(self):
        self._changes = []
        self._setup_transliterations()
    
    def _setup_transliterations(self):
        """Setup common transliterations for Indian languages."""
        # Common Hindi/Devanagari numeric representations
        self.hindi_numerals = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
        }
        
        # Common abbreviations expansion
        self.abbreviations = {
            r'\bMfg\.?\b': 'Manufacturing',
            r'\bMfd\.?\b': 'Manufactured',
            r'\bPkd\.?\b': 'Packed',
            r'\bExp\.?\b': 'Expiry',
            r'\bMRP\b': 'Maximum Retail Price',
            r'\bWt\.?\b': 'Weight',
            r'\bQty\.?\b': 'Quantity',
            r'\bLic\.?\b': 'License',
            r'\bNo\.?\b': 'Number',
            r'\bRegd\.?\b': 'Registered',
            r'\bPvt\.?\b': 'Private',
            r'\bLtd\.?\b': 'Limited',
            r'\bInc\.?\b': 'Incorporated',
        }
        
        # Currency symbols normalization
        self.currency_map = {
            '₹': 'Rs.',
            'Rs': 'Rs.',
            'Rs.': 'Rs.',
            'INR': 'Rs.',
        }
        
        # Unit normalization
        self.unit_map = {
            r'\bgms?\b': 'g',
            r'\bgrm?s?\b': 'g',
            r'\bkgs?\b': 'kg',
            r'\bkilos?\b': 'kg',
            r'\bmls?\b': 'ml',
            r'\bltrs?\b': 'L',
            r'\blitres?\b': 'L',
            r'\bliters?\b': 'L',
        }
    
    def normalize(
        self,
        text: str,
        language: str = "english",
        remove_special_chars: bool = True,
        lowercase: bool = False,
        expand_abbreviations: bool = True,
        normalize_numbers: bool = True,
        normalize_units: bool = True,
    ) -> str:
        """
        Normalize text with various cleaning options.
        
        Args:
            text: Input text
            language: Source language for context
            remove_special_chars: Remove unusual special characters
            lowercase: Convert to lowercase
            expand_abbreviations: Expand common abbreviations
            normalize_numbers: Convert regional numerals to Arabic
            normalize_units: Standardize unit representations
        
        Returns:
            Normalized text
        """
        self._changes = []
        
        if not text:
            return ""
        
        original = text
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Convert regional numerals if present
        if normalize_numbers:
            text = self._normalize_numerals(text)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Remove control characters
        text = self._remove_control_chars(text)
        
        # Expand abbreviations
        if expand_abbreviations:
            text = self._expand_abbreviations(text)
        
        # Normalize units
        if normalize_units:
            text = self._normalize_units(text)
        
        # Remove special chars if requested
        if remove_special_chars:
            text = self._remove_special_chars(text)
        
        # Lowercase if requested
        if lowercase:
            text = text.lower()
            self._changes.append("converted to lowercase")
        
        # Final cleanup
        text = self._final_cleanup(text)
        
        if text != original:
            logger.debug(f"Normalized text: {len(self._changes)} changes made")
        
        return text
    
    def _normalize_numerals(self, text: str) -> str:
        """Convert regional numerals to Arabic numerals."""
        changed = False
        for regional, arabic in self.hindi_numerals.items():
            if regional in text:
                text = text.replace(regional, arabic)
                changed = True
        
        if changed:
            self._changes.append("converted regional numerals")
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize all whitespace to single spaces."""
        # Replace various whitespace chars with regular space
        text = re.sub(r'[\t\r\n\f\v]+', '\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r'[ ]+', ' ', text)
        # Replace multiple newlines with single newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _remove_control_chars(self, text: str) -> str:
        """Remove control characters except newlines."""
        # Keep printable chars and newlines
        cleaned = ''.join(
            char for char in text
            if char.isprintable() or char in '\n\r\t'
        )
        
        if len(cleaned) != len(text):
            self._changes.append("removed control characters")
        
        return cleaned
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        for abbr, expansion in self.abbreviations.items():
            if re.search(abbr, text, re.IGNORECASE):
                # Keep original for pattern matching, just track the expansion
                pass  # Don't expand - keep abbreviations for better pattern matching
        
        return text
    
    def _normalize_units(self, text: str) -> str:
        """Normalize unit representations."""
        for pattern, replacement in self.unit_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_special_chars(self, text: str) -> str:
        """Remove unusual special characters while keeping meaningful ones."""
        # Keep: letters, numbers, common punctuation, currency symbols
        # Remove: unusual symbols, emoji, decorative chars
        
        # Pattern for chars to keep
        keep_pattern = r'[a-zA-Z0-9\s.,;:!?\'"()\[\]{}\-_/\\@#$%&*+=₹°\n]'
        
        # Keep Devanagari and other Indian scripts
        indian_scripts = r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0B00-\u0B7F\u0C00-\u0C7F\u0D00-\u0D7F]'
        
        def should_keep(char):
            return (
                re.match(keep_pattern, char) or
                re.match(indian_scripts, char) or
                unicodedata.category(char) in ['Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd', 'Nl', 'No']
            )
        
        cleaned = ''.join(char if should_keep(char) else ' ' for char in text)
        
        if len(cleaned) != len(text):
            self._changes.append("removed special characters")
        
        return cleaned
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup."""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Remove spaces before punctuation
        text = re.sub(r' ([.,;:!?])', r'\1', text)
        # Add space after punctuation if missing
        text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def get_changes_summary(self) -> list[str]:
        """Get list of changes made during normalization."""
        return self._changes.copy()
    
    def normalize_for_comparison(self, text: str) -> str:
        """
        Aggressive normalization for text comparison.
        
        Useful for matching similar text patterns.
        """
        text = self.normalize(
            text,
            remove_special_chars=True,
            lowercase=True,
            normalize_numbers=True,
            normalize_units=True,
        )
        
        # Remove all punctuation for comparison
        text = re.sub(r'[^\w\s]', '', text)
        # Normalize all whitespace to single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Handle common sentence endings
        text = re.sub(r'([.!?])\s+', r'\1\n', text)
        sentences = [s.strip() for s in text.split('\n') if s.strip()]
        return sentences
    
    def tokenize(self, text: str) -> list[str]:
        """Simple word tokenization."""
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
