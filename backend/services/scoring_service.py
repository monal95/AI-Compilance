"""
Legal Metrology Compliance Scoring Service
Implements score-based risk assessment per The Legal Metrology (Packaged Commodities) Rules, 2011
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class Violation:
    """Represents a compliance violation"""
    code: str
    category: str  # A, B, C, D
    description: str
    points_deducted: int
    field: str


@dataclass
class ScoringResult:
    """Compliance scoring result"""
    compliance_score: float
    risk_level: str
    risk_indicator: str
    violations: List[Dict] = field(default_factory=list)
    category_a_violations: List[Dict] = field(default_factory=list)
    category_b_violations: List[Dict] = field(default_factory=list)
    category_c_violations: List[Dict] = field(default_factory=list)
    category_d_violations: List[Dict] = field(default_factory=list)
    penalty_risk: str = ""
    action_required: str = ""
    total_deductions: int = 0


class ComplianceScoringService:
    """Manages Legal Metrology compliance scoring"""

    # Scoring configuration
    BASE_SCORE = 100
    MIN_SCORE = 0
    MAX_SCORE_WITH_CATEGORY_A = 60

    # Category deductions
    CATEGORY_DEDUCTIONS = {
        "A": 25,  # Prohibited Practices
        "B": 20,  # Missing Mandatory Declarations
        "C": 10,  # Format / Declaration Errors
        "D": 5,   # Minor Technical Issues
    }

    # Risk level mapping - score-based only
    RISK_LEVELS = {
        "90-100": {
            "level": "Fully Compliant",
            "indicator": "✅",
            "penalty_risk": "None",
            "action": "No action required",
        },
        "70-89": {
            "level": "Minor Risk",
            "indicator": "⚠️",
            "penalty_risk": "Low",
            "action": "Address minor issues within 30 days",
        },
        "50-69": {
            "level": "Moderate Legal Risk",
            "indicator": "⚠️⚠️",
            "penalty_risk": "Moderate - Possible fine Rs. 2000-5000",
            "action": "Mandatory correction required within 15 days",
        },
        "0-49": {
            "level": "High Penalty Risk",
            "indicator": "❌",
            "penalty_risk": "High - Possible fine Rs. 5000+ or imprisonment",
            "action": "Immediate removal from sale, product detention required",
        },
    }

    @staticmethod
    def calculate_compliance_score(violations: List[Dict]) -> ScoringResult:
        """
        Calculate compliance score based on violations found

        Args:
            violations: List of violation dictionaries with keys:
                - category: "A", "B", "C", or "D"
                - code: violation code
                - description: violation description
                - field: field name that violated

        Returns:
            ScoringResult with score, risk level, and detailed violation breakdown
        """
        score = ComplianceScoringService.BASE_SCORE
        result = ScoringResult(
            compliance_score=score,
            risk_level="",
            risk_indicator="",
        )

        # Categorize violations
        category_violations = {
            "A": [],
            "B": [],
            "C": [],
            "D": [],
        }

        for violation in violations:
            category = violation.get("category", "D").upper()
            if category not in category_violations:
                category = "D"

            violation_entry = {
                "code": violation.get("code", "UNKNOWN"),
                "description": violation.get("description", "Unknown violation"),
                "field": violation.get("field", ""),
                "points_deducted": ComplianceScoringService.CATEGORY_DEDUCTIONS[category],
            }

            category_violations[category].append(violation_entry)

        # Store categorized violations in result
        result.category_a_violations = category_violations["A"]
        result.category_b_violations = category_violations["B"]
        result.category_c_violations = category_violations["C"]
        result.category_d_violations = category_violations["D"]

        # Calculate total deductions
        total_deductions = 0

        # Category A: 25 points each + cap score at 60
        has_category_a = len(category_violations["A"]) > 0
        for violation in category_violations["A"]:
            deduction = ComplianceScoringService.CATEGORY_DEDUCTIONS["A"]
            total_deductions += deduction

        # Category B: 20 points each
        for violation in category_violations["B"]:
            deduction = ComplianceScoringService.CATEGORY_DEDUCTIONS["B"]
            total_deductions += deduction

        # Category C: 10 points each
        for violation in category_violations["C"]:
            deduction = ComplianceScoringService.CATEGORY_DEDUCTIONS["C"]
            total_deductions += deduction

        # Category D: 5 points each
        for violation in category_violations["D"]:
            deduction = ComplianceScoringService.CATEGORY_DEDUCTIONS["D"]
            total_deductions += deduction

        # Calculate final score
        final_score = max(
            ComplianceScoringService.MIN_SCORE,
            ComplianceScoringService.BASE_SCORE - total_deductions,
        )

        # Apply cap if Category A violation exists
        if has_category_a:
            final_score = min(
                final_score, ComplianceScoringService.MAX_SCORE_WITH_CATEGORY_A
            )

        # Determine risk level based solely on score
        risk_info = ComplianceScoringService._get_risk_level(final_score)

        # Update result
        result.compliance_score = final_score
        result.risk_level = risk_info["level"]
        result.risk_indicator = risk_info["indicator"]
        result.penalty_risk = risk_info["penalty_risk"]
        result.action_required = risk_info["action"]
        result.total_deductions = total_deductions

        # Combine all violations for summary
        result.violations = (
            category_violations["A"]
            + category_violations["B"]
            + category_violations["C"]
            + category_violations["D"]
        )

        return result

    @staticmethod
    def _get_risk_level(score: float) -> Dict[str, str]:
        """
        Determine risk level based solely on compliance score

        Args:
            score: Compliance score (0-100)

        Returns:
            Dictionary with risk level information
        """
        if score >= 90:
            return ComplianceScoringService.RISK_LEVELS["90-100"]
        elif score >= 70:
            return ComplianceScoringService.RISK_LEVELS["70-89"]
        elif score >= 50:
            return ComplianceScoringService.RISK_LEVELS["50-69"]
        else:
            return ComplianceScoringService.RISK_LEVELS["0-49"]

    @staticmethod
    def validate_product_compliance(product_data: Dict) -> ScoringResult:
        """
        Validate product data and calculate compliance score

        Args:
            product_data: Product information dictionary

        Returns:
            ScoringResult with compliance assessment
        """
        violations = []

        # Check Category A violations
        if product_data.get("price_exceeds_mrp"):
            violations.append(
                {
                    "category": "A",
                    "code": "LM-SCORE-A002",
                    "description": "Selling price exceeds printed MRP - violation of Rule 18",
                    "field": "price_not_exceeding_mrp",
                }
            )

        if product_data.get("misleading_quantity_words"):
            violations.append(
                {
                    "category": "A",
                    "code": "LM-SCORE-A001",
                    "description": "Using misleading words in quantity declaration",
                    "field": "net_quantity_no_approximation",
                }
            )

        # Check Category B violations (mandatory declarations)
        if not product_data.get("mrp_inclusive_of_taxes"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B001",
                    "description": "Missing MRP (inclusive of all taxes)",
                    "field": "mrp_inclusive_of_taxes",
                }
            )

        if not product_data.get("net_quantity"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B002",
                    "description": "Missing Net Quantity",
                    "field": "net_quantity",
                }
            )

        if not product_data.get("manufacturer_name"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B003",
                    "description": "Missing Manufacturer/Packer/Importer Name & Address",
                    "field": "manufacturer_or_importer",
                }
            )

        if not product_data.get("date_of_manufacture"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B004",
                    "description": "Missing Month & Year of Manufacture/Packing/Import",
                    "field": "date_of_manufacture_or_import",
                }
            )

        if not product_data.get("consumer_care"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B005",
                    "description": "Missing Customer Care Details",
                    "field": "consumer_care_information",
                }
            )

        if product_data.get("is_imported") and not product_data.get("country_of_origin"):
            violations.append(
                {
                    "category": "B",
                    "code": "LM-SCORE-B006",
                    "description": "Missing Country of Origin (if imported)",
                    "field": "country_of_origin",
                }
            )

        # Check Category C violations (format/declaration errors)
        if not product_data.get("valid_si_units"):
            violations.append(
                {
                    "category": "C",
                    "code": "LM-SCORE-C001",
                    "description": "Incorrect SI unit usage in quantity",
                    "field": "net_quantity_unit_valid",
                }
            )

        if product_data.get("incorrect_font_size"):
            violations.append(
                {
                    "category": "C",
                    "code": "LM-SCORE-C002",
                    "description": "Incorrect font size or visibility",
                    "field": "font_size_visibility",
                }
            )

        if not product_data.get("declaration_on_pdp"):
            violations.append(
                {
                    "category": "C",
                    "code": "LM-SCORE-C003",
                    "description": "Declaration not on Principal Display Panel",
                    "field": "declaration_on_pdp",
                }
            )

        if product_data.get("improper_mrp_format"):
            violations.append(
                {
                    "category": "C",
                    "code": "LM-SCORE-C004",
                    "description": "Improper MRP format",
                    "field": "mrp_format_valid",
                }
            )

        # Check Category D violations (minor issues)
        if product_data.get("spacing_alignment_issues"):
            violations.append(
                {
                    "category": "D",
                    "code": "LM-SCORE-D001",
                    "description": "Spacing/alignment issues in declarations",
                    "field": "spacing_alignment",
                }
            )

        if product_data.get("formatting_inconsistencies"):
            violations.append(
                {
                    "category": "D",
                    "code": "LM-SCORE-D002",
                    "description": "Minor formatting inconsistencies",
                    "field": "formatting_consistency",
                }
            )

        return ComplianceScoringService.calculate_compliance_score(violations)

    @staticmethod
    def get_risk_summary(scoring_result: ScoringResult) -> Dict:
        """
        Generate a comprehensive risk summary

        Args:
            scoring_result: ScoringResult object

        Returns:
            Dictionary with risk assessment and recommendations
        """
        return {
            "compliance_score": scoring_result.compliance_score,
            "risk_level": scoring_result.risk_level,
            "risk_indicator": scoring_result.risk_indicator,
            "penalty_risk": scoring_result.penalty_risk,
            "action_required": scoring_result.action_required,
            "violations_summary": {
                "category_a_count": len(scoring_result.category_a_violations),
                "category_b_count": len(scoring_result.category_b_violations),
                "category_c_count": len(scoring_result.category_c_violations),
                "category_d_count": len(scoring_result.category_d_violations),
                "total_violations": len(scoring_result.violations),
            },
            "violations_by_category": {
                "category_a_prohibited_practices": scoring_result.category_a_violations,
                "category_b_missing_declarations": scoring_result.category_b_violations,
                "category_c_format_errors": scoring_result.category_c_violations,
                "category_d_minor_issues": scoring_result.category_d_violations,
            },
            "total_points_deducted": scoring_result.total_deductions,
        }
