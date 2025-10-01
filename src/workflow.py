from __future__ import annotations
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from agents.triage_agent import triage_agent, parse_triage_result
from agents.kb_agent import build_retrievers_from_csvs, build_agent, parse_agent2_output_text, parse_agent2_output_json
from agents.reply_agent.crew import ReplyAgentCrew, reply_agent, redraft_reply_agent
from agents.action_suggester_agent import action_suggester_agent, parse_action_suggester_result
from agents.action_executor_agent import action_executor_agent
from utils.config import config

# Initialize KB agent with configured model
kb_retrievers = build_retrievers_from_csvs()
kb_agent = build_agent(kb_retrievers, model=config.kb_model)

# State definition
class KBHit(BaseModel):
    retriever: str
    summary: str

class KBResult(BaseModel):
    retrieved_sources: List[KBHit] = Field(default_factory=list)
    consolidated_context: str = ""

class ActionProposal(BaseModel):
    action: str 
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = 0.0
    rationale: str = ""
    approved: Optional[bool] = None 

class TicketMeta(BaseModel):
    source: Literal["email", "chat", "web", "api"] = "email"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_id: Optional[str] = None
    locale: Optional[str] = None

class TicketState(BaseModel):
    # Input
    ticket_text: str
    meta: TicketMeta = Field(default_factory=TicketMeta)

    # Derived
    language: str = Field(default_factory=lambda: config.default_language)
    category: Literal['billing', 'technical', 'account', 'product', 'feedback', 'orders', 'compliance', 'general'] = Field(default_factory=lambda: config.default_category)
    category_conf: float = 0.0
    urgency: Literal['low', 'medium', 'high', 'critical'] = Field(default_factory=lambda: config.default_urgency)
    urgency_conf: float = 0.0

    kb_result: KBResult = Field(default_factory=KBResult)

    reply_draft: str = ""
    reply_conf: Optional[float] = 0.0

    actions: List[ActionProposal] = Field(default_factory=list)

    # Human-in-the-loop
    needs_review: bool = False
    human_feedback: Optional[str] = None  # guidance for redraft
    redraft_count: int = 0

    # Execution & results
    posted: bool = False
    escalated: bool = False

    # Control & diagnostics
    retries: Dict[str, int] = Field(default_factory=dict)  # per-node retry counts
    errors: List[str] = Field(default_factory=list)

# Utility helpers (stubs for now)
def incr_retry(state: TicketState, key: str) -> int:
    state.retries[key] = state.retries.get(key, 0) + 1
    return state.retries[key]

def mcp_safe_call(tool_name: str, fn, state: TicketState, *args, **kwargs):
    """Minimal retry wrapper for MCP/tool calls.
    Replace `fn` with actual adapter (e.g., tools.ticketing.post_comment).
    """
    key = f"tool:{tool_name}"
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        count = incr_retry(state, key)
        state.errors.append(f"{key} error: {e}")
        if count <= config.max_retries:
            return fn(*args, **kwargs)
        raise

def get_narrative_context(kb_result: KBResult) -> str:
    if kb_result.retrieved_sources:
        narrative_parts = []
        narrative_parts.append("Relevant Knowledge:")
        
        for hit in kb_result.retrieved_sources:
            summary_clean = " ".join(hit.summary.split())
            narrative_parts.append(f"- {summary_clean} [{hit.retriever}]")
        
        narrative_parts.append("\nConsolidated Summary:")
        narrative_parts.append(kb_result.consolidated_context)
        
        narrative_context = "\n".join(narrative_parts)
    else:
        narrative_context = "No relevant knowledge found."
    return narrative_context

# Node implementations
# 1) Triage classification
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

# 2) KB retrieval (semantic search via vector DB)
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

# 3) Reply drafting (CrewAI team or single LLM) — updated to support redrafting
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

# 4) Action suggestions
def suggest_actions(state: TicketState) -> TicketState:
    if state.actions:
        print("Action Suggester Agent: actions already proposed, skipping")
        return state 
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

# 5) Decide whether human review is needed
def decide_human_review(state: TicketState) -> TicketState:
    if config.force_human_review:
        state.needs_review = True
    else:
        risky_present = any(p.action in config.risky_actions for p in state.actions)
        low_conf_reply = state.reply_conf < config.high_confidence
        low_conf_category = state.category_conf < config.high_confidence
        state.needs_review = risky_present or low_conf_reply or low_conf_category
    return state

# 7) (Placeholder) Human review node
def human_review_node(state: TicketState) -> TicketState:
    if not state.needs_review:
        return state
    
    # Show current state to human reviewer
    print("\n" + "="*config.separator_length)
    print("HUMAN REVIEW REQUIRED")
    print("="*config.separator_length)
    ticket_preview = state.ticket_text[:config.max_ticket_preview_length]
    if len(state.ticket_text) > config.max_ticket_preview_length:
        ticket_preview += "..."
    print(f"Ticket: {ticket_preview}")
    print(f"Category: {state.category} (confidence: {state.category_conf:.{config.display_confidence_decimals}f})")
    print(f"Urgency: {state.urgency} (confidence: {state.urgency_conf:.{config.display_confidence_decimals}f})")
    print(f"\nProposed Reply:\n{state.reply_draft}")
    
    print(f"\nProposed Actions:")
    for i, action in enumerate(state.actions):
        risk_status = "RISKY" if action.action in config.risky_actions else "SAFE"
        print(f"  {i+1}. {action.action} [{risk_status}]")
        print(f"     Params: {action.params}")
        print(f"     Rationale: {action.rationale}")
    
    print("\n" + "-"*config.separator_length)
    
    # Get human input for actions
    for i, action in enumerate(state.actions):
        while True:
            approve = input(f"Approve action '{action.action}'? (y/n/skip): ").lower().strip()
            if approve == 'y':
                action.approved = True
                break
            elif approve == 'n':
                action.approved = False
                break
            elif approve == 'skip':
                action.approved = None
                break
            else:
                print("Please enter 'y', 'n', or 'skip'")
    
    # Get feedback for reply
    while True:
        reply_feedback = input("\nReply feedback (press Enter to approve, 'r' to request revision): ").strip()
        if reply_feedback == '':
            # Approved as-is
            state.human_feedback = None
            break
        elif reply_feedback.lower() == 'r':
            while True:
                revision_type = input("Enter 'manual' to provide your own draft, or 'auto' for AI redraft with feedback: ").strip().lower()
                if revision_type == 'manual':
                    new_draft = input("Enter your revised reply: ").strip()
                    if new_draft:
                        state.reply_draft = new_draft
                        state.human_feedback = None  # No feedback needed for manual draft
                    break
                elif revision_type == 'auto':
                    revision_request = input("Enter revision instructions: ").strip()
                    state.human_feedback = revision_request  # Set feedback for AI redraft
                    state.redraft_count += 1
                    break
                else:
                    print("Invalid option. Enter 'manual' to provide your own draft, or 'auto' for AI redraft with feedback: ")
            break
        else:
            print("Invalid option. Press Enter to approve or 'r' to request revision")
    
    print("="*config.separator_length + "\n")
    return state

# 8) Execute approved actions
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

# 9) Post reply or escalate
def post_or_escalate(state: TicketState) -> TicketState:
    if "create_support_ticket" in [a.action for a in state.actions if a.approved]:
        state.escalated = True
        state.posted = False
        return state
    state.posted = True
    return state

# 10) Metrics / finalize
def finalize(state: TicketState) -> TicketState:
    print(f"Ticket processing completed at {datetime.now()}")
    print(f"Final state: Posted={state.posted}, Escalated={state.escalated}")
    print(f"Total retries: {sum(state.retries.values())}")
    if state.errors:
        print(f"Errors encountered: {len(state.errors)}")
    return state

# Build the graph (with loops)
workflow = StateGraph(TicketState)

workflow.add_node("triage", triage_classifier)
workflow.add_node("kb_retrieve", kb_retrieve)
workflow.add_node("draft_reply", draft_reply)
workflow.add_node("suggest_actions", suggest_actions)
workflow.add_node("decide_human_review", decide_human_review)
workflow.add_node("human_review", human_review_node)
workflow.add_node("execute_actions", execute_actions)
workflow.add_node("post_or_escalate", post_or_escalate)
workflow.add_node("finalize", finalize)

workflow.set_entry_point("triage")

# Linear path up to decisions
workflow.add_edge("triage", "kb_retrieve")
workflow.add_edge("kb_retrieve", "draft_reply")
workflow.add_edge("draft_reply", "suggest_actions")
workflow.add_edge("suggest_actions", "decide_human_review")

# Branch: review or proceed
workflow.add_conditional_edges(
    "decide_human_review",
    lambda s: "review" if s.needs_review else "no_review",
    {
        "review": "human_review",
        "no_review": "execute_actions",
    },
)

# After human review, possibly loop for redraft if feedback present and under limit
# (In production, the human review node would set human_feedback; here we emulate.)
workflow.add_conditional_edges(
    "human_review",
    lambda s: "redraft" if (s.human_feedback and s.redraft_count < config.max_redrafts) else "proceed",
    {
        "redraft": "draft_reply", 
        "proceed": "execute_actions",
    },
)

workflow.add_edge("execute_actions", "post_or_escalate")
workflow.add_edge("post_or_escalate", "finalize")
workflow.add_edge("finalize", END)

triage_flow = workflow.compile()

# Minimal runnable example (dev only)
if __name__ == "__main__":
    sample = TicketState(ticket_text=input("Enter ticket text: "))
    out = triage_flow.invoke(sample)
