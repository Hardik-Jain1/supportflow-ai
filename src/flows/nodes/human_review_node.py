from flows.state.ticket_state import TicketState
from utils.config import config

async def decide_human_review(state: TicketState) -> TicketState:
    if config.force_human_review:
        state.needs_review = True
    else:
        risky_present = any(p.action in config.risky_actions for p in state.actions)
        low_conf_reply = state.reply_conf < config.high_confidence
        low_conf_category = state.category_conf < config.high_confidence
        state.needs_review = risky_present or low_conf_reply or low_conf_category
    return state

async def human_review_node(state: TicketState) -> TicketState:
    if not state.needs_review:
        return state
    
    # Show current state to human reviewer
    print("\n" + "="*config.separator_length)
    print("HUMAN REVIEW REQUIRED")
    print("="*config.separator_length)
    ticket_preview = state.ticket_text[:config.max_ticket_preview_length]
    if len(state.ticket_text) > config.max_ticket_preview_length:
        ticket_preview += "..."
    print(f"Ticket: {ticket_preview}")
    print(f"Category: {state.category} (confidence: {state.category_conf:.{config.display_confidence_decimals}f})")
    print(f"Urgency: {state.urgency} (confidence: {state.urgency_conf:.{config.display_confidence_decimals}f})")
    print(f"\nProposed Reply:\n{state.reply_draft}")
    
    print(f"\nProposed Actions:")
    for i, action in enumerate(state.actions):
        risk_status = "RISKY" if action.action in config.risky_actions else "SAFE"
        print(f"  {i+1}. {action.action} [{risk_status}]")
        print(f"     Params: {action.params}")
        print(f"     Rationale: {action.rationale}")
    
    print("\n" + "-"*config.separator_length)
    
    # Get human input for actions
    for i, action in enumerate(state.actions):
        while True:
            approve = input(f"Approve action '{action.action}'? (y/n/skip): ").lower().strip()
            if approve == 'y':
                action.approved = True
                break
            elif approve == 'n':
                action.approved = False
                break
            elif approve == 'skip':
                action.approved = None
                break
            else:
                print("Please enter 'y', 'n', or 'skip'")
    
    # Get feedback for reply
    while True:
        reply_feedback = input("\nReply feedback (press Enter to approve, 'r' to request revision): ").strip()
        if reply_feedback == '':
            # Approved as-is
            state.human_feedback = None
            break
        elif reply_feedback.lower() == 'r':
            while True:
                revision_type = input("Enter 'manual' to provide your own draft, or 'auto' for AI redraft with feedback: ").strip().lower()
                if revision_type == 'manual':
                    new_draft = input("Enter your revised reply: ").strip()
                    if new_draft:
                        state.reply_draft = new_draft
                        state.human_feedback = None  # No feedback needed for manual draft
                    break
                elif revision_type == 'auto':
                    revision_request = input("Enter revision instructions: ").strip()
                    state.human_feedback = revision_request  # Set feedback for AI redraft
                    state.redraft_count += 1
                    break
                else:
                    print("Invalid option. Enter 'manual' to provide your own draft, or 'auto' for AI redraft with feedback: ")
            break
        else:
            print("Invalid option. Press Enter to approve or 'r' to request revision")
    
    print("="*config.separator_length + "\n")
    return state