from langgraph.graph import StateGraph, END
from flows.state.ticket_state import TicketState
from flows.nodes.triage_node import triage_classifier
from flows.nodes.kb_node import kb_retrieve
from flows.nodes.reply_node import draft_reply
from flows.nodes.actions_node import suggest_actions
from flows.nodes.human_review_node import decide_human_review, human_review_node
from flows.nodes.execution_node import execute_actions, post_or_escalate, finalize
from utils.config import config

def create_triage_workflow() -> StateGraph:
    workflow = StateGraph(TicketState)

    # Add all nodes
    workflow.add_node("triage", triage_classifier)
    workflow.add_node("kb_retrieve", kb_retrieve)
    workflow.add_node("draft_reply", draft_reply)
    workflow.add_node("suggest_actions", suggest_actions)
    workflow.add_node("decide_human_review", decide_human_review)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("execute_actions", execute_actions)
    workflow.add_node("post_or_escalate", post_or_escalate)
    workflow.add_node("finalize", finalize)

    # Set entry point
    workflow.set_entry_point("triage")

    # Define linear path
    workflow.add_edge("triage", "kb_retrieve")
    workflow.add_edge("kb_retrieve", "draft_reply")
    workflow.add_edge("draft_reply", "suggest_actions")
    workflow.add_edge("suggest_actions", "decide_human_review")

    # Conditional edges for human review
    workflow.add_conditional_edges(
        "decide_human_review",
        lambda s: "review" if s.needs_review else "no_review",
        {
            "review": "human_review",
            "no_review": "execute_actions",
        },
    )

    # Conditional edges for redrafting
    workflow.add_conditional_edges(
        "human_review",
        lambda s: "redraft" if (s.human_feedback and s.redraft_count < config.max_redrafts) else "proceed",
        {
            "redraft": "draft_reply", 
            "proceed": "execute_actions",
        },
    )

    # Final path
    workflow.add_edge("execute_actions", "post_or_escalate")
    workflow.add_edge("post_or_escalate", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()