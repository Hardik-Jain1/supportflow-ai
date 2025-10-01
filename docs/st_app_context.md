## Context for Building Streamlit UI for Customer Support Triage Multi-Agent Workflow

We have implemented a **multi-agent system** for Customer Support Triage using LangGraph, with 5 main agents:

1. **Agent 1 – Classifier**: Classifies ticket into predefined categories (Billing, Technical Issues, etc.) and assigns urgency.
2. **Agent 2 – KB Retrieval & Consolidation**: Retrieves knowledge from relevant KB retrievers, consolidates context, outputs in XML.
3. **Agent 3 – Reply Crew**: Multi-agent crew (drafting + refining) that produces a draft customer reply from the retrieved context.
4. **Agent 4 – Action Suggestor**: Suggests possible system actions (e.g., refund, reset password) based on ticket + context.
5. **Agent 5 – Action Executor**: Executes dummy implementations of selected actions.

The LangGraph workflow orchestrates these agents in sequence. Critical features:

* **Human-in-the-Loop (HITL)**: At the review stage, a human approves/edits the draft reply and approves/rejects suggested actions.
* **Redraft Loop**: If the draft reply is rejected, human feedback is passed back, and Agent 3 generates a new draft. This repeats until approval or max attempts.
* **Action Execution**: Approved actions are executed by dummy functions (`actions.py`) returning structured dict outputs.

---

## Streamlit App Requirements

We now want a **Streamlit app** that demonstrates the full workflow with HITL support. The app should:

### 1. Ticket Submission

* User enters a new ticket text into a sidebar text area.
* On submit, app starts a new workflow run (`start_run`).
* A unique `run_id` is created and stored in `st.session_state`.

### 2. Step-by-Step Workflow with Pauses

* Workflow runs until it hits a pause (e.g., HITL review node) or finishes.
* At each node, outputs are persisted and made available for UI display.
* HITL nodes pause the workflow, return intermediate outputs, and wait for user input.

### 3. HITL (Human Review) UI

* **Draft Reply Section**:

  * Show draft reply in editable text area.
  * Show prior feedback/drafts (version history) if any.
* **Action Suggestions Section**:

  * Display suggested actions with arguments.
  * Allow user to approve/reject via checkboxes.
  * Allow editing of arguments.
* **Context Panel**:

  * Show ticket category & urgency.
  * Show retrieved knowledge and consolidated context.
* **Control Buttons**:

  * Approve & Continue → workflow resumes to next node.
  * Request Redraft → workflow loops back to Agent 3 with human feedback.
  * Escalate → workflow terminates with escalation flag.

### 4. Redraft Loop

* If user requests redraft:

  * Feedback entered is passed to workflow (`resume_run`).
  * Agent 3 generates new draft, flow pauses again at HITL.
  * New draft is displayed in UI, with feedback history.
* Limit max attempts (e.g., 3 redrafts).
* After max attempts, escalate.

### 5. Action Execution & Final Results

* When actions are approved:

  * Agent 5 executes dummy implementations (`actions.py`).
  * Show execution results (table with action, args, status, details).
* Final reply is shown.
* Provide option to download full run log (JSON).

### 6. Run State Management

* Use `st.session_state` to track current `run_id` and node state.
* Persist full run state to file (`/tmp/langgraph_runs/<run_id>.json`).
* Workflow runner API should expose:

  * `start_run(ticket_text)` → starts a new run, executes until pause.
  * `resume_run(run_id, human_inputs)` → resumes from paused node with human input.
  * `load_run_state(run_id)` → loads saved state.

---

## Architecture

### Backend (Workflow API)

* Wrap LangGraph workflow with 3 functions:

```py
def start_run(ticket_text: str) -> Dict
    # starts workflow until pause or completion

def resume_run(run_id: str, human_inputs: Dict) -> Dict
    # resumes workflow from paused state

def load_run_state(run_id: str) -> Dict
    # loads saved state for Streamlit display
```

* Each node returns structured dict:

```json
{
  "run_id": "abc123",
  "node": "classifier",
  "status": "ok" | "paused" | "error",
  "outputs": {...},
  "history": [...]
}
```

### Frontend (Streamlit)

* Sidebar:

  * Ticket input box
  * Start button
  * Run history list
* Main area:

  * Show current node outputs
  * HITL controls (reply editor, action checkboxes, feedback box)
  * Approve/Reject buttons
  * Execution results display

---

## Key Notes for Implementation

* Replace `input()` calls in current workflow with pause + return structured state.
* Ensure Agent 3 accepts human feedback for redraft loop.
* Deterministic LLM outputs (set `temperature=0` for repeatability).
* All outputs (classifier, retriever, draft, actions, execution results) must be JSON/dict so Streamlit can render cleanly.
* Max 3 redrafts → escalate.
* Dummy actions in `actions.py` return structured dicts (already implemented).

---

## Deliverable

We want a **single Streamlit app** (`app.py`) that runs with:

```bash
streamlit run app.py
```

The app should:

* Let user submit ticket text.
* Show workflow step outputs (classification, KB retrieval, draft reply, suggested actions).
* Pause for HITL review and accept feedback.
* Support redraft loop.
* Execute approved actions and show results.
* Show final reply.
* Allow run log download.
