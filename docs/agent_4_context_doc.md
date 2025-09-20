# **Agent 4 Context Document – Action Suggester**

## 🎯 Purpose

Agent 4 is responsible for suggesting follow-up **actions** based on the ticket, retrieved context (from Agent 2), and drafted reply (from Agent 3). Its role is not to execute actions but to propose them in a structured manner that can be reviewed by a Human-in-the-Loop (HITL) and then passed on to Agent 5 (Action Executor).

---

## 🔑 Role in the Workflow

* Works **after Agent 3** has drafted the reply.
* Interprets both the **ticket details** and the **consolidated knowledge** provided.
* Suggests **next best actions** that should be taken to resolve the ticket or assist the customer.
* Ensures actions are aligned with the drafted reply and the ticket’s intent.
* Outputs structured recommendations for HITL review.

---

## 📌 Key Responsibilities

1. **Interpret Context:**

   * Analyze the drafted reply, ticket text, and retrieved knowledge.
   * Detect whether further action is needed beyond sending a reply.

2. **Action Suggestion:**

   * Suggest possible actions (with arguments/parameters where needed).
   * Each action should have:

     * `name` (action identifier)
     * `description` (why it is suggested)
     * `arguments` (e.g., `user_id`, `order_id` if applicable)

3. **Structured Output:**

   * Output must be **structured and machine-readable** (e.g., JSON or XML).
   * Should clearly distinguish between: suggested action(s), reasoning, and required parameters.

4. **HITL Alignment:**

   * Keep actions in a **suggestion mode only**.
   * HITL will approve, reject, or modify the suggested actions.

---

## 📋 Example Action Catalog (Initial Scope)

To demonstrate the workflow without requiring real backend APIs, we define a **dummy catalog** of possible actions:

1. `create_support_ticket(issue_type, details)`
2. `issue_refund(order_id, amount)`
3. `fetch_invoice(order_id)`
4. `reset_password(user_id)`
5. `escalate_to_human(reason)`
6. `apply_late_fee_waiver(user_id, invoice_id)`

*(Dummy implementations will be used for testing and demonstration.)*

---

## ⚙️ Input & Output

**Input:**

* Ticket text
* Consolidated context (from Agent 2)
* Drafted reply (from Agent 3) [Optional]

**Output (XML format):**

```xml
```xml
<result>
  <suggested_actions>
    <action name="[action_name]">
      <arguments>
        <arg key="[arg_name]">[value or placeholder]</arg>
        ...
      </arguments>
    </action>
    ...
  </suggested_actions>
</result>
```
```

---

## 🔀 Relation to Other Agents

* **Agent 2** → Provides factual and knowledge base context.
* **Agent 3** → Drafts the customer-facing reply.
* **Agent 4** → Suggests backend/support actions aligned with reply.
* **HITL** → Approves/rejects actions.
* **Agent 5** → Executes approved actions.

---

## ✅ Benefits

* Keeps **reply generation** and **action suggestion** logically separate.
* Provides a **traceable, auditable suggestion log**.
* Ensures **HITL control** before execution.
* Flexible to integrate **real APIs** in the future.

---
