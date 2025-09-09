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