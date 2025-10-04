import streamlit as st
import asyncio
from pathlib import Path

# Import UI components and workflow runners
from ui.workflow_runner import start_run, load_run_state, list_runs
from ui.components import display_welcome, display_run

# Configuration
RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

# Load custom CSS from file
def load_css():
    css_file = Path("ui/style.css")
    if css_file.exists():
        with open(css_file, "r") as f:
            return f"<style>{f.read()}</style>"
    return ""

CUSTOM_CSS = load_css()


def main():
    """Main Streamlit app entry point"""
    st.set_page_config(
        page_title="Customer Support Triage",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
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
                # Create placeholder for progress
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                progress_bar = progress_placeholder.progress(0)
                status_text = status_placeholder.empty()
                
                def update_progress(message, value):
                    progress_bar.progress(value)
                    status_text.info(f"⏳ {message}")
                
                try:
                    result = asyncio.run(start_run(ticket_text, progress_callback=update_progress))
                    st.session_state.run_id = result.get("run_id")
                    st.session_state.run_state = result
                    
                    # Clear progress indicators
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    
                    st.success("✅ Workflow processing complete!")
                    st.rerun()
                except Exception as e:
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    st.error(f"❌ Error: {str(e)}")
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


if __name__ == "__main__":
    main()
