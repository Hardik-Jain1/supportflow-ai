"""
Knowledge Base Agent - Retrieves relevant information from knowledge base.
"""

from .agent import (
    build_retrievers,
    create_kb_agent,
    parse_kb_output,
    parse_kb_output_text,
    get_qdrant_client,
    close_qdrant_client,
)

# Backward compatibility aliases
build_retrievers_from_csvs = build_retrievers
build_agent = create_kb_agent
parse_agent2_output_json = parse_kb_output
parse_agent2_output_text = parse_kb_output_text

__all__ = [
    'build_retrievers',
    'create_kb_agent',
    'parse_kb_output',
    'parse_kb_output_text',
    'get_qdrant_client',
    'close_qdrant_client',
    # Backward compatibility
    'build_retrievers_from_csvs',
    'build_agent',
    'parse_agent2_output_json',
    'parse_agent2_output_text',
]
