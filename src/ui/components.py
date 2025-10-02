"""
UI Components for the Customer Support Triage Streamlit App.
Contains all display functions for rendering the user interface.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any

from ui.workflow_runner import resume_run, load_run_state
from utils.config import config


def display_welcome():
    """Display welcome screen"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🎫</h1>
            <h2 style='margin-top: 0;'>Welcome to Customer Support Triage</h2>
            <p style='font-size: 1.1rem; color: #666; margin-bottom: 2rem;'>
                Intelligent multi-agent system for automating customer support workflows
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Feature cards
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("""
            #### 🎯 Smart Classification
            Automatically categorizes tickets by type and urgency using advanced NLP
            
            #### ✍️ Reply Generation  
            Generates professional, context-aware responses using AI
            
            #### 👤 Human Oversight
            Review and approve all actions before execution
            """)
        
        with col_b:
            st.markdown("""
            #### 📚 Knowledge Base
            Retrieves relevant information from comprehensive knowledge sources
            
            #### ⚡ Action Automation
            Suggests and executes system actions (refunds, password resets, etc.)
            
            #### 🔄 Redraft Support
            Iteratively improve responses with human feedback
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 Getting Started
        
        1. **Submit a Ticket** - Enter customer support text in the sidebar
        2. **Start Workflow** - Click the button to begin automated processing  
        3. **Review Results** - Check classification, KB results, and draft reply
        4. **Approve or Edit** - Modify responses and approve actions
        5. **Execute** - Let the system handle approved actions
        
        <div style='text-align: center; margin-top: 3rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;'>
            <p style='color: #666; margin: 0;'>
                <strong>Powered by LangGraph Multi-Agent Workflow</strong><br/>
                Built with Streamlit • Python • OpenAI
            </p>
        </div>
        """, unsafe_allow_html=True)


def display_run(run_id: str, run_state: Dict[str, Any]):
    """Display run details and controls"""
    status = run_state.get("status", "unknown")
    state_dict = run_state.get("state", {})
    history = run_state.get("history", [])
    
    status_colors = {
        "paused": "🟡",
        "completed": "🟢",
        "escalated": "🟠",
        "error": "🔴",
        "running": "🔵"
    }
    
    status_messages = {
        "paused": "Awaiting Human Review",
        "completed": "Workflow Completed",
        "escalated": "Escalated to Human Agent",
        "error": "Error Occurred",
        "running": "Processing"
    }
    
    # Header with status and metadata
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.subheader(f"{status_colors.get(status, '⚪')} Run ID: `{run_id}`")
        st.caption(status_messages.get(status, status.upper()))
    with col2:
        st.metric("Steps", f"{len(history)}")
    with col3:
        created_at = run_state.get("created_at", run_state.get("updated_at", ""))
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                st.metric("Created", dt.strftime("%H:%M:%S"))
            except:
                st.metric("Created", "N/A")
    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.run_state = load_run_state(run_id)
            st.rerun()
    
    st.markdown("---")
    
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
    st.text_area(
        "Ticket Text", 
        ticket_text, 
        height=150, 
        disabled=True,
        help="Original ticket submitted by customer"
    )
    
    st.markdown("---")
    st.subheader("🎯 Classification Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = state_dict.get("category", "N/A")
        category_conf = state_dict.get("category_conf", 0.0)
        st.metric(
            "Category",
            category.upper(),
            f"{category_conf * 100:.1f}% confidence"
        )
        
        if category_conf >= config.high_confidence:
            st.success("✅ High confidence")
        elif category_conf >= config.medium_confidence:
            st.warning("⚠️ Medium confidence")
        else:
            st.error("❌ Low confidence")
    
    with col2:
        urgency = state_dict.get("urgency", "N/A")
        urgency_conf = state_dict.get("urgency_conf", 0.0)
        st.metric(
            "Urgency",
            urgency.upper(),
            f"{urgency_conf * 100:.1f}% confidence"
        )
        
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
    
    if human_feedback:
        st.warning(f"⏳ Feedback pending: {human_feedback}")
    
    edited_reply = st.text_area(
        "Draft Reply:",
        reply_draft,
        height=200,
        disabled=(status not in ["paused"]),
        key=f"reply_edit_{run_id}_{redraft_count}"
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
            st.markdown(f"**📋 Rationale:** {rationale}")
            
            if status == "paused":
                st.markdown("---")
                st.markdown("**⚙️ Parameters** (editable):")
                
                if i not in st.session_state.action_params:
                    st.session_state.action_params[i] = params.copy()
                
                edited_params = {}
                for param_name, param_value in params.items():
                    param_key = f"{run_id}_action_{i}_param_{param_name}"
                    display_name = param_name.replace("_", " ").title()
                    
                    if isinstance(param_value, bool):
                        edited_value = st.checkbox(
                            f"{display_name}",
                            value=st.session_state.action_params[i].get(param_name, param_value),
                            key=param_key,
                            help=f"Parameter: {param_name}"
                        )
                    elif isinstance(param_value, (int, float)):
                        edited_value = st.number_input(
                            f"{display_name}",
                            value=float(st.session_state.action_params[i].get(param_name, param_value)),
                            key=param_key,
                            help=f"Parameter: {param_name}"
                        )
                        if isinstance(param_value, int):
                            edited_value = int(edited_value)
                    else:
                        edited_value = st.text_input(
                            f"{display_name}",
                            value=str(st.session_state.action_params[i].get(param_name, param_value)),
                            key=param_key,
                            help=f"Parameter: {param_name}"
                        )
                    
                    edited_params[param_name] = edited_value
                
                st.session_state.action_params[i] = edited_params
                
                st.markdown("---")
                approval_key = f"{run_id}_action_{i}_approval"
                
                approved_value = st.checkbox(
                    "✅ Approve this action",
                    value=approved if approved is not None else False,
                    key=approval_key
                )
                
                st.session_state.action_approvals[i] = approved_value
            else:
                st.markdown("**Parameters:**")
                st.json(params)
    
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
                st.session_state.action_params = {}
                st.rerun()


def display_history_and_results(run_state: Dict[str, Any]):
    """Display workflow history and execution results"""
    history = run_state.get("history", [])
    state_dict = run_state.get("state", {})
    status = run_state.get("status", "")
    
    st.subheader("📊 Workflow Execution Timeline")
    
    node_icons = {
        "triage": "🎯",
        "kb_retrieve": "📚",
        "draft_reply": "✍️",
        "draft_reply_redraft": "🔄",
        "suggest_actions": "⚡",
        "decide_human_review": "🤔",
        "human_review": "👤",
        "execute_actions": "⚙️",
        "post_or_escalate": "📤",
        "finalize": "✅"
    }
    
    for i, entry in enumerate(history):
        node = entry.get("node", "")
        timestamp = entry.get("timestamp", "")
        outputs = entry.get("outputs", {})
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%H:%M:%S")
        except:
            formatted_time = timestamp
        
        icon = node_icons.get(node, "▶️")
        node_display = node.replace("_", " ").title()
        
        with st.expander(f"{icon} Step {i+1}: {node_display} • {formatted_time}", expanded=False):
            if outputs:
                st.json(outputs)
            else:
                st.info("No output data recorded")
    
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
        
        st.subheader("📧 Final Reply")
        st.text_area(
            "Final reply sent to customer:",
            state_dict.get("reply_draft", ""),
            height=150,
            disabled=True
        )
        
        actions = state_dict.get("actions", [])
        executed_actions = [a for a in actions if a.get("approved")]
        
        if executed_actions:
            st.subheader("⚡ Executed Actions")
            for action in executed_actions:
                st.success(f"✅ {action.get('action')} - {action.get('params')}")
    
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
        result = resume_run(run_id, {
            "reply_draft": edited_reply,
            "human_feedback": feedback
        })
        
        st.session_state.run_state = result
        st.session_state.request_redraft = False
        
        if result.get("status") == "paused":
            st.success(result.get("message", "Redraft generated"))
        elif result.get("status") == "error":
            st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        st.rerun()


def execute_workflow(run_id: str, state_dict: Dict[str, Any]):
    """Execute workflow with approved actions and edited parameters"""
    actions = state_dict.get("actions", [])
    action_inputs = []
    
    for i, action in enumerate(actions):
        approved = st.session_state.action_approvals.get(i, False)
        edited_params = st.session_state.action_params.get(i, action.get("params", {}))
        
        action_inputs.append({
            "action": action.get("action"),
            "params": edited_params,
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
        st.session_state.action_params = {}
        
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
        st.session_state.action_params = {}
        st.warning("⚠️ Ticket escalated to human agent")
        st.rerun()
