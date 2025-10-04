from flows.state.ticket_state import TicketState, KBHit, KBResult
import asyncio
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from utils.config import config
import json

async def kb_retrieve(state: TicketState) -> TicketState:
    input_data = json.dumps({
        "ticket_text": state.ticket_text,
        "category": state.category
    })
    async with Client(base_url="http://localhost:8001") as client:
        run = await client.run_sync(
            agent="kb_agent",
            input=[
                Message(
                    parts=[MessagePart(content=input_data, content_type="text/plain")]
                )
            ],
        )
        agent_2_output_json = json.loads(run.output[0].parts[0].content)

    if agent_2_output_json:
        # Convert parsed sources to KBHit objects
        kb_hits = []
        for source in agent_2_output_json.get("sources", []):
            kb_hits.append(KBHit(
                retriever=source.get("retriever", ""),
                summary=source.get("summary", "")
            ))
        
        state.kb_result = KBResult(
            retrieved_sources=kb_hits,
            consolidated_context=agent_2_output_json.get("consolidated_context", "")
        )
        print(f"KB Agent: retrieved {len(state.kb_result.retrieved_sources)} sources")
    return state

