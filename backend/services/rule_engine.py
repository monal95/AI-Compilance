import json
from pathlib import Path

from backend.models import ExtractedFields, Violation


class RuleEngine:
    def __init__(self, rules_path: str = "backend/legal_rules/rules.json") -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        with self.rules_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate(self, extracted: ExtractedFields) -> tuple[int, list[Violation]]:
        score = 100
        violations: list[Violation] = []

        for rule in self.rules.get("rules", []):
            field_name = rule["field"]
            field_value = getattr(extracted, field_name, None)
            if rule.get("mandatory") and not field_value:
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

        return max(score, 0), violations
