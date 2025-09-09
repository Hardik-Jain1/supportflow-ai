## Agent 3 Context: Reply Generation Crew

### Purpose

Agent 3 is responsible for generating customer-facing replies for support tickets. It operates as a **Crew** of two specialized agents rather than a single monolithic one. This ensures separation of concerns: one agent focuses on factual accuracy and content, while the other ensures professionalism, tone, and formatting.

### Input

* **Ticket text** (classified in Agent 1).
* **Narrative context**: A stitched explanation with inline citations derived from Agent 2’s XML output. This is transformed into a clean, readable form so that Agent 3 does not need to parse XML.

### Crew Design

1. **Drafting Agent (Content Drafter)**

   * **Role**: Generate the first draft of the reply.
   * **Focus**: Accuracy, completeness, covering all relevant information from the narrative.
   * **Tone**: Neutral and factual; does not need to worry about customer empathy or stylistic refinement.
   * **Input**: Ticket text + narrative context.
   * **Output**: Draft reply (factual, clear, comprehensive).

2. **Tone & Format Agent (Refiner)**

   * **Role**: Refine and polish the draft reply.
   * **Focus**: Ensure customer-friendly tone, professionalism, and readability.
   * **Tasks**: Add empathy, polite phrasing, proper greetings/closings, formatting (paragraphs, bullets if needed).
   * **Constraint**: Must preserve all factual content from the draft (no omissions, no hallucinations).
   * **Input**: Draft reply.
   * **Output**: Final polished reply ready for human approval or direct sending.

### Flow

1. Narrative context (from Agent 2 XML → stitched narrative) + ticket text → **Drafting Agent**.
2. Draft reply → **Tone & Format Agent**.
3. Final polished reply → either human-in-the-loop (approval/editing) or posted directly to the ticketing system.

### Why Two Agents Instead of More?

* No parser agent is needed: XML from Agent 2 is already pre-processed into narrative form.
* No separate final reply agent is needed: the Refiner already delivers the final output.
* Keeps the design modular but lightweight.
* Still extensible: later we can add compliance or localization agents if needed.

### Key Instructions to Keep in Mind

* Drafting Agent must stay **strictly factual** and base answers only on the given context.
* Refiner Agent must stay **strictly stylistic**, ensuring tone and format, without altering meaning.
* All outputs must be clear, customer-ready, and easily auditable by humans.
