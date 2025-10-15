"""
Action Executor Agent - Executes approved actions via MCP tools.
"""

from .agent import execute_actions

# Backward compatibility alias
action_executor_agent = execute_actions

__all__ = [
    'execute_actions',
    # Backward compatibility
    'action_executor_agent',
]
