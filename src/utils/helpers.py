from flows.state.ticket_state import TicketState, KBHit, KBResult
from utils.config import config


def incr_retry(state: TicketState, key: str) -> int:
    state.retries[key] = state.retries.get(key, 0) + 1
    return state.retries[key]

def mcp_safe_call(tool_name: str, fn, state: TicketState, *args, **kwargs):
    """Minimal retry wrapper for MCP/tool calls.
    Replace `fn` with actual adapter (e.g., tools.ticketing.post_comment).
    """
    key = f"tool:{tool_name}"
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        count = incr_retry(state, key)
        state.errors.append(f"{key} error: {e}")
        if count <= config.max_retries:
            return fn(*args, **kwargs)
        raise

def get_narrative_context(kb_result: KBResult) -> str:
    if kb_result.retrieved_sources:
        narrative_parts = []
        narrative_parts.append("Relevant Knowledge:")
        
        for hit in kb_result.retrieved_sources:
            summary_clean = " ".join(hit.summary.split())
            narrative_parts.append(f"- {summary_clean} [{hit.retriever}]")
        
        narrative_parts.append("\nConsolidated Summary:")
        narrative_parts.append(kb_result.consolidated_context)
        
        narrative_context = "\n".join(narrative_parts)
    else:
        narrative_context = "No relevant knowledge found."
    return narrative_context