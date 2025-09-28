from flows.state.ticket_state import TicketState, KBHit, KBResult
from agents.kb_agent import build_retrievers_from_csvs, build_agent, parse_agent2_output_text, parse_agent2_output_json
from utils.config import config

# Initialize KB agent with configured model
kb_retrievers = build_retrievers_from_csvs()
kb_agent = build_agent(kb_retrievers, model=config.kb_model)

def kb_retrieve(state: TicketState) -> TicketState:
    agent2_output_xml = kb_agent.invoke({
        "ticket_text": state.ticket_text,
        "category": state.category
    })["output"]

    agent2_parsed_json = parse_agent2_output_json(agent2_output_xml)
    if agent2_parsed_json:
        # Convert parsed sources to KBHit objects
        kb_hits = []
        for source in agent2_parsed_json.get("sources", []):
            kb_hits.append(KBHit(
                retriever=source.get("retriever", ""),
                summary=source.get("summary", "")
            ))
        
        state.kb_result = KBResult(
            retrieved_sources=kb_hits,
            consolidated_context=agent2_parsed_json.get("consolidated_context", "")
        )
        print(f"KB Agent: retrieved {len(state.kb_result.retrieved_sources)} sources")
    return state

