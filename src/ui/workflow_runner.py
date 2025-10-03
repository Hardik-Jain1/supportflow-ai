"""
Workflow execution and state management for the Streamlit UI.
Handles running workflows, managing state, and persisting run data.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from utils.config import config

from flows.state.ticket_state import (
    TicketState,
    TicketMeta,
    KBResult,
    KBHit,
    ActionProposal
)
from flows.nodes.triage_node import triage_classifier
from flows.nodes.kb_node import kb_retrieve
from flows.nodes.reply_node import draft_reply
from flows.nodes.actions_node import suggest_actions
from flows.nodes.human_review_node import decide_human_review
from flows.nodes.execution_node import execute_actions, post_or_escalate
from flows.triage_workflow import finalize

# Configuration
RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)


def start_run(ticket_text: str, progress_callback=None) -> Dict[str, Any]:
    """
    Start a new workflow run with the given ticket text.
    Executes until pause (human review) or completion.
    """
    run_id = str(uuid.uuid4())[:8]
    
    # Create initial state
    initial_state = TicketState(
        ticket_text=ticket_text,
        meta=TicketMeta(
            source="web",
            created_at=datetime.now()
        )
    )
    
    # Save initial state
    save_run_state(run_id, {
        "run_id": run_id,
        "ticket_text": ticket_text,
        "status": "running",
        "current_node": "triage",
        "state": initial_state.model_dump(),
        "history": [],
        "created_at": datetime.now().isoformat()
    })
    
    # Execute workflow until human review or completion
    try:
        state = initial_state
        history = []
        
        if progress_callback:
            progress_callback("Classifying ticket...", 0.2)
        
        # Node 1: Triage
        state = triage_classifier(state)
        history.append({
            "node": "triage",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "category": state.category,
                "category_conf": state.category_conf,
                "urgency": state.urgency,
                "urgency_conf": state.urgency_conf
            }
        })
        
        if progress_callback:
            progress_callback("Retrieving knowledge base...", 0.4)
        
        # Node 2: KB Retrieve
        state = kb_retrieve(state)
        history.append({
            "node": "kb_retrieve",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "retrieved_sources": len(state.kb_result.retrieved_sources),
                "consolidated_context": state.kb_result.consolidated_context[:200] + "..."
            }
        })
        
        if progress_callback:
            progress_callback("Drafting reply...", 0.6)
        
        # Node 3: Draft Reply
        state = draft_reply(state)
        history.append({
            "node": "draft_reply",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "reply_draft": state.reply_draft,
                "redraft_count": state.redraft_count
            }
        })
        
        if progress_callback:
            progress_callback("Suggesting actions...", 0.8)
        
        # Node 4: Suggest Actions
        state = suggest_actions(state)
        history.append({
            "node": "suggest_actions",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "actions": [
                    {
                        "action": a.action,
                        "params": a.params,
                        "rationale": a.rationale,
                        "approved": a.approved
                    } for a in state.actions
                ]
            }
        })
        
        if progress_callback:
            progress_callback("Finalizing...", 0.9)
        
        # Node 5: Decide Human Review
        state = decide_human_review(state)
        history.append({
            "node": "decide_human_review",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "needs_review": state.needs_review
            }
        })
        
        if progress_callback:
            progress_callback("Complete!", 1.0)
        
        # Save state at human review pause point
        run_state = {
            "run_id": run_id,
            "ticket_text": ticket_text,
            "status": "paused" if state.needs_review else "running",
            "current_node": "human_review" if state.needs_review else "execute_actions",
            "state": state.model_dump(),
            "history": history,
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, run_state)
        
        return {
            "run_id": run_id,
            "status": "paused" if state.needs_review else "running",
            "state": state.model_dump(),
            "history": history
        }
        
    except Exception as e:
        error_state = {
            "run_id": run_id,
            "status": "error",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, error_state)
        return error_state


def resume_run(run_id: str, human_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume a paused workflow run with human inputs.
    
    human_inputs expected format:
    {
        "reply_draft": str,  # approved or edited reply
        "human_feedback": Optional[str],  # feedback for redraft
        "actions": [{"action": str, "params": dict, "approved": bool}]
    }
    """
    # Load saved state
    run_state = load_run_state(run_id)
    if not run_state:
        return {"error": "Run not found"}
    
    # Reconstruct TicketState from saved dict
    state_dict = run_state["state"]
    
    # Manually reconstruct nested objects to ensure proper typing
    kb_result_dict = state_dict.get("kb_result", {})
    kb_hits = [
        KBHit(**hit) if isinstance(hit, dict) else hit
        for hit in kb_result_dict.get("retrieved_sources", [])
    ]
    kb_result = KBResult(
        retrieved_sources=kb_hits,
        consolidated_context=kb_result_dict.get("consolidated_context", "")
    )
    
    actions = [
        ActionProposal(**action) if isinstance(action, dict) else action
        for action in state_dict.get("actions", [])
    ]
    
    meta_dict = state_dict.get("meta", {})
    if "created_at" in meta_dict and isinstance(meta_dict["created_at"], str):
        meta_dict["created_at"] = datetime.fromisoformat(meta_dict["created_at"].replace('Z', '+00:00'))
    meta = TicketMeta(**meta_dict)
    
    # Create state with reconstructed objects
    state = TicketState(
        ticket_text=state_dict["ticket_text"],
        meta=meta,
        language=state_dict.get("language", config.default_language),
        category=state_dict.get("category", config.default_category),
        category_conf=state_dict.get("category_conf", 0.0),
        urgency=state_dict.get("urgency", config.default_urgency),
        urgency_conf=state_dict.get("urgency_conf", 0.0),
        kb_result=kb_result,
        reply_draft=state_dict.get("reply_draft", ""),
        reply_conf=state_dict.get("reply_conf", 0.0),
        actions=actions,
        needs_review=state_dict.get("needs_review", False),
        human_feedback=state_dict.get("human_feedback"),
        redraft_count=state_dict.get("redraft_count", 0),
        posted=state_dict.get("posted", False),
        escalated=state_dict.get("escalated", False),
        retries=state_dict.get("retries", {}),
        errors=state_dict.get("errors", [])
    )
    
    history = run_state.get("history", [])
    
    # Apply human inputs
    state.reply_draft = human_inputs.get("reply_draft", state.reply_draft)
    
    # Set human_feedback BEFORE checking for redraft
    human_feedback_text = human_inputs.get("human_feedback")
    if human_feedback_text:
        state.human_feedback = human_feedback_text
    
    # Update action approvals and edited parameters
    if "actions" in human_inputs:
        for i, action_input in enumerate(human_inputs["actions"]):
            if i < len(state.actions):
                state.actions[i].approved = action_input.get("approved")
                if "params" in action_input:
                    state.actions[i].params = action_input["params"]
    
    history.append({
        "node": "human_review",
        "timestamp": datetime.now().isoformat(),
        "inputs": human_inputs,
        "redraft_count_before": state.redraft_count,
        "has_feedback": bool(state.human_feedback)
    })
    
    # Check if redraft is requested
    if state.human_feedback and state.redraft_count < config.max_redrafts:
        previous_draft = state.reply_draft
        
        state = draft_reply(state)
        
        history.append({
            "node": "draft_reply_redraft",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "reply_draft": state.reply_draft,
                "redraft_count": state.redraft_count,
                "feedback_applied": state.human_feedback is None,
                "reply_preview": state.reply_draft[:200] + "..." if len(state.reply_draft) > 200 else state.reply_draft,
                "reply_changed": state.reply_draft != previous_draft
            }
        })
        
        state.needs_review = True
        
        run_state = {
            "run_id": run_id,
            "ticket_text": state.ticket_text,
            "status": "paused",
            "current_node": "human_review",
            "state": state.model_dump(),
            "history": history,
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, run_state)
        
        return {
            "run_id": run_id,
            "status": "paused",
            "state": state.model_dump(),
            "history": history,
            "message": f"Redraft generated (attempt {state.redraft_count})"
        }
    
    # Check if escalation is requested
    escalate = human_inputs.get("escalate", False)
    if escalate or state.redraft_count >= config.max_redrafts:
        state.escalated = True
        state.needs_review = False
        
        run_state = {
            "run_id": run_id,
            "ticket_text": state.ticket_text,
            "status": "escalated",
            "current_node": "finalize",
            "state": state.model_dump(),
            "history": history,
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, run_state)
        
        return {
            "run_id": run_id,
            "status": "escalated",
            "state": state.model_dump(),
            "history": history
        }
    
    # Continue workflow: Execute actions
    try:
        state = execute_actions(state)
        history.append({
            "node": "execute_actions",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "executed_actions": [
                    {"action": a.action, "approved": a.approved}
                    for a in state.actions if a.approved
                ]
            }
        })
        
        state = post_or_escalate(state)
        history.append({
            "node": "post_or_escalate",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "posted": state.posted,
                "escalated": state.escalated
            }
        })
        
        state = finalize(state)
        history.append({
            "node": "finalize",
            "timestamp": datetime.now().isoformat()
        })
        
        run_state = {
            "run_id": run_id,
            "ticket_text": state.ticket_text,
            "status": "completed",
            "current_node": "finalize",
            "state": state.model_dump(),
            "history": history,
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, run_state)
        
        return {
            "run_id": run_id,
            "status": "completed",
            "state": state.model_dump(),
            "history": history
        }
        
    except Exception as e:
        error_state = {
            "run_id": run_id,
            "status": "error",
            "error": str(e),
            "state": state.model_dump(),
            "history": history,
            "updated_at": datetime.now().isoformat()
        }
        save_run_state(run_id, error_state)
        return error_state


def save_run_state(run_id: str, state: Dict[str, Any]):
    """Save run state to file"""
    file_path = RUNS_DIR / f"{run_id}.json"
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def load_run_state(run_id: str) -> Optional[Dict[str, Any]]:
    """Load run state from file"""
    file_path = RUNS_DIR / f"{run_id}.json"
    if not file_path.exists():
        return None
    with open(file_path, 'r') as f:
        return json.load(f)


def list_runs() -> list:
    """List all saved runs"""
    runs = []
    for file_path in RUNS_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                run_state = json.load(f)
                runs.append({
                    "run_id": run_state.get("run_id"),
                    "status": run_state.get("status"),
                    "created_at": run_state.get("created_at", run_state.get("updated_at")),
                    "ticket_preview": run_state.get("ticket_text", "")[:50] + "..."
                })
        except Exception:
            continue
    return sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)
