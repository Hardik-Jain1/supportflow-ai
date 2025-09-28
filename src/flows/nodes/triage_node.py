from flows.state.ticket_state import TicketState
from agents.triage_agent import triage_agent, parse_triage_result
from utils.config import config

def triage_classifier(state: TicketState) -> TicketState:
    agent1_output = triage_agent(state.ticket_text, model=config.triage_model)
    agent1_output_json = parse_triage_result(agent1_output.choices[0].message.content)
    if agent1_output_json:
        cat_id = agent1_output_json.get("category").strip()
        state.category = config.category_mapping.get(cat_id)
        state.category_conf = float(agent1_output_json.get("confidence_for_category", "0.0").strip())

        urg_id = agent1_output_json.get("urgency").strip()
        state.urgency = config.urgency_mapping.get(urg_id)
        state.urgency_conf = float(agent1_output_json.get("confidence_for_urgency_level", "0.0").strip())

        print(f"Triage Agent: category={state.category} ({state.category_conf:.{config.display_confidence_decimals}f}), urgency={state.urgency} ({state.urgency_conf:.{config.display_confidence_decimals}f})")
    return state