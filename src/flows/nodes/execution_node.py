from flows.state.ticket_state import TicketState
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from utils.config import config
import json
from datetime import datetime

async def execute_actions(state: TicketState) -> TicketState:
    if not state.actions:
        print("No actions to execute")
        return state

    actions = []
    for a in state.actions:
        if a.approved is True:
            actions.append({
                "name": a.action,
                "arguments": a.params
            })
    
    if not actions:
        print("No approved actions to execute")
        return state
    
    input_data = json.dumps({
        "actions": actions
    })
    print(f"===\nSending to action_executor_agent:\n{input_data}\n===")

    async with Client(base_url="http://localhost:8001") as client:
        run = await client.run_sync(
            agent="action_executor_agent",
            input=[
                Message(
                    parts=[MessagePart(content=input_data, content_type="text/plain")]
                )
            ],
        )
        agent_5_output = run.output[0].parts[0].content

    print("\n" + "="*config.action_separator_length)
    print("ACTION EXECUTION RESULTS\n")
    print(agent_5_output)
    print("="*config.action_separator_length + "\n")

    return state

async def post_or_escalate(state: TicketState) -> TicketState:
    if "create_support_ticket" in [a.action for a in state.actions if a.approved]:
        state.escalated = True
        state.posted = False
        return state
    state.posted = True
    return state

async def finalize(state: TicketState) -> TicketState:
    print(f"Ticket processing completed at {datetime.now()}")
    print(f"Final state: Posted={state.posted}, Escalated={state.escalated}")
    print(f"Total retries: {sum(state.retries.values())}")
    if state.errors:
        print(f"Errors encountered: {len(state.errors)}")
    return state