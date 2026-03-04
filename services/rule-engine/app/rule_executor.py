"""
Rule Executor for processing compliance rules against data.
"""
import re
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RuleExecutor:
    """Execute compliance rules against product data."""
    
    def __init__(self):
        self.operators = {
            'eq': self._op_equals,
            'ne': self._op_not_equals,
            'gt': self._op_greater_than,
            'lt': self._op_less_than,
            'gte': self._op_greater_than_equals,
            'lte': self._op_less_than_equals,
            'contains': self._op_contains,
            'not_contains': self._op_not_contains,
            'regex': self._op_regex,
            'exists': self._op_exists,
            'in': self._op_in,
            'not_in': self._op_not_in,
            'between': self._op_between,
            'length_eq': self._op_length_equals,
            'length_gt': self._op_length_greater,
            'length_lt': self._op_length_less,
            'is_expired': self._op_is_expired,
            'days_until_expiry': self._op_days_until_expiry,
        }
    
    def execute(self, rule: dict, data: dict) -> dict:
        """
        Execute a single rule against data.
        
        Returns:
            Dict with status, rule_id, messages, details
        """
        rule_id = rule.get('id', 'unknown')
        rule_name = rule.get('name', 'Unknown Rule')
        
        try:
            # Evaluate all conditions
            conditions = rule.get('conditions', [])
            condition_results = []
            all_passed = True
            
            for condition in conditions:
                result = self._evaluate_condition(condition, data)
                condition_results.append(result)
                if not result['passed']:
                    all_passed = False
            
            # Determine overall status
            if all_passed:
                status = 'passed'
                messages = []
            else:
                severity = rule.get('severity', 'medium')
                if severity in ['critical', 'high']:
                    status = 'failed'
                else:
                    status = 'warning'
                
                # Get action messages
                actions = rule.get('actions', [])
                messages = [a.get('message', 'Rule violation') for a in actions]
            
            return {
                'rule_id': rule_id,
                'rule_name': rule_name,
                'status': status,
                'passed': all_passed,
                'severity': rule.get('severity', 'medium'),
                'category': rule.get('category', 'general'),
                'messages': messages,
                'condition_results': condition_results,
            }
        
        except Exception as e:
            logger.error(f"Rule execution error for {rule_id}: {e}")
            return {
                'rule_id': rule_id,
                'rule_name': rule_name,
                'status': 'error',
                'passed': False,
                'error': str(e),
            }
    
    def _evaluate_condition(self, condition: dict, data: dict) -> dict:
        """Evaluate a single condition."""
        field = condition.get('field')
        operator = condition.get('operator')
        expected_value = condition.get('value')
        value_field = condition.get('value_field')  # For cross-field
        
        # Get actual value from data
        actual_value = self._get_nested_value(data, field)
        
        # Handle cross-field comparison
        if value_field:
            expected_value = self._get_nested_value(data, value_field)
        
        # Get operator function
        op_func = self.operators.get(operator)
        if not op_func:
            return {
                'field': field,
                'passed': False,
                'error': f'Unknown operator: {operator}',
            }
        
        # Execute operator
        try:
            passed = op_func(actual_value, expected_value)
            return {
                'field': field,
                'operator': operator,
                'expected': expected_value,
                'actual': actual_value,
                'passed': passed,
            }
        except Exception as e:
            return {
                'field': field,
                'passed': False,
                'error': str(e),
            }
    
    def _get_nested_value(self, data: dict, field: str) -> Any:
        """Get value from nested dict using dot notation."""
        if not field:
            return None
        
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                idx = int(key)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        
        return value
    
    # Operator implementations
    def _op_equals(self, actual: Any, expected: Any) -> bool:
        return actual == expected
    
    def _op_not_equals(self, actual: Any, expected: Any) -> bool:
        return actual != expected
    
    def _op_greater_than(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return float(actual) > float(expected)
    
    def _op_less_than(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return float(actual) < float(expected)
    
    def _op_greater_than_equals(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return float(actual) >= float(expected)
    
    def _op_less_than_equals(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return float(actual) <= float(expected)
    
    def _op_contains(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return str(expected).lower() in str(actual).lower()
    
    def _op_not_contains(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return True
        return str(expected).lower() not in str(actual).lower()
    
    def _op_regex(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return bool(re.search(str(expected), str(actual), re.IGNORECASE))
    
    def _op_exists(self, actual: Any, expected: Any) -> bool:
        exists = actual is not None and actual != '' and actual != []
        return exists == expected
    
    def _op_in(self, actual: Any, expected: Any) -> bool:
        if not isinstance(expected, list):
            expected = [expected]
        return actual in expected
    
    def _op_not_in(self, actual: Any, expected: Any) -> bool:
        if not isinstance(expected, list):
            expected = [expected]
        return actual not in expected
    
    def _op_between(self, actual: Any, expected: Any) -> bool:
        if actual is None or not isinstance(expected, list) or len(expected) != 2:
            return False
        return float(expected[0]) <= float(actual) <= float(expected[1])
    
    def _op_length_equals(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return len(str(actual)) == int(expected)
    
    def _op_length_greater(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return len(str(actual)) > int(expected)
    
    def _op_length_less(self, actual: Any, expected: Any) -> bool:
        if actual is None:
            return False
        return len(str(actual)) < int(expected)
    
    def _op_is_expired(self, actual: Any, expected: Any) -> bool:
        """Check if date is expired."""
        if actual is None:
            return not expected  # If expecting expired=True and no date, return False
        
        try:
            if isinstance(actual, str):
                # Try to parse date
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        actual = datetime.strptime(actual, fmt)
                        break
                    except ValueError:
                        continue
            
            if isinstance(actual, datetime):
                is_expired = actual < datetime.now()
                return is_expired == expected
        except Exception:
            pass
        
        return False
    
    def _op_days_until_expiry(self, actual: Any, expected: Any) -> bool:
        """Check days until expiry (for near-expiry warnings)."""
        if actual is None:
            return False
        
        try:
            if isinstance(actual, str):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        actual = datetime.strptime(actual, fmt)
                        break
                    except ValueError:
                        continue
            
            if isinstance(actual, datetime):
                days = (actual - datetime.now()).days
                return days <= int(expected)
        except Exception:
            pass
        
        return False
    
    def execute_batch(self, rules: list[dict], data: dict) -> list[dict]:
        """Execute multiple rules against data."""
        return [self.execute(rule, data) for rule in rules]
    
    def get_supported_operators(self) -> list[str]:
        """Get list of supported operators."""
        return list(self.operators.keys())
