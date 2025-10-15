"""
Action Suggester Agent - Suggests actions based on ticket analysis.
"""

from .agent import suggest_actions, parse_suggestions

# Backward compatibility aliases
action_suggester_agent = suggest_actions
parse_action_suggester_result = parse_suggestions

__all__ = [
    'suggest_actions',
    'parse_suggestions',
    # Backward compatibility
    'action_suggester_agent',
    'parse_action_suggester_result',
]
