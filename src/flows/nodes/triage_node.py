from flows.state.ticket_state import TicketState
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from utils.config import config
import json

async def triage_classifier(state: TicketState) -> TicketState:
    input_data = json.dumps({
        "ticket_text": state.ticket_text,
        "model": config.triage_model
    })
    async with Client(base_url="http://localhost:8001") as client:
        run = await client.run_sync(
            agent="triage_agent",
            input=[
                Message(
                    parts=[MessagePart(content=input_data, content_type="text/plain")]
                )
            ],
        )
        agent_1_output_json = json.loads(run.output[0].parts[0].content)

    if agent_1_output_json:
        cat_id = agent_1_output_json.get("category").strip()
        state.category = config.category_mapping.get(cat_id)
        state.category_conf = float(agent_1_output_json.get("confidence_for_category", "0.0").strip())

        urg_id = agent_1_output_json.get("urgency").strip()
        state.urgency = config.urgency_mapping.get(urg_id)
        state.urgency_conf = float(agent_1_output_json.get("confidence_for_urgency_level", "0.0").strip())

        print(f"Triage Agent: category={state.category} ({state.category_conf:.{config.display_confidence_decimals}f}), urgency={state.urgency} ({state.urgency_conf:.{config.display_confidence_decimals}f})")
    return state