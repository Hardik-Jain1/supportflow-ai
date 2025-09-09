# V1

# **Project Context – Customer Support Triage & Action Agent (Multi-Agent System)**

## **Problem Statement**

Customer support teams receive high volumes of tickets daily.
Challenges:

* Tickets must be **categorized** quickly (billing, technical, refund, feature request, etc.).
* Agents spend time searching the **knowledge base (KB)** for existing answers.
* **Draft replies** must be written, reviewed, and customized.
* Some cases require **action execution** (refund processing, creating Jira tickets, escalating).
  This leads to delays, inconsistent support quality, and unnecessary manual workload.

---

## **Proposed Solution**

We will build a **multi-agent AI system** using frameworks like **LangGraph, CrewAI, LangChain, Smolagents**, and communication via **ACP (Agent Communication Protocol)** with **MCP (Model Context Protocol)** for tool usage.

The system will:

1. **Classify** incoming tickets into categories.
2. **Retrieve** relevant KB documents/FAQs.
3. **Draft reply** using retrieved docs and ticket context.
4. **Review reply** (agent/human-in-loop optional).
5. **Escalate or Execute actions** (refund, Jira task, CRM update) via MCP-integrated tools.

This will **reduce support overhead**, **increase accuracy/consistency**, and **speed up ticket resolution**.

---

## **MVP Scope**

* Input: Raw support ticket (text).
* Output: Drafted reply OR executed action.
* Agents:

  * **Classifier Agent** → Categorizes ticket.
  * **KB Retrieval Agent** → Fetches relevant docs from KB.
  * **Drafting Agent** → Generates draft reply.
  * **Action Agent** → Executes actions (refund/Jira/etc.) via MCP.
  * **Review Agent** (optional) → Checks reply before sending.

---

## **LangGraph MVP Flow (High-level)**

1. **Start → Classifier Agent**

   * Input: `ticket_text`
   * Output: `category`

2. **Category → KB Retrieval Agent**

   * Input: `category`, `ticket_text`
   * Output: `kb_docs`

3. **KB Docs → Drafting Agent**

   * Input: `ticket_text`, `kb_docs`
   * Output: `draft_reply`

4. **Decision Node**

   * If draft is sufficient → **Reply Sent**
   * If action required → **Action Agent**
   * If unclear → **Review Agent (human-in-loop)**

5. **Action Agent (via MCP)**

   * Executes `refund`, `Jira ticket`, `CRM update`, etc.
   * Output: `tool_call_result`

6. **End** – Ticket resolved (reply + actions logged).

---

## **State Object (Example Schema)**

```yaml
ticket_text: str          # Original customer ticket
category: str             # Predicted category
kb_docs: list[str]        # Retrieved KB docs
draft_reply: str          # Generated draft reply
actions: list[str]        # Actions required (if any)
tool_call_result: dict    # MCP execution output
status: str               # [in_progress, resolved, escalated]
```

---

## **Tech Stack**

* **Multi-Agent Frameworks**: LangGraph, CrewAI, LangChain, Smolagents
* **Agent Communication**: ACP SDK (Python)
* **Tool Integration**: MCP SDK (Python)
* **Data**: Sample support tickets + Knowledge Base (FAQ/Docs)
* **Infra (later)**: Vector DB (Qdrant/Weaviate) for KB search, API layer for integration.

---

## **Project Approach**

1. **MVP (basic flow)** – Ticket → Classification → KB Retrieval → Draft Reply → End.
2. **Add Action Agent** – Integrate MCP for refund/Jira.
3. **Add Review Agent** – Optional human-in-loop before sending reply.
4. **Iterative Improvement** –

   * Custom tools (refund API mock, Jira API mock).
   * Better state design (error handling, retries, looping).
   * Production-level modularization & scaling.

---

This **context** should be enough to plug into any AI tool (Claude, GPT, Gemini, Cursor, etc.) and say:
👉 *“Help me implement part X of this project given this context.”*


# V2

## Project Context: Customer Support Triage & Action Agent

### Problem Statement

Customer support teams receive large volumes of tickets daily across multiple domains such as billing, technical issues, account management, and legal compliance. Manually triaging, drafting responses, retrieving knowledge base (KB) articles, and taking required actions (like refund initiation, order tracking, or Jira escalation) is slow and error-prone. This leads to delayed resolution, inconsistent responses, and reduced customer satisfaction.

### Solution Overview

We are building a **multi-agent AI system** for automated **customer support triage and action execution**, using frameworks like **LangGraph, CrewAI, LangChain, Smolagents**, while incorporating interoperability protocols like **Agent Communication Protocol (ACP)** and **Model Context Protocol (MCP)**.

The system will:

1. **Classify tickets** by category and urgency.
2. **Retrieve knowledge** from multiple KBs (billing, technical, account, orders, policies, etc.).
3. **Draft replies** for support tickets.
4. **Suggest actions** (refunds, order updates, escalations).
5. **Human-in-the-loop** review when confidence is low or actions require approval.
6. **Execute safe actions** and post replies to the ticketing system.

The system will start with a **Minimum Viable Product (MVP)** and iteratively improve toward production-grade design (scalable, modular, and following best practices).

### High-Level Agent Flow (LangGraph)

1. **Agent 1: Classifier**

   * Input: Raw ticket text.
   * Output: Category + Urgency.
   * Uses LLM prompt-based classification (with clear category definitions) instead of initial fine-tuning.

2. **Agent 2: Knowledge Retriever**

   * Inputs: Ticket text, Category, Urgency.
   * Has access to multiple retrievers (Billing, Technical, Account, Product, Feedback, Orders, Compliance, General).
   * Strategy: Always query the KB suggested by category, always check FAQ/General KB, optionally query others if needed.
   * Output: Context docs relevant to the ticket.

3. **Agent 3: Reply Drafter**

   * Inputs: Ticket text + retrieved docs.
   * Output: Drafted customer-facing reply (polite, clear, using evidence from docs).

4. **Agent 4: Action Suggestor**

   * Inputs: Ticket text, category, urgency, KB context, drafted reply.
   * Output: Suggested action(s) (structured JSON with action type + args).
   * Actions can include: issue refund, check order status, reset password, create Jira escalation, send reminder.

5. **Human-in-the-Loop**

   * Triggered if reply confidence is low, action requires approval, or escalation needed.
   * Human sees drafted reply + suggested actions in a UI.
   * Human may approve, edit, or override.

6. **Agent 5: Action Executor**

   * Executes safe MCP actions (refund, Jira creation, sending reminders).
   * Posts the approved drafted reply to ticketing system (e.g., inserts reply into Zendesk or Jira Service Desk).

### Escalation Definition

* Escalation means **creating a Jira ticket** or assigning the case to a higher-level team when it cannot be auto-resolved.
* This differs from human-in-the-loop (approval) because escalation indicates **reassigning ownership** of the ticket.

### Categories & Urgency Definitions

**Categories (8 total):**

1. Billing & Payments
2. Technical Issues
3. Account Management
4. Product/Service Inquiry
5. Feature Requests / Feedback
6. Order & Delivery
7. Compliance / Legal / Security
8. General / Other

**Urgency Levels (4 total):**

1. **Low (Informational)**: Minor/informational requests with no immediate impact.
2. **Medium (Routine)**: Timely but non-critical issues causing inconvenience.
3. **High (Blocking)**: Problems that block or significantly restrict product usage.
4. **Critical (Emergency)**: Severe issues requiring immediate escalation (outages, security breaches).

### Knowledge Base Design

We will maintain **separate retrievers/vector stores**:

* Billing KB
* Technical KB
* Account KB
* Product Inquiry KB
* Feedback KB
* Orders KB
* Compliance KB
* General/FAQ KB

### Human-in-the-Loop Workflow

* Human reviews when:

  * Drafted reply has low confidence.
  * Suggested action requires approval (e.g., refund above threshold).
  * Escalation is flagged.
* The flow is paused until human approves or edits.
* Once approved, the flow resumes to execution.

### Implementation Roadmap

1. Repo scaffold (done).
2. Define LangGraph state schema.
3. Implement mock nodes (Classifier, Retriever, Drafter, Action Suggestor, Executor).
4. Wire up LangGraph flow and test with dummy tickets.
5. Replace mocks with actual implementations of agents, including working on:
   * LLM prompts (Agent 1, Agent 2, Agent 3, Agent 4),
   * KB retrievers as tools for agent with FAISS/Qdrant (Agent 2),
   * MCP tools for action execution (Agent 5),
   * Defining ACP servers for inter-agent communication, etc.
6. Add Human-in-the-Loop interface (simple web UI).
7. Improve modularity, monitoring, and accuracy.

---

Till now, I have created the prompt for agent 1 (Classifier), now we will proceed to agent 2 implementation. Before going for it, let's first understand the things I already think about for agent 2 (to keep in mind while implementing it):

