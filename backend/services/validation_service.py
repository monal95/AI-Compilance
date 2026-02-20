import json
import logging
import re
from pathlib import Path
from typing import Optional

from backend.models import MandatoryDeclarations, Violation

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Category-based Legal Metrology Validation Service.
    Dynamically applies rules based on product category.
    """
    
    CATEGORY_FOOD = "food"
    CATEGORY_ELECTRONICS = "electronics"
    CATEGORY_COSMETICS = "cosmetics"
    CATEGORY_GENERIC = "generic"
    
    VALID_CATEGORIES = [CATEGORY_FOOD, CATEGORY_ELECTRONICS, CATEGORY_COSMETICS, CATEGORY_GENERIC]

    def __init__(
        self, 
        rules_path: str = "backend/legal_rules/audit_rules.json",
        category_rules_path: str = "backend/legal_rules/category_rules.json"
    ) -> None:
        self.rules_path = Path(rules_path)
        self.category_rules_path = Path(category_rules_path)
        self.generic_rules = self._load_rules()
        self.category_rules = self._load_category_rules()

    def _load_rules(self) -> dict:
        """Load generic fallback rules"""
        try:
            with self.rules_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Failed to load generic rules: {e}")
            return {"rules": []}

    def _load_category_rules(self) -> dict:
        """Load category-specific rules"""
        try:
            with self.category_rules_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            logger.warning(f"Failed to load category rules: {e}")
            return {"categories": {}}

    def get_available_categories(self) -> list[dict]:
        """Return list of available product categories"""
        categories = []
        for key, value in self.category_rules.get("categories", {}).items():
            categories.append({
                "id": key,
                "name": value.get("name", key.title()),
                "description": value.get("description", ""),
                "rule_count": len(value.get("rules", []))
            })
        return categories

    def detect_category(self, text: str) -> str:
        """
        Auto-detect product category based on text content.
        Returns the category ID or 'generic' if not detected.
        """
        text_lower = text.lower()
        category_keywords = self.category_rules.get("category_keywords", {})
        
        # Count keyword matches for each category
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            # Return category with highest match
            best_category = max(scores, key=scores.get)
            logger.info(f"Auto-detected category: {best_category} (score: {scores[best_category]})")
            return best_category
        
        return self.CATEGORY_GENERIC

    def get_rules_for_category(self, category: str) -> list[dict]:
        """Get rules for a specific category"""
        category = category.lower() if category else self.CATEGORY_GENERIC
        
        if category not in self.VALID_CATEGORIES:
            category = self.CATEGORY_GENERIC
        
        category_data = self.category_rules.get("categories", {}).get(category)
        
        if category_data:
            return category_data.get("rules", [])
        
        # Fallback to generic rules
        return self.generic_rules.get("rules", [])

    def validate(
        self,
        fields: MandatoryDeclarations,
        scraped_text: str,
        ocr_text: str,
        category: Optional[str] = None,
    ) -> tuple[int, list[Violation]]:
        """
        Validate product fields against category-specific rules.
        
        Args:
            fields: Extracted mandatory declarations
            scraped_text: Text from web scraping
            ocr_text: Text from OCR extraction
            category: Product category (food, electronics, cosmetics, or generic)
        
        Returns:
            Tuple of (compliance_score, list of violations)
        """
        score = 100
        violations: list[Violation] = []

        combined_text = f"{scraped_text}\n{ocr_text}".lower()
        
        # Auto-detect category if not provided
        if not category:
            category = self.detect_category(combined_text)
        else:
            category = category.lower()
        
        # Check for imported goods
        is_imported_goods = bool(re.search(r"\bimport(?:ed|er)?\b", combined_text))
        
        # Check for electrical appliance (for electronics category)
        is_appliance = bool(re.search(
            r"\b(refrigerator|fridge|washing\s*machine|air\s*conditioner|ac|fan|heater|iron|mixer|grinder|microwave)\b",
            combined_text
        ))
        
        # Get category-specific rules
        rules = self.get_rules_for_category(category)
        
        logger.info(f"Validating with category '{category}' - {len(rules)} rules")
        
        for rule in rules:
            field_name = rule["field"]
            field_value = getattr(fields, field_name, None)

            # Determine if field is required
            required_if_imported = rule.get("required_if_imported", False)
            required_if_appliance = rule.get("required_if_appliance", False)
            is_required = bool(rule.get("mandatory"))
            
            if required_if_imported and is_imported_goods:
                is_required = True
            if required_if_appliance and is_appliance:
                is_required = True

            if is_required and not field_value:
                penalty = int(rule.get("penalty", 0))
                score -= penalty
                violations.append(
                    Violation(
                        code=rule["code"],
                        field=field_name,
                        message=rule["message"],
                        penalty=penalty,
                    )
                )
        
        # Additional validation rules (new Legal Metrology rules)
        additional_violations = self._validate_additional_rules(fields, combined_text, is_imported_goods)
        for violation in additional_violations:
            score -= violation.penalty
            violations.append(violation)

        return max(score, 0), violations

    def _validate_additional_rules(
        self, 
        fields: MandatoryDeclarations,
        combined_text: str,
        is_imported: bool
    ) -> list[Violation]:
        """
        Validate additional Legal Metrology rules not covered by basic field checks.
        Includes: prohibited expressions, MRP format, unit validation, etc.
        """
        violations = []
        
        # Rule LM-AUD-007: Common/Generic Name Check
        common_name = getattr(fields, "common_generic_name", None)
        if not common_name:
            violations.append(Violation(
                code="LM-AUD-007",
                field="common_generic_name",
                message="Missing common or generic name of commodity.",
                penalty=15,
            ))
        
        # Rule LM-AUD-008: Manufacturer Address Check
        mfr_address = getattr(fields, "manufacturer_address", None)
        if not mfr_address:
            violations.append(Violation(
                code="LM-AUD-008",
                field="manufacturer_address",
                message="Missing complete manufacturer/packer address.",
                penalty=15,
            ))
        
        # Rule LM-AUD-009: Importer Address (if imported)
        if is_imported:
            importer_address = getattr(fields, "importer_address", None)
            if not importer_address:
                violations.append(Violation(
                    code="LM-AUD-009",
                    field="importer_address",
                    message="Missing importer name and address for imported goods.",
                    penalty=15,
                ))
        
        # Rule LM-AUD-010: Net Quantity Unit Validation
        unit_valid = getattr(fields, "net_quantity_unit_valid", None)
        if unit_valid is False:
            violations.append(Violation(
                code="LM-AUD-010",
                field="net_quantity_unit_valid",
                message="Net quantity not in standard SI units (g, kg, ml, L, cm, m).",
                penalty=10,
            ))
        
        # Rule LM-AUD-011: Net Quantity Prohibited Expressions
        prohibited = getattr(fields, "net_quantity_prohibited_expressions", None)
        if prohibited:
            violations.append(Violation(
                code="LM-AUD-011",
                field="net_quantity_no_approximation",
                message=f"Net quantity contains prohibited expressions: {', '.join(prohibited)}",
                penalty=15,
            ))
        
        # Rule LM-AUD-012: MRP Format Validation
        mrp = getattr(fields, "mrp_inclusive_of_taxes", None)
        if mrp:
            mrp_valid = self._validate_mrp_format(mrp)
            if not mrp_valid:
                violations.append(Violation(
                    code="LM-AUD-012",
                    field="mrp_format_valid",
                    message="MRP not in correct format 'MRP Rs. X (inclusive of all taxes)'.",
                    penalty=10,
                ))
        
        # Rule LM-AUD-013: Price Exceeding MRP Check
        price_violation = self._check_price_exceeds_mrp(combined_text, mrp)
        if price_violation:
            violations.append(Violation(
                code="LM-AUD-013",
                field="price_not_exceeding_mrp",
                message="Selling price appears to exceed printed MRP - violation of Rule 18.",
                penalty=25,
            ))
        
        return violations
    
    def _validate_mrp_format(self, mrp_text: str) -> bool:
        """
        Validate MRP format includes 'inclusive of all taxes'.
        """
        if not mrp_text:
            return False
        mrp_lower = mrp_text.lower()
        # Check if it mentions taxes
        if any(phrase in mrp_lower for phrase in ["incl", "inclusive", "all taxes", "taxes included"]):
            return True
        # If no tax mention but has a price, it's technically valid but incomplete
        return "₹" in mrp_text or "rs" in mrp_lower
    
    def _check_price_exceeds_mrp(self, combined_text: str, mrp_text: str) -> bool:
        """
        Check if selling price exceeds MRP.
        Returns True if violation detected.
        """
        if not mrp_text:
            return False
        
        # Extract MRP value
        mrp_match = re.search(r"([0-9,]+(?:\.[0-9]+)?)", mrp_text.replace(",", ""))
        if not mrp_match:
            return False
        
        try:
            mrp_value = float(mrp_match.group(1).replace(",", ""))
        except ValueError:
            return False
        
        # Extract selling price from text
        selling_price_match = re.search(
            r"(?:selling\s*price|sale\s*price|price|offer\s*price|our\s*price)\s*[:\-₹Rs\.]*\s*([0-9,]+(?:\.[0-9]+)?)",
            combined_text,
            re.IGNORECASE
        )
        
        if selling_price_match:
            try:
                selling_price = float(selling_price_match.group(1).replace(",", ""))
                if selling_price > mrp_value:
                    return True
            except ValueError:
                pass
        
        return False

    def get_category_summary(self, category: str) -> dict:
        """Get summary info about a category's rules"""
        rules = self.get_rules_for_category(category)
        
        mandatory_count = sum(1 for r in rules if r.get("mandatory"))
        max_penalty = sum(r.get("penalty", 0) for r in rules if r.get("mandatory"))
        
        return {
            "category": category,
            "total_rules": len(rules),
            "mandatory_rules": mandatory_count,
            "max_possible_penalty": max_penalty,
            "rules": [
                {
                    "code": r["code"],
                    "field": r["field"],
                    "mandatory": r.get("mandatory", False),
                    "penalty": r.get("penalty", 0)
                }
                for r in rules
            ]
        }
