# **Context Document – Alternative Workflow with Pre-Action Handling**

## 🎯 Purpose

This document outlines a future design extension of the customer support multi-agent workflow, where factual or customer-specific tickets requiring database queries or account actions are handled **before drafting the reply**. This ensures the system can support both *informational* and *factual* queries seamlessly.

---

## 🔄 Workflow Overview

1. **Agent 1 – Ticket Classifier**

   * Categorizes the ticket into predefined categories (e.g., Billing, Account, Technical).
   * Assigns urgency/severity.

2. **Agent 2 – Retrieval & Context Builder**

   * Retrieves knowledge from category-specific, general, and optionally overlapping retrievers.
   * Consolidates into a stitched narrative.
   * **Outputs a `data_flag`:**

     * `false` → All info available from KB.
     * `true` → Reply requires factual/customer-specific data (e.g., account status, invoice).

3. **Agent 3 – Drafting Agent**

   * If `data_flag = false`: Drafts reply normally using provided context.
   * If `data_flag = true`: Drafts a *preliminary* or *placeholder* reply, noting that factual information is missing and must be fetched first.

4. **Agent 4 – Action Suggester**

   * Suggests actions based on the ticket and `data_flag`.
   * Examples: `fetch_account_info`, `fetch_invoice(order_id)`, `reset_password`, `check_refund_status`.

5. **HITL (Human-in-the-Loop)**

   * Approves or modifies suggested actions.
   * If `data_flag = false`: Also validates drafted reply.
   * If `data_flag = true`: Confirms whether factual info is indeed required, or overrides.

6. **Agent 5 – Action Executor**

   * Executes approved actions (or dummy implementations in demo).
   * Returns action results (e.g., account info, payment status).

7. **Loopback to Agent 3 (if `data_flag = true`)**

   * With updated action results + ticket text + retrieved context, Agent 3 re-drafts a **final reply**.
   * Ensures reply is accurate, grounded, and complete.

---

## 🔀 Flow Summary

* **Informational ticket (policy, FAQ, guidelines):**
  Agent 2 → Agent 3 drafts reply → Agent 4 suggests optional actions → HITL → Agent 5 (if any).
  *No loop needed.*

* **Factual ticket (requires lookup/action first):**
  Agent 2 raises `data_flag = true` → Agent 4 suggests required action → HITL → Agent 5 executes → Agent 3 drafts final reply with new info.
  *Loop ensures completeness before customer-facing output.*

---

## 📌 Benefits

* Extends coverage from **informational** to **factual, customer-specific** tickets.
* Introduces **flag-based branching** for clean separation of flows.
* Keeps HITL as control point for both **action approval** and **flag verification**.
* Flexible enough for future **API/DB integration** or simulated actions.

---
