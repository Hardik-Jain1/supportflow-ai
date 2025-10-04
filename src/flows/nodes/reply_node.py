from flows.state.ticket_state import TicketState
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from utils.helpers import get_narrative_context
from utils.config import config
import json

async def draft_reply(state: TicketState) -> TicketState:
    async def _run_reply_agent(input_data: str) -> str:
        async with Client(base_url="http://localhost:8001") as client:
            run = await client.run_sync(
                agent="reply_agent",
                input=[
                    Message(
                        parts=[MessagePart(content=input_data, content_type="text/plain")]
                    )
                ],
            )
            return run.output[0].parts[0].content
         
    if state.human_feedback and state.redraft_count < config.max_redrafts:
        input_data = json.dumps({
            "ticket_text": state.ticket_text,
            "context": get_narrative_context(state.kb_result),
            "reply_draft": state.reply_draft,
            "human_feedback": state.human_feedback,
            "model": config.reply_model
        })
        agent_3_output = await _run_reply_agent(input_data)
        state.redraft_count += 1
        print(f"Reply Agent: redrafting based on human feedback (redraft count {state.redraft_count})")
        state.human_feedback = None
    else:
        input_data = json.dumps({
            "ticket_text": state.ticket_text,
            "context": get_narrative_context(state.kb_result),
            "model": config.reply_model
        })
        agent_3_output = await _run_reply_agent(input_data)
        print(f"Reply Agent: initial draft reply of length {len(agent_3_output)}")
    
    state.reply_draft = agent_3_output
    return state