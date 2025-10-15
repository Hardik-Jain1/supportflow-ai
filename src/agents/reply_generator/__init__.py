"""
Reply Generator Agent - Generates customer support replies using CrewAI.
"""

from .agent import generate_reply, redraft_reply, ReplyGeneratorCrew

# Backward compatibility aliases
reply_agent = generate_reply
redraft_reply_agent = redraft_reply
ReplyAgentCrew = ReplyGeneratorCrew

__all__ = [
    'generate_reply',
    'redraft_reply',
    'ReplyGeneratorCrew',
    # Backward compatibility
    'reply_agent',
    'redraft_reply_agent',
    'ReplyAgentCrew',
]
