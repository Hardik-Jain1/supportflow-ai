"""
Triage Agent - Classifies customer support tickets by category and urgency.
"""

from .agent import classify_ticket, parse_classification

# Backward compatibility aliases
triage_agent = classify_ticket
parse_triage_result = parse_classification

__all__ = [
    'classify_ticket',
    'parse_classification',
    # Backward compatibility
    'triage_agent',
    'parse_triage_result',
]
