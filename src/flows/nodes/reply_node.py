from flows.state.ticket_state import TicketState
from agents.reply_agent.crew import reply_agent, redraft_reply_agent
from utils.helpers import get_narrative_context
from utils.config import config

def draft_reply(state: TicketState) -> TicketState:
    agent3_context = get_narrative_context(state.kb_result)
    
    if state.human_feedback and state.redraft_count < config.max_redrafts:
        # Redraft based on human feedback using the enhanced crew
        agent3_output = redraft_reply_agent(
            ticket=state.ticket_text,
            context=agent3_context,
            previous_draft=state.reply_draft,
            human_feedback=state.human_feedback,
            model=config.reply_model
        )
        state.redraft_count += 1
        print(f"Reply Agent: redrafting based on human feedback (redraft count {state.redraft_count})")
        
        # Clear feedback after processing
        state.human_feedback = None
    else:
        # Initial draft using existing workflow
        agent3_output = reply_agent(state.ticket_text, agent3_context, model=config.reply_model)
        print(f"Reply Agent: initial draft reply of length {len(agent3_output.raw)}")
    
    state.reply_draft = agent3_output.raw
    return state