# Customer Support Triage & Action Agent — Requirements & MVP Plan

## One-line summary

An intelligent multi-agent system that automatically triages incoming support tickets, retrieves relevant knowledge-base (KB) articles, drafts appropriate replies, and suggests or executes safe actions (e.g., create Jira task, send payment reminder) while keeping a human in the loop for risky operations.

## Problem (simple terms)

Support teams get overloaded with routine, repetitive tickets (password resets, refund requests, order status). This creates slow response times, unhappy customers, and high cost per ticket. Manually reading and routing every ticket wastes human time that could be used for complex problems.

## What we will build (simple terms)

A system that:

* reads a new ticket,
* figures out what kind of problem it is (category, urgency, language),
* searches the company KB for relevant answers,
* drafts a reply (tone matched),
* suggests any actions (create Jira, refund request, escalate to L2),
* posts the draft or the action after human approval (depending on confidence and action type).

## Example (concrete)

Ticket: *"Hi — I was charged twice for my subscription last night. Please refund one charge ASAP."*
System flow (MVP):

1. Classifier tags ticket as **Billing / Refund** + **High urgency**.
2. KB Retriever finds the refund policy and sample refund wording.
3. Reply Drafter (CrewAI) drafts a polite reply including expected timeline.
4. Action Suggestor recommends creating a Jira task and flags for human approval for refund.
5. Agent posts the draft reply to the ticketing system and attaches the suggested Jira task link after human confirms the action.

## Stakeholders

* Customer support agents (primary users)
* Support managers (KPIs & policies)
* Customers (end beneficiaries)
* Engineers/Product (integration owners)
* Compliance/Finance (for monetary actions)

## Goals & Success Metrics

* Reduce first response time (FRT) by X% (e.g., 40%).
* Increase % of tickets with helpful suggested reply accepted by agent (target: 60–80% acceptance).
* Reduce manual triage time per ticket.
* Maintain/Improve CSAT on automated replies.
* Track false-positive action suggestions (target: near 0 for monetary actions).

## Requirements

### Functional requirements

* Ingest tickets from a ticketing system (Zendesk, Freshdesk, or CSV import).
* Classify ticket into categories (billing, technical, account, refund, general) and urgency levels.
* Perform KB semantic search and return top N relevant articles/snippets.
* Generate a reply draft with placeholders for variables (name, order id), tone-adjusted.
* Suggest actions (refund, create Jira, escalate, assign to team) with rationale.
* Post draft reply and/or submit suggested action to ticketing/issue systems via MCP.
* Provide a review UI (or ticket comment) where a human can accept/edit/reject suggested reply/actions.
* Maintain audit logs for every automated suggestion/action.

### Non-functional requirements

* Response latency: initial triage + draft within 30–90s for typical tickets.
* Availability: 99% for the MVP service during business hours.
* Security: role-based access, encrypted credentials for MCP integrations, GDPR/PII safe handling.
* Explainability: for each suggestion show short rationale (which KB snippet matched, classifier confidence).

## Data & Integrations

* Ticketing system API (Zendesk, Help Scout, Freshdesk) or CSV upload for historical data.
* Knowledge base (Confluence, Notion, markdown repo, or simple vector DB of KB articles).
* CRM for customer context (optional for MVP).
* Issue tracker (Jira) for escalations.
* Email/Slack connector for alerts.

## Agent Roles (mapping to frameworks)

* **Orchestrator (LangGraph)**: controls flow, retries, branching based on confidence.
* **Classifier (Smolagents)**: lightweight micro-agent for category & urgency classification.
* **KB Retriever (LangChain or LangGraph integrated retriever)**: semantic search using embeddings + vector DB.
* **Reply Crew (CrewAI)**: multiple agents collaborate to draft, polish, and format replies.
* **Action Executor (Smolagents + MCP tools)**: prepares suggestions and calls external APIs (only after approval for high-risk ops).
* **Bridge (ACP)**: handles cross-framework inter-agent messaging and contract enforcement.

## Safety & Guardrails

* Confidence thresholds determine automation level: e.g., auto-post reply only if (classifier\_conf > 0.9 AND reply\_conf > 0.9 AND action is non-monetary).
* Monetary actions (refunds) are always suggested and routed to human approval.
* Allowlist/blocklist for any automated outbound calls; sandbox mode for testing.
* Immutable audit log and change history for regulatory traceability.

## MVP Scope (minimal, fast-to-build)

* Data input: CSV bulk import + Zendesk demo account integration.
* Tasks: classification, KB retrieval, draft reply generation, suggested action creation (no auto-exec for financial ops).
* Orchestration: LangGraph or a simple queue-based orchestrator.
* Human-in-loop review UI: web page or simple dashboard showing suggested replies and actions with accept/edit buttons.
* Storage: vector DB for KB (e.g., FAISS/Chroma in dev), DB for logs and tickets (SQLite/Postgres).

## Acceptance Criteria for MVP

* System correctly classifies tickets in held-out test set with >= 85% accuracy for top categories.
* Draft replies are accepted by agents (no change or minor edits) >= 60% in a 100-ticket pilot.
* System suggests correct escalations (Jira creation) with low false positives in pilot.

## Example user stories

* *As a support agent, I want the system to draft replies for common questions so I can respond faster.*
* *As a support manager, I want the system to surface high-urgency tickets so I can prioritize staffing.*
* *As a compliance officer, I want an audit log for all automated suggestions and actions.*

## Constraints & Assumptions

* We assume access to \~1k anonymized historical tickets for training/tuning (or synthetic dataset otherwise).
* We assume KB is available in a text/HTML/markdown form to build a vector store.
* We will not auto-execute refunds in MVP.

## Next immediate steps (what I can deliver next, right away)

1. Create a proposed repo scaffold and folder layout (monorepo with `orchestrator/`, `agents/`, `mcp_tools/`, `ui/`, `data/`).
2. Draft the LangGraph flow (nodes + transitions) for MVP.
3. Provide sample Smolagents classifier code and prompt templates for CrewAI reply generation.

---

In the current flow, what we are doing is:
- given ticket text, the first agent will classifly the ticket to determine its category and urgency.
- then, the KB retriever will search for relevant articles based on the ticket category and ticket text.
- the reply crew will generate a draft reply based on the retrieved articles and ticket text.
- the action suggestor will suggest actions based on the ticket category and urgency, such as creating a Jira task or sending a payment reminder.
- then if the action is safe and the drafted reply is having high confidence, it will moe to action executor, otherwise it will be sent for human either for redrafting the reply or for actions approval.
- then the  action executor will execute the action, such as creating a Jira task or sending a payment reminder.
- then the drafted reply would to posted to the ticketing system.

so now I have couple of questions:
- how the action suggestor will suggest actions? what inputs it will get? only the ticket text or also the retrieved articles and the drafted reply? Also how this agent will suggest those actions? will it be a prompt (with available actions that can be taken) for llm which will provide the actions to be taken along with args and we need to parse those from its output? or will it be a tool calling llm to which we will pass the available actions as tools and then it will return the action to be taken along with args as tool calls? if it will be tool calling, then how we will handle the tool execution because the action executor will only execute any action once and return but will not provide it back to the llm used during the action suggestor step so as to decide if any further action is needed or not or if the action is sufficient or not just like how an agent work? or if it will be a prompt, then are we assuming that the llm will be able to understand the available actions and args and provide them in a structured way and would be the actions are themselves such that needs to be executed only once without any further reasoning? explain with examples.
- how the human in the loop will work? will there be a web UI where the human can see the drafted reply and the suggested actions for the tickets and approve or edit them? if so then in the node where the human needs to approve the reply or actions, the flow would be stuck until the human approves or edits the reply or actions, and then it will continue to the next node? explain with examples.
- what does the escalation mean in this context? because we are already having the human in the loop where human needs to approve the reply or actions, so what does it mean to escalate the ticket? is it just to notify the human that this ticket needs their attention and approval (which I think already done before this node when human review decided)? or is it to assign the ticket to a different team or agent for further handling? if the ticket does not need any human approval further because its already done then it should be posted as reply to that ticket i.e. in the ticket resolving system where I think the support team see any ticket and then reply to that ticket, after this agentic system the team will already be provided with some drafted reply for the tickets and the performed actions (which based on human approval), right? if so then where does the escalation come into play? and if the ticket needs further handling by a different team or agent, then how the system will handle that? explain with examples.
