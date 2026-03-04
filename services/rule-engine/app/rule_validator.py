"""
Rule Validator for validating rule definitions.
"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RuleValidator:
    """Validate compliance rule definitions."""
    
    VALID_RULE_TYPES = [
        'required_field',
        'format_validation',
        'range_check',
        'expiry_check',
        'pattern_match',
        'cross_field',
        'custom',
    ]
    
    VALID_SEVERITIES = ['critical', 'high', 'medium', 'low', 'info']
    
    VALID_STATUSES = ['active', 'inactive', 'deprecated', 'draft']
    
    VALID_OPERATORS = [
        'eq', 'ne', 'gt', 'lt', 'gte', 'lte',
        'contains', 'not_contains', 'regex', 'exists',
        'in', 'not_in', 'between',
        'length_eq', 'length_gt', 'length_lt',
        'is_expired', 'days_until_expiry',
    ]
    
    VALID_ACTION_TYPES = ['flag', 'warning', 'error', 'auto_fix', 'info']
    
    def validate_rule(self, rule: dict) -> dict:
        """
        Validate a rule definition.
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Required fields
        if not rule.get('name'):
            errors.append("Rule name is required")
        elif len(rule['name']) < 3:
            errors.append("Rule name must be at least 3 characters")
        elif len(rule['name']) > 100:
            errors.append("Rule name must not exceed 100 characters")
        
        if not rule.get('description'):
            errors.append("Rule description is required")
        elif len(rule['description']) < 10:
            errors.append("Rule description must be at least 10 characters")
        
        if not rule.get('rule_type'):
            errors.append("Rule type is required")
        elif rule['rule_type'] not in self.VALID_RULE_TYPES:
            errors.append(f"Invalid rule type. Valid types: {self.VALID_RULE_TYPES}")
        
        if not rule.get('category'):
            errors.append("Category is required")
        
        # Validate severity
        if rule.get('severity') and rule['severity'] not in self.VALID_SEVERITIES:
            errors.append(f"Invalid severity. Valid values: {self.VALID_SEVERITIES}")
        
        # Validate status
        if rule.get('status') and rule['status'] not in self.VALID_STATUSES:
            errors.append(f"Invalid status. Valid values: {self.VALID_STATUSES}")
        
        # Validate conditions
        conditions = rule.get('conditions', [])
        if not conditions:
            errors.append("At least one condition is required")
        else:
            for i, condition in enumerate(conditions):
                cond_errors = self._validate_condition(condition, i)
                errors.extend(cond_errors)
        
        # Validate actions
        actions = rule.get('actions', [])
        if not actions:
            errors.append("At least one action is required")
        else:
            for i, action in enumerate(actions):
                action_errors = self._validate_action(action, i)
                errors.extend(action_errors)
        
        # Validate tags
        tags = rule.get('tags', [])
        if tags:
            for tag in tags:
                if not isinstance(tag, str) or len(tag) < 2:
                    errors.append(f"Invalid tag: {tag}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }
    
    def _validate_condition(self, condition: dict, index: int) -> list[str]:
        """Validate a single condition."""
        errors = []
        prefix = f"Condition {index + 1}"
        
        if not condition.get('field'):
            errors.append(f"{prefix}: Field is required")
        
        operator = condition.get('operator')
        if not operator:
            errors.append(f"{prefix}: Operator is required")
        elif operator not in self.VALID_OPERATORS:
            errors.append(f"{prefix}: Invalid operator '{operator}'. Valid: {self.VALID_OPERATORS}")
        
        # Validate operator-specific requirements
        if operator in ['exists']:
            if condition.get('value') not in [True, False]:
                errors.append(f"{prefix}: 'exists' operator requires boolean value")
        
        if operator in ['regex']:
            pattern = condition.get('value')
            if pattern:
                try:
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"{prefix}: Invalid regex pattern: {e}")
        
        if operator in ['between']:
            value = condition.get('value')
            if not isinstance(value, list) or len(value) != 2:
                errors.append(f"{prefix}: 'between' requires list of [min, max]")
        
        if operator in ['in', 'not_in']:
            value = condition.get('value')
            if not isinstance(value, list):
                errors.append(f"{prefix}: 'in/not_in' requires a list value")
        
        return errors
    
    def _validate_action(self, action: dict, index: int) -> list[str]:
        """Validate a single action."""
        errors = []
        prefix = f"Action {index + 1}"
        
        action_type = action.get('type')
        if not action_type:
            errors.append(f"{prefix}: Action type is required")
        elif action_type not in self.VALID_ACTION_TYPES:
            errors.append(f"{prefix}: Invalid action type '{action_type}'. Valid: {self.VALID_ACTION_TYPES}")
        
        if not action.get('message'):
            errors.append(f"{prefix}: Action message is required")
        
        # auto_fix requires fix_value
        if action_type == 'auto_fix' and not action.get('fix_value'):
            errors.append(f"{prefix}: auto_fix action requires fix_value")
        
        return errors
    
    def validate_condition_value_type(
        self, 
        operator: str, 
        value: Any
    ) -> bool:
        """Check if value type is valid for operator."""
        if operator in ['eq', 'ne']:
            return True  # Any type allowed
        
        if operator in ['gt', 'lt', 'gte', 'lte']:
            try:
                float(value)
                return True
            except (TypeError, ValueError):
                return False
        
        if operator in ['contains', 'not_contains', 'regex']:
            return isinstance(value, str)
        
        if operator in ['exists']:
            return isinstance(value, bool)
        
        if operator in ['in', 'not_in']:
            return isinstance(value, list)
        
        if operator in ['between']:
            return isinstance(value, list) and len(value) == 2
        
        if operator in ['length_eq', 'length_gt', 'length_lt']:
            try:
                int(value)
                return True
            except (TypeError, ValueError):
                return False
        
        return True
    
    def get_validation_schema(self) -> dict:
        """Get the validation schema for documentation."""
        return {
            'rule_types': self.VALID_RULE_TYPES,
            'severities': self.VALID_SEVERITIES,
            'statuses': self.VALID_STATUSES,
            'operators': self.VALID_OPERATORS,
            'action_types': self.VALID_ACTION_TYPES,
            'required_fields': ['name', 'description', 'rule_type', 'category', 'conditions', 'actions'],
        }
