from flows.state.ticket_state import TicketState
from agents.action_executor_agent import action_executor_agent
from utils.config import config
from datetime import datetime

def execute_actions(state: TicketState) -> TicketState:
    if not state.actions:
        return state

    actions = []
    for a in state.actions:
        if a.approved is True:
            actions.append({
                "name": a.action,
                "arguments": a.params
            })
    agent5_output = action_executor_agent(actions)

    print("\n" + "="*config.action_separator_length)
    print("ACTION EXECUTION RESULTS\n")
    print(agent5_output)
    print("="*config.action_separator_length + "\n")

    return state

def post_or_escalate(state: TicketState) -> TicketState:
    if "create_support_ticket" in [a.action for a in state.actions if a.approved]:
        state.escalated = True
        state.posted = False
        return state
    state.posted = True
    return state

def finalize(state: TicketState) -> TicketState:
    print(f"Ticket processing completed at {datetime.now()}")
    print(f"Final state: Posted={state.posted}, Escalated={state.escalated}")
    print(f"Total retries: {sum(state.retries.values())}")
    if state.errors:
        print(f"Errors encountered: {len(state.errors)}")
    return state