
## Context: Agent 2 (Knowledge Retriever / Reasoning Agent)

### Role of Agent 2

Agent 2 is responsible for retrieving relevant knowledge base (KB) documents to support ticket resolution. It takes as input the **ticket text**, along with the **category and urgency** determined by Agent 1, and outputs a set of relevant context documents that downstream agents (Reply Drafter, Action Suggestor) can use.

---

### Options Considered for Implementation

#### **Option 1: Simple KB Retriever**

* **Approach:**

  * Based directly on the classified category from Agent 1.
  * Retrieve top-k documents from a single, predefined KB (e.g., Billing KB for Billing category).
* **Pros:**

  * Simpler and deterministic.
  * Easy to implement.
  * Lower cost (fewer LLM calls).
* **Cons:**

  * Cannot handle multi-faceted queries that touch multiple domains.
  * Risks missing relevant docs (e.g., a billing + login issue).
* **Example:**

  * Ticket: “I was double charged and now can’t log in.”
  * Agent 1 → Category: Billing & Payments.
  * Agent 2 (Option 1) → Queries only Billing KB.
  * Misses relevant context from Account KB.

---

#### **Option 2: Reasoning Agent with Multiple Retrievers**

* **Approach:**

  * Agent 2 is an LLM-powered reasoning agent.
  * Has access to multiple retriever tools (Billing, Technical, Account, Product, Feedback, Orders, Compliance, General).
  * Always queries the KB suggested by Agent 1’s classification.
  * Always also queries the **FAQ/General KB**.
  * Dynamically decides if additional KBs are needed.
  * Can merge results from multiple retrievers.
* **Pros:**

  * Flexible and adaptive.
  * Handles tickets spanning multiple domains.
  * Ensures general guidelines (FAQ/Policy) are always considered.
* **Cons:**

  * More complex to implement.
  * Higher compute cost (multiple retriever calls + reasoning step).
* **Example:**

  * Ticket: “I was double charged and now can’t log in.”
  * Agent 1 → Category: Billing & Payments.
  * Agent 2 (Option 2) → Queries Billing KB (refund), Account KB (login reset), FAQ KB (general refund policy).
  * Provides merged, richer context.

---

### Knowledge Base Design

* We maintain **8 KB retrievers** (aligned with the 8 ticket categories):

  1. Billing & Payments
  2. Technical Issues
  3. Account Management
  4. Product/Service Inquiry
  5. Feature Requests / Feedback
  6. Order & Delivery
  7. Compliance / Legal / Security
  8. General / FAQ

---

### Current Decision

* We will move forward with **Option 2: Reasoning Agent with Multiple Retrievers**, because:

  * It balances determinism (category hint from Agent 1) with flexibility (multi-domain retrieval).
  * It avoids missing context in multi-faceted tickets.
  * It scales better to real-world support environments.

---

### Things to Keep in Mind

1. **Classification is a hint, not a hard constraint** → Agent 2 should still consider other KBs when necessary.
2. **Always include General/FAQ retriever** in retrieval.
3. **Design structured outputs** (context chunks + metadata) so downstream agents can consume easily.
4. **Optimize cost** by limiting retriever calls when unnecessary.

---

### Next Focus

* Implement Agent 2 as a reasoning agent with multiple retriever tools.
* Need some starter corpus or some initial dummy/real set of data for each KB retrievers (data for each KB need not be very large in size but enough to be used to create vector stores and retrieve relevant chunks).
* Define prompts/guidelines so Agent 2:
  * Queries the primary KB (based on Agent 1 classification).
  * Always queries FAQ KB.
  * Dynamically queries additional KBs as needed.
  * Outputs a merged set of context documents for reply drafting and action suggestion.

okay so now first help me in creating the agent with multiple retrievers as tools and then we will work on the prompt for it.
For creating the retrievers, we need some dummy/real set of data for each category. What can we use for that?