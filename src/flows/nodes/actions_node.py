from flows.state.ticket_state import TicketState,  ActionProposal
from typing import List
from agents.action_suggester_agent import action_suggester_agent, parse_action_suggester_result
from utils.helpers import get_narrative_context
from utils.config import config

def suggest_actions(state: TicketState) -> TicketState:
    proposals: List[ActionProposal] = []

    agent4_inputs = {
        "ticket_text": state.ticket_text,
        "category": state.category,
        "urgency": state.urgency,
        "narrative_context": get_narrative_context(state.kb_result)
    }
    agent4_output = action_suggester_agent(agent4_inputs, model=config.action_suggester_model)
    agent4_output_json = parse_action_suggester_result(agent4_output)

    if agent4_output_json:
        for action_item in agent4_output_json:
            proposals.append(ActionProposal(
                action=action_item.get("name", ""),
                params=action_item.get("arguments", {}),
                rationale=f"Suggested by action agent based on ticket analysis",
                approved=None
            ))

    # Auto-approval policy for non-risky actions when high confidence
    if config.enable_auto_approval:
        for p in proposals:
            if p.action in config.non_risky_autosafe and (state.category_conf >= config.auto_approval_confidence_threshold and state.reply_conf >= config.auto_approval_confidence_threshold):
                p.approved = True

    state.actions = proposals
    print(f"Action Suggester Agent: proposed {len(state.actions)} actions")
    return state