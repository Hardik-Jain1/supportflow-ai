import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Import workflow components
from workflow import (
    TicketState, 
    TicketMeta,
    KBResult,
    KBHit,
    ActionProposal,
    triage_flow,
    get_narrative_context
)
from utils.config import config

# Configuration
RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

# ============================================================================
# Workflow Runner API
# ============================================================================

def start_run(ticket_text: str) -> Dict[str, Any]:
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
        # Run triage
        state = initial_state
        history = []
        
        # Node 1: Triage
        from workflow import triage_classifier
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
        
        # Node 2: KB Retrieve
        from workflow import kb_retrieve
        state = kb_retrieve(state)
        history.append({
            "node": "kb_retrieve",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "retrieved_sources": len(state.kb_result.retrieved_sources),
                "consolidated_context": state.kb_result.consolidated_context[:200] + "..."
            }
        })
        
        # Node 3: Draft Reply
        from workflow import draft_reply
        state = draft_reply(state)
        history.append({
            "node": "draft_reply",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "reply_draft": state.reply_draft,
                "redraft_count": state.redraft_count
            }
        })
        
        # Node 4: Suggest Actions
        from workflow import suggest_actions
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
        
        # Node 5: Decide Human Review
        from workflow import decide_human_review
        state = decide_human_review(state)
        history.append({
            "node": "decide_human_review",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "needs_review": state.needs_review
            }
        })
        
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
    
    print(f"[DEBUG] Reconstructing state from saved run")
    print(f"[DEBUG] Saved redraft_count: {state_dict.get('redraft_count', 0)}")
    print(f"[DEBUG] Saved reply_draft length: {len(state_dict.get('reply_draft', ''))}")
    
    # Manually reconstruct nested objects to ensure proper typing
    # Reconstruct KBResult
    kb_result_dict = state_dict.get("kb_result", {})
    kb_hits = [
        KBHit(**hit) if isinstance(hit, dict) else hit
        for hit in kb_result_dict.get("retrieved_sources", [])
    ]
    kb_result = KBResult(
        retrieved_sources=kb_hits,
        consolidated_context=kb_result_dict.get("consolidated_context", "")
    )
    
    # Reconstruct ActionProposals
    actions = [
        ActionProposal(**action) if isinstance(action, dict) else action
        for action in state_dict.get("actions", [])
    ]
    
    # Reconstruct TicketMeta
    meta_dict = state_dict.get("meta", {})
    if "created_at" in meta_dict and isinstance(meta_dict["created_at"], str):
        from datetime import datetime
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
    
    # IMPORTANT: Set human_feedback BEFORE checking for redraft
    # This ensures draft_reply function receives the feedback
    human_feedback_text = human_inputs.get("human_feedback")
    if human_feedback_text:
        state.human_feedback = human_feedback_text
    
    # Update action approvals and edited parameters
    if "actions" in human_inputs:
        print(f"[DEBUG] Updating {len(human_inputs['actions'])} actions from human inputs")
        for i, action_input in enumerate(human_inputs["actions"]):
            if i < len(state.actions):
                # Update approval status
                state.actions[i].approved = action_input.get("approved")
                
                # Update params if provided (edited by user)
                if "params" in action_input:
                    original_params = state.actions[i].params
                    new_params = action_input["params"]
                    
                    print(f"[DEBUG] Action {i} ({state.actions[i].action}):")
                    print(f"[DEBUG]   Approved: {state.actions[i].approved}")
                    print(f"[DEBUG]   Original params: {original_params}")
                    print(f"[DEBUG]   Updated params: {new_params}")
                    
                    state.actions[i].params = new_params
    
    history.append({
        "node": "human_review",
        "timestamp": datetime.now().isoformat(),
        "inputs": human_inputs,
        "redraft_count_before": state.redraft_count,
        "has_feedback": bool(state.human_feedback)
    })
    
    # Check if redraft is requested
    if state.human_feedback and state.redraft_count < config.max_redrafts:
        # Redraft loop
        print(f"[DEBUG] Redrafting with feedback: {state.human_feedback[:50]}...")
        print(f"[DEBUG] Current redraft_count: {state.redraft_count}")
        print(f"[DEBUG] Previous reply length: {len(state.reply_draft)}")
        
        # Store previous draft for comparison
        previous_draft = state.reply_draft
        
        from workflow import draft_reply
        state = draft_reply(state)
        
        print(f"[DEBUG] After draft_reply, redraft_count: {state.redraft_count}")
        print(f"[DEBUG] New reply length: {len(state.reply_draft)}")
        print(f"[DEBUG] Reply changed: {state.reply_draft != previous_draft}")
        print(f"[DEBUG] Feedback cleared: {state.human_feedback is None}")
        
        history.append({
            "node": "draft_reply_redraft",
            "timestamp": datetime.now().isoformat(),
            "outputs": {
                "reply_draft": state.reply_draft,
                "redraft_count": state.redraft_count,
                "feedback_applied": state.human_feedback is None,  # Should be None after processing
                "reply_preview": state.reply_draft[:200] + "..." if len(state.reply_draft) > 200 else state.reply_draft,
                "reply_changed": state.reply_draft != previous_draft
            }
        })
        
        # Keep in review mode for another round
        state.needs_review = True
        
        # Pause again for review
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
        from workflow import execute_actions, post_or_escalate, finalize
        
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


# ============================================================================
# Streamlit UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="Customer Support Triage Agent",
        page_icon="🎫",
        layout="wide"
    )
    
    st.title("🎫 Customer Support Triage Multi-Agent System")
    st.markdown("---")
    
    # Initialize session state
    if "run_id" not in st.session_state:
        st.session_state.run_id = None
    if "run_state" not in st.session_state:
        st.session_state.run_state = None
    
    # Sidebar
    with st.sidebar:
        st.header("📝 New Ticket")
        
        ticket_text = st.text_area(
            "Enter ticket text:",
            height=150,
            placeholder="Describe the customer support issue..."
        )
        
        if st.button("🚀 Start Workflow", type="primary", use_container_width=True):
            if ticket_text.strip():
                with st.spinner("Processing ticket..."):
                    result = start_run(ticket_text)
                    st.session_state.run_id = result.get("run_id")
                    st.session_state.run_state = result
                    st.rerun()
            else:
                st.error("Please enter ticket text")
        
        st.markdown("---")
        st.header("📋 Run History")
        
        runs = list_runs()
        if runs:
            for run in runs[:5]:  # Show last 5 runs
                status_icon = {
                    "paused": "⏸️",
                    "completed": "✅",
                    "escalated": "⚠️",
                    "error": "❌",
                    "running": "▶️"
                }.get(run["status"], "❓")
                
                if st.button(
                    f"{status_icon} {run['run_id']} - {run['status']}",
                    key=f"load_{run['run_id']}",
                    use_container_width=True
                ):
                    st.session_state.run_id = run["run_id"]
                    st.session_state.run_state = load_run_state(run["run_id"])
                    st.rerun()
        else:
            st.info("No runs yet")
    
    # Main area
    if st.session_state.run_id and st.session_state.run_state:
        display_run(st.session_state.run_id, st.session_state.run_state)
    else:
        display_welcome()


def display_welcome():
    """Display welcome screen"""
    st.markdown("""
    ## Welcome to the Customer Support Triage System
    
    This multi-agent system helps automate customer support ticket processing with:
    
    - 🎯 **Automatic Classification**: Categorizes tickets by type and urgency
    - 📚 **Knowledge Base Retrieval**: Finds relevant information from KB
    - ✍️ **Reply Drafting**: Generates professional responses
    - ⚡ **Action Suggestions**: Recommends system actions (refunds, password resets, etc.)
    - 👤 **Human-in-the-Loop**: Review and approve before execution
    
    ### Getting Started
    
    1. Enter a customer support ticket in the sidebar
    2. Click "Start Workflow" to begin processing
    3. Review the automated analysis and suggestions
    4. Approve, edit, or request redrafts
    5. Execute approved actions
    
    ---
    
    **Powered by LangGraph Multi-Agent Workflow**
    """)


def display_run(run_id: str, run_state: Dict[str, Any]):
    """Display run details and controls"""
    status = run_state.get("status", "unknown")
    state_dict = run_state.get("state", {})
    
    # Status indicator
    status_colors = {
        "paused": "🟡",
        "completed": "🟢",
        "escalated": "🟠",
        "error": "🔴",
        "running": "🔵"
    }
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"{status_colors.get(status, '⚪')} Run: {run_id}")
    with col2:
        st.metric("Status", status.upper())
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.run_state = load_run_state(run_id)
            st.rerun()
    
    # Error handling
    if status == "error":
        st.error(f"Error: {run_state.get('error', 'Unknown error')}")
        return
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Ticket & Classification",
        "📚 Knowledge Base",
        "✍️ Reply Draft",
        "⚡ Actions",
        "📊 History & Results"
    ])
    
    with tab1:
        display_ticket_classification(state_dict)
    
    with tab2:
        display_knowledge_base(state_dict)
    
    with tab3:
        display_reply_section(run_id, state_dict, status)
    
    with tab4:
        display_actions_section(run_id, state_dict, status)
    
    with tab5:
        display_history_and_results(run_state)


def display_ticket_classification(state_dict: Dict[str, Any]):
    """Display ticket text and classification results"""
    st.subheader("🎫 Ticket Details")
    
    ticket_text = state_dict.get("ticket_text", "")
    st.text_area("Ticket Text", ticket_text, height=150, disabled=True)
    
    st.markdown("---")
    st.subheader("🎯 Classification Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = state_dict.get("category", "N/A")
        category_conf = state_dict.get("category_conf", 0.0)
        st.metric(
            "Category",
            category.upper(),
            f"{category_conf:.2f}% confidence"
        )
        
        # Confidence indicator
        if category_conf >= config.high_confidence:
            st.success("High confidence ✅")
        elif category_conf >= config.medium_confidence:
            st.warning("Medium confidence ⚠️")
        else:
            st.error("Low confidence ❌")
    
    with col2:
        urgency = state_dict.get("urgency", "N/A")
        urgency_conf = state_dict.get("urgency_conf", 0.0)
        st.metric(
            "Urgency",
            urgency.upper(),
            f"{urgency_conf:.2f}% confidence"
        )
        
        # Urgency indicator
        urgency_colors = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        st.markdown(f"### {urgency_colors.get(urgency, '⚪')} {urgency.upper()}")


def display_knowledge_base(state_dict: Dict[str, Any]):
    """Display KB retrieval results"""
    kb_result = state_dict.get("kb_result", {})
    retrieved_sources = kb_result.get("retrieved_sources", [])
    consolidated_context = kb_result.get("consolidated_context", "")
    
    st.subheader("📚 Retrieved Knowledge")
    
    if retrieved_sources:
        st.info(f"Found {len(retrieved_sources)} relevant knowledge sources")
        
        for i, source in enumerate(retrieved_sources, 1):
            with st.expander(f"Source {i}: {source.get('retriever', 'Unknown')}"):
                st.markdown(source.get("summary", ""))
        
        st.markdown("---")
        st.subheader("📝 Consolidated Context")
        st.text_area(
            "Consolidated knowledge for reply generation:",
            consolidated_context,
            height=200,
            disabled=True
        )
    else:
        st.warning("No relevant knowledge found in the knowledge base.")


def display_reply_section(run_id: str, state_dict: Dict[str, Any], status: str):
    """Display reply draft and human review controls"""
    reply_draft = state_dict.get("reply_draft", "")
    redraft_count = state_dict.get("redraft_count", 0)
    human_feedback = state_dict.get("human_feedback")
    
    st.subheader("✍️ Reply Draft")
    
    # Show redraft information
    if redraft_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📝 This is redraft #{redraft_count} of {config.max_redrafts} maximum redrafts")
        with col2:
            remaining = config.max_redrafts - redraft_count
            if remaining > 0:
                st.metric("Redrafts Left", remaining)
            else:
                st.warning("Max redrafts reached")
    
    # Show if there was previous feedback
    if human_feedback:
        st.warning(f"⏳ Feedback pending: {human_feedback}")
    
    # Editable reply
    edited_reply = st.text_area(
        "Draft Reply:",
        reply_draft,
        height=200,
        disabled=(status not in ["paused"]),
        key=f"reply_edit_{run_id}_{redraft_count}"  # Add redraft_count to key to force refresh
    )
    
    if status == "paused":
        st.markdown("---")
        st.subheader("💭 Feedback & Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve Reply", type="primary", use_container_width=True):
                st.session_state.reply_approved = True
                st.session_state.edited_reply = edited_reply
        
        with col2:
            if redraft_count < config.max_redrafts:
                if st.button("🔄 Request Redraft", use_container_width=True):
                    st.session_state.request_redraft = True
        
        # Redraft feedback input
        if st.session_state.get("request_redraft"):
            feedback = st.text_area(
                "Provide feedback for redraft:",
                placeholder="E.g., 'Make it more empathetic' or 'Add troubleshooting steps'",
                key=f"feedback_{run_id}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Submit Feedback", type="primary", use_container_width=True):
                    if feedback.strip():
                        resume_with_feedback(run_id, edited_reply, feedback)
                    else:
                        st.error("Please provide feedback")
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.request_redraft = False
                    st.rerun()


def display_actions_section(run_id: str, state_dict: Dict[str, Any], status: str):
    """Display suggested actions and approval controls"""
    actions = state_dict.get("actions", [])
    
    st.subheader("⚡ Suggested Actions")
    
    if not actions:
        st.info("No actions suggested for this ticket.")
        return
    
    # Initialize session state for action approvals and edited params
    if "action_approvals" not in st.session_state:
        st.session_state.action_approvals = {}
    if "action_params" not in st.session_state:
        st.session_state.action_params = {}
    
    for i, action in enumerate(actions):
        action_name = action.get("action", "")
        params = action.get("params", {})
        rationale = action.get("rationale", "")
        approved = action.get("approved")
        
        is_risky = action_name in config.risky_actions
        
        with st.expander(
            f"{'🔴 RISKY' if is_risky else '🟢 SAFE'}: {action_name}",
            expanded=(status == "paused")
        ):
            st.markdown(f"**Rationale:** {rationale}")
            
            if status == "paused":
                st.markdown("**Parameters:**")
                
                # Initialize params dict for this action if not exists
                if i not in st.session_state.action_params:
                    st.session_state.action_params[i] = params.copy()
                
                # Create editable inputs for each parameter
                edited_params = {}
                for param_name, param_value in params.items():
                    param_key = f"{run_id}_action_{i}_param_{param_name}"
                    
                    # Determine input type based on value
                    if isinstance(param_value, bool):
                        edited_value = st.checkbox(
                            f"**{param_name}**",
                            value=st.session_state.action_params[i].get(param_name, param_value),
                            key=param_key
                        )
                    elif isinstance(param_value, (int, float)):
                        edited_value = st.number_input(
                            f"**{param_name}**",
                            value=float(st.session_state.action_params[i].get(param_name, param_value)),
                            key=param_key
                        )
                        # Convert back to int if original was int
                        if isinstance(param_value, int):
                            edited_value = int(edited_value)
                    else:
                        # String or other types
                        edited_value = st.text_input(
                            f"**{param_name}**",
                            value=str(st.session_state.action_params[i].get(param_name, param_value)),
                            key=param_key
                        )
                    
                    edited_params[param_name] = edited_value
                
                # Update session state with edited params
                st.session_state.action_params[i] = edited_params
                
                # Show approval checkbox
                st.markdown("---")
                approval_key = f"{run_id}_action_{i}_approval"
                
                if approved is None:
                    default_approval = False
                else:
                    default_approval = approved
                
                approved_value = st.checkbox(
                    "✅ Approve this action",
                    value=default_approval,
                    key=approval_key
                )
                
                st.session_state.action_approvals[i] = approved_value
            else:
                # Display params as read-only JSON when not in paused state
                st.markdown("**Parameters:**")
                st.json(params)
    
    # Execute actions button
    if status == "paused" and st.session_state.get("reply_approved"):
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Execute Approved Actions", type="primary", use_container_width=True):
                execute_workflow(run_id, state_dict)
        
        with col2:
            if st.button("⚠️ Escalate to Human", use_container_width=True):
                escalate_workflow(run_id)
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.reply_approved = False
                st.session_state.action_approvals = {}
                st.session_state.action_params = {}  # Clear edited params
                st.rerun()


def display_history_and_results(run_state: Dict[str, Any]):
    """Display workflow history and execution results"""
    history = run_state.get("history", [])
    state_dict = run_state.get("state", {})
    status = run_state.get("status", "")
    
    st.subheader("📊 Workflow History")
    
    for i, entry in enumerate(history):
        node = entry.get("node", "")
        timestamp = entry.get("timestamp", "")
        outputs = entry.get("outputs", {})
        
        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp
        
        with st.expander(f"Step {i+1}: {node} - {formatted_time}"):
            st.json(outputs)
    
    # Execution results
    if status == "completed":
        st.markdown("---")
        st.subheader("✅ Execution Results")
        
        posted = state_dict.get("posted", False)
        escalated = state_dict.get("escalated", False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Reply Posted", "✅ Yes" if posted else "❌ No")
        with col2:
            st.metric("Escalated", "⚠️ Yes" if escalated else "✅ No")
        
        # Final reply
        st.subheader("📧 Final Reply")
        st.text_area(
            "Final reply sent to customer:",
            state_dict.get("reply_draft", ""),
            height=150,
            disabled=True
        )
        
        # Action execution results (if available)
        actions = state_dict.get("actions", [])
        executed_actions = [a for a in actions if a.get("approved")]
        
        if executed_actions:
            st.subheader("⚡ Executed Actions")
            for action in executed_actions:
                st.success(f"✅ {action.get('action')} - {action.get('params')}")
    
    # Download run log
    st.markdown("---")
    if st.button("📥 Download Run Log (JSON)", use_container_width=True):
        json_str = json.dumps(run_state, indent=2, default=str)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"run_{run_state.get('run_id')}.json",
            mime="application/json",
            use_container_width=True
        )


def resume_with_feedback(run_id: str, edited_reply: str, feedback: str):
    """Resume workflow with human feedback for redraft"""
    with st.spinner("Generating redraft..."):
        print(f"[DEBUG] resume_with_feedback called with:")
        print(f"  run_id: {run_id}")
        print(f"  feedback: {feedback[:100]}...")
        
        # Don't pass actions when requesting redraft - let them stay as-is
        result = resume_run(run_id, {
            "reply_draft": edited_reply,
            "human_feedback": feedback
            # Note: Not passing "actions" to preserve existing action state
        })
        
        print(f"[DEBUG] Result status: {result.get('status')}")
        print(f"[DEBUG] Result message: {result.get('message', 'No message')}")
        
        st.session_state.run_state = result
        st.session_state.request_redraft = False
        
        if result.get("status") == "paused":
            st.success(result.get("message", "Redraft generated"))
        elif result.get("status") == "error":
            st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        st.rerun()


def execute_workflow(run_id: str, state_dict: Dict[str, Any]):
    """Execute workflow with approved actions and edited parameters"""
    # Gather action approvals and edited parameters
    actions = state_dict.get("actions", [])
    action_inputs = []
    
    print(f"[DEBUG] execute_workflow called for run_id: {run_id}")
    print(f"[DEBUG] Total actions: {len(actions)}")
    
    for i, action in enumerate(actions):
        approved = st.session_state.action_approvals.get(i, False)
        
        # Use edited params from session state if available, otherwise use original
        edited_params = st.session_state.action_params.get(i, action.get("params", {}))
        
        print(f"[DEBUG] Action {i}: {action.get('action')}")
        print(f"[DEBUG]   Approved: {approved}")
        print(f"[DEBUG]   Original params: {action.get('params')}")
        print(f"[DEBUG]   Edited params: {edited_params}")
        
        action_inputs.append({
            "action": action.get("action"),
            "params": edited_params,  # Use edited params
            "approved": approved
        })
    
    with st.spinner("Executing actions..."):
        result = resume_run(run_id, {
            "reply_draft": st.session_state.get("edited_reply", state_dict.get("reply_draft")),
            "actions": action_inputs
        })
        
        st.session_state.run_state = result
        st.session_state.reply_approved = False
        st.session_state.action_approvals = {}
        st.session_state.action_params = {}  # Clear edited params
        
        if result.get("status") == "completed":
            st.success("✅ Workflow completed successfully!")
        st.rerun()


def escalate_workflow(run_id: str):
    """Escalate workflow to human agent"""
    with st.spinner("Escalating to human agent..."):
        result = resume_run(run_id, {"escalate": True})
        
        st.session_state.run_state = result
        st.session_state.reply_approved = False
        st.session_state.action_approvals = {}
        st.session_state.action_params = {}  # Clear edited params
        st.warning("⚠️ Ticket escalated to human agent")
        st.rerun()


if __name__ == "__main__":
    main()
