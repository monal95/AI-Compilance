import re
import logging
from typing import Optional

from backend.models import MandatoryDeclarations

logger = logging.getLogger(__name__)


class FieldIdentificationService:
    """
    Service to extract mandatory product declaration fields.
    Supports category-specific field extraction for Food, Electronics, Cosmetics.
    """
    
    def _capture(self, pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip(" .,-")
        return value or None

    def _check_prohibited_expressions(self, text: str) -> list:
        """Check for prohibited expressions in net quantity"""
        prohibited = ["approx", "approximately", "about", "minimum", "min", 
                     "average", "avg", "not less than", "atleast", "at least"]
        found = []
        if text:
            text_lower = text.lower()
            for expr in prohibited:
                if expr in text_lower:
                    found.append(expr)
        return found
    
    def _validate_net_quantity_unit(self, net_qty: str) -> bool:
        """Validate net quantity uses standard SI units"""
        if not net_qty:
            return False
        valid_units = r"\b(g|gram|grams|kg|kilogram|kilograms|ml|millilitre|millilitres|l|litre|litres|cm|centimetre|m|metre|metres|pcs|pieces|units?)\b"
        return bool(re.search(valid_units, net_qty, re.IGNORECASE))

    def _extract_universal_fields(self, combined: str) -> dict:
        """Extract fields common to all product categories"""
        # Prioritize Manufacturer over Brand for manufacturer field
        manufacturer = self._capture(
            r"Manufacturer\s*[:\-]\s*([^\n|,]+)",
            combined,
        )
        if not manufacturer:
            manufacturer = self._capture(
                r"(?:Importer|Marketed\s*by|Packed\s*by)\s*[:\-]\s*([^\n|,]+)",
                combined,
            )
        if not manufacturer:
            manufacturer = self._capture(
                r"Brand\s*[:\-]\s*([^\n|,]+)",
                combined,
            )
        
        # Extract manufacturer/importer complete address
        manufacturer_address = self._capture(
            r"(?:Manufacturer|Mfg\.?|Packed\s*by|Marketed\s*by)\s*[:\-]?\s*(?:[^,\n]+,)?\s*([A-Za-z0-9\s,\.\-]+(?:\d{6}|\d{3}\s*\d{3}))",
            combined,
        )
        
        importer_address = self._capture(
            r"(?:Importer|Imported\s*by)\s*[:\-]?\s*([^\n]+(?:\d{6}|\d{3}\s*\d{3})?)",
            combined,
        )
        
        # Extract common/generic name (product type, not brand name)
        common_generic_name = self._capture(
            r"(?:Product\s*(?:Type|Name)|Generic\s*Name|Type|Category)\s*[:\-]?\s*([A-Za-z\s]+)",
            combined,
        )
        if not common_generic_name:
            # Try to infer from product title or description
            common_generic_name = self._capture(
                r"(?:Biscuits?|Shampoo|Oil|Rice|Tea|Coffee|Chips?|Chocolate|Cream|Lotion|Soap|Powder|Juice|Drink)",
                combined,
            )
        
        # Extract raw net quantity for validation
        net_quantity_raw = self._capture(
            r"(?:Net\s*(?:Qty|Quantity|Wt|Weight|Content\s*Volume?)|Item\s*Weight|Weight)\s*[:\-]?\s*([^\n|]{5,50})",
            combined,
        )
        
        # Extract clean net quantity
        net_quantity = self._capture(
            r"(?:Net\s*(?:Qty|Quantity|Wt|Weight|Content\s*Volume?)|Item\s*Weight|Weight)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kg|kilogram|g|gram|grams|ml|millilitre|milliliter|millilitres|milliliters|l|litre|litres|liter|liters|pcs|pieces|units?)[s]?)",
            combined,
        )
        
        # Check for prohibited expressions in net quantity
        prohibited_found = self._check_prohibited_expressions(net_quantity_raw) if net_quantity_raw else []
        unit_valid = self._validate_net_quantity_unit(net_quantity) if net_quantity else False
            
        return {
            "manufacturer_or_importer": manufacturer,
            "manufacturer_address": manufacturer_address,
            "importer_address": importer_address,
            "common_generic_name": common_generic_name,
            "net_quantity": net_quantity,
            "net_quantity_prohibited_expressions": prohibited_found if prohibited_found else None,
            "net_quantity_unit_valid": unit_valid,
            "mrp_inclusive_of_taxes": self._capture(
                r"(?:MRP|M\.R\.P\.?|Maximum\s*Retail\s*Price)\s*[:₹Rs\.\s]*([0-9,]+(?:\.[0-9]{1,2})?\s*(?:incl(?:usive)?\s*of\s*(?:all\s*)?taxes)?)",
                combined,
            ),
            "consumer_care_information": self._capture(
                r"(?:Consumer\s*(?:Care|Complaint|Support)|Customer\s*Care|Contact\s*(?:Us|Info)|Helpline|Toll\s*Free)\s*[:\-]?\s*([^\n|]+)",
                combined,
            ),
            "date_of_manufacture_or_import": self._capture(
                r"(?:Date\s*(?:of\s*)?(?:Manufacture|Mfg|Import|Packing)|Mfg\.?\s*Date|Manufactured\s*on|Imported\s*on|Packed\s*on|Date\s*First\s*Available)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{1,2}\s*[A-Za-z]{3,9}\s*[0-9]{2,4}|[A-Za-z]{3,9}\s*[0-9]{1,2}[,]?\s*[0-9]{2,4})",
                combined,
            ),
            "country_of_origin": self._capture(
                r"(?:Country\s*of\s*Origin|Made\s*in|Manufactured\s*in|Origin)\s*[:\-]?\s*([A-Za-z ]{2,30})",
                combined,
            ),
        }

    def _extract_food_fields(self, combined: str) -> dict:
        """Extract food-specific fields (FSSAI, expiry, ingredients, etc.)"""
        
        # Try to extract comprehensive nutritional info
        nutritional_info = self._capture(
            r"Energy\s*\(?(?:kcal)?\)?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kcal|cal|Kilocalories|kJ)?)",
            combined,
        )
        if not nutritional_info:
            nutritional_info = self._capture(
                r"Calories?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?[^\n]*)",
                combined,
            )
        
        return {
            "fssai_license": self._capture(
                r"(?:FSSAI\s*(?:Lic(?:ense)?\.?\s*)?(?:No\.?)?|License\s*No\.?|Lic\.?\s*No\.?)\s*[:\-]?\s*([0-9]{10,14})",
                combined,
            ),
            "expiry_date": self._capture(
                r"(?:Exp(?:iry)?\.?\s*Date|Best\s*Before|Use\s*By|BB|Shelf\s*Life)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{1,2}\s*[A-Za-z]{3,9}\s*[0-9]{2,4}|[A-Za-z]{3,9}\s*[0-9]{1,2}[,]?\s*[0-9]{2,4}|[0-9]+\s*(?:months?|days?|years?))",
                combined,
            ),
            "ingredients_list": self._capture(
                r"Ingredients?\s*[:\-]?\s*([^\n]+(?:oil|sugar|salt|water|flour|milk|spice|extract|acid|preservative|vitamin|mineral|refined|soya|rice)[^\n]*)",
                combined,
            ),
            "nutritional_info": nutritional_info,
            "allergen_info": self._capture(
                r"(?:Allergen(?:s)?(?:\s*Info(?:rmation)?)?|May\s*Contain)\s*[:\-]?\s*([^\n]*(?:nuts?|milk|soy|wheat|gluten|egg|peanut|sesame|fish|shellfish|sulphite|mustard)[^\n]*)",
                combined,
            ),
            "veg_nonveg_symbol": self._capture(
                r"(?:Ingredient\s*Type|Diet\s*Type)?[:\-]?\s*(Vegetarian|Non[\s\-]?Vegetarian|Veg(?:an)?|Non[\s\-]?Veg)",
                combined,
            ),
            "batch_lot_number": self._capture(
                r"(?:Batch\s*(?:No\.?)?|Lot\s*(?:No\.?)?|B\.?\s*No\.?)\s*[:\-]?\s*([A-Z0-9\-]{4,})",
                combined,
            ),
            "storage_instructions": self._capture(
                r"(?:Storage|Store|Directions?)\s*[:\-]?\s*([^\n]*(?:cool|dry|refrigerat|freez|temperature|away\s*from|room\s*temp|dark|moisture)[^\n]*)",
                combined,
            ),
        }

    def _extract_electronics_fields(self, combined: str) -> dict:
        """Extract electronics-specific fields (BIS, warranty, power, etc.)"""
        return {
            "bis_certification": self._capture(
                r"(?:BIS|ISI|Bureau\s*of\s*Indian\s*Standards?)(?:\s*Cert(?:ification)?)?(?:\s*No\.?)?\s*[:\-]?\s*(R-[0-9]+|[A-Z]{2,3}[0-9]+)",
                combined,
            ),
            "model_number": self._capture(
                r"(?:Model\s*(?:No\.?|Number)?|Item\s*Model)\s*[:\-]?\s*([A-Z0-9\-]+)",
                combined,
            ),
            "warranty_period": self._capture(
                r"(?:Warranty|Guarantee)\s*[:\-]?\s*([0-9]+\s*(?:year|month|yr|mo)[s]?)",
                combined,
            ),
            "power_rating": self._capture(
                r"(?:Power|Wattage|Rating)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:W|Watt|kW)[s]?)",
                combined,
            ),
            "voltage_frequency": self._capture(
                r"(?:Voltage|Input|Operating)\s*[:\-]?\s*([0-9]+(?:\-[0-9]+)?\s*V(?:olt)?[s]?(?:\s*[/,]\s*[0-9]+\s*Hz)?)",
                combined,
            ),
            "energy_rating": self._capture(
                r"(?:Energy\s*(?:Rating|Star)|Star\s*Rating|BEE)\s*[:\-]?\s*([0-9]\s*(?:Star)?s?)",
                combined,
            ),
            "serial_number": self._capture(
                r"(?:Serial\s*(?:No\.?|Number)?|S\/N)\s*[:\-]?\s*([A-Z0-9\-]{6,})",
                combined,
            ),
            "safety_instructions": self._capture(
                r"(?:Safety|Warning|Caution)\s*[:\-]?\s*([^\n]+(?:shock|fire|water|heat)[^\n]*)",
                combined,
            ),
        }

    def _extract_cosmetics_fields(self, combined: str) -> dict:
        """Extract cosmetics-specific fields (batch, usage, warnings, etc.)"""
        return {
            "batch_lot_number": self._capture(
                r"(?:Batch\s*(?:No\.?)?|Lot\s*(?:No\.?)?|B\.?\s*No\.?)\s*[:\-]?\s*([A-Z0-9\-]+)",
                combined,
            ),
            "expiry_date": self._capture(
                r"(?:Exp(?:iry)?\.?\s*Date|Best\s*Before|Use\s*By|BB)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[A-Za-z]{3,9}\s*[0-9]{2,4})",
                combined,
            ),
            "ingredients_list": self._capture(
                r"(?:Ingredients?|Contains|Composition)\s*[:\-]\s*([^\n]+(?:\n[^\n]+)?)",
                combined,
            ),
            "usage_instructions": self._capture(
                r"(?:Usage|How\s*to\s*Use|Directions?|Apply)\s*[:\-]?\s*([^\n]+)",
                combined,
            ),
            "warnings": self._capture(
                r"(?:Warning|Caution|Note)\s*[:\-]?\s*([^\n]+)",
                combined,
            ),
            "cruelty_free": self._capture(
                r"(Cruelty[\s\-]?Free|Not\s*Tested\s*on\s*Animals?|Vegan)",
                combined,
            ),
            "allergen_info": self._capture(
                r"(?:Allergen(?:s)?|Contains|May\s*Contain)\s*[:\-]?\s*([^\n]+)",
                combined,
            ),
        }

    def extract_mandatory_fields(
        self, 
        scraped_text: str, 
        ocr_text: str,
        category: Optional[str] = None
    ) -> MandatoryDeclarations:
        """
        Extract mandatory fields from combined text.
        
        Args:
            scraped_text: Text from web scraping
            ocr_text: Text from OCR extraction
            category: Product category (food, electronics, cosmetics)
            
        Returns:
            MandatoryDeclarations with all extracted fields
        """
        combined = "\n".join([scraped_text or "", ocr_text or ""])
        
        # Start with universal fields
        fields = self._extract_universal_fields(combined)
        
        # Normalize country of origin
        if fields.get("country_of_origin"):
            fields["country_of_origin"] = fields["country_of_origin"].title()
        
        # Add category-specific fields
        category_lower = (category or "").lower()
        
        if category_lower == "food":
            food_fields = self._extract_food_fields(combined)
            fields.update({k: v for k, v in food_fields.items() if v})
            logger.info(f"Extracted {sum(1 for v in food_fields.values() if v)} food-specific fields")
            
        elif category_lower == "electronics":
            electronics_fields = self._extract_electronics_fields(combined)
            fields.update({k: v for k, v in electronics_fields.items() if v})
            logger.info(f"Extracted {sum(1 for v in electronics_fields.values() if v)} electronics-specific fields")
            
        elif category_lower == "cosmetics":
            cosmetics_fields = self._extract_cosmetics_fields(combined)
            fields.update({k: v for k, v in cosmetics_fields.items() if v})
            logger.info(f"Extracted {sum(1 for v in cosmetics_fields.values() if v)} cosmetics-specific fields")
        
        else:
            # For generic/unknown, try to extract common fields from all categories
            # This helps when category is auto-detected later
            for extract_func in [self._extract_food_fields, self._extract_electronics_fields, self._extract_cosmetics_fields]:
                category_fields = extract_func(combined)
                # Only add fields that aren't already present
                fields.update({k: v for k, v in category_fields.items() if v and not fields.get(k)})
        
        return MandatoryDeclarations(**fields)
