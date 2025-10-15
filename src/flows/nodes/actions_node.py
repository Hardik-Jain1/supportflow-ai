from flows.state.ticket_state import TicketState,  ActionProposal
from typing import List
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from utils.helpers import get_narrative_context
from utils.config import config
import json

async def suggest_actions(state: TicketState) -> TicketState:
    if state.actions:
        print("Action Suggester Agent: actions already proposed, skipping")
        return state 

    proposals: List[ActionProposal] = []

    input_data = json.dumps({
        "ticket_text": state.ticket_text,
        "category": state.category,
        "urgency": state.urgency,
        "narrative_context": get_narrative_context(state.kb_result),
    })
    async with Client(base_url="http://localhost:8001") as client:
        run = await client.run_sync(
            agent="action_suggester_agent",
            input=[
                Message(
                    parts=[MessagePart(content=input_data, content_type="text/plain")]
                )
            ],
        )
        agent_4_output_json = json.loads(run.output[0].parts[0].content)

    if agent_4_output_json:
        for action_item in agent_4_output_json:
            proposals.append(ActionProposal(
                action=action_item.get("name", ""),
                params=action_item.get("arguments", {}),
                rationale=action_item.get("reasoning", ""),
                approved=None
            ))

    # Auto-approval policy for non-risky actions when high confidence
    if config.enable_auto_approval:
        for p in proposals:
            if p.action in config.non_risky_autosafe and state.category_conf >= config.auto_approval_confidence_threshold: # and state.reply_conf >= config.auto_approval_confidence_threshold
                p.approved = True

    state.actions = proposals
    print(f"Action Suggester Agent: proposed {len(state.actions)} actions")
    return state