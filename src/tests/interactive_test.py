#!/usr/bin/env python3
"""
Interactive test for the enhanced reply drafting workflow.
This allows you to manually test the redrafting process with custom feedback.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from workflow import TicketState, TicketMeta, draft_reply, KBResult, KBHit
from datetime import datetime, timezone

def create_sample_ticket_state():
    """Create a sample ticket state for testing"""
    ticket_options = {
        "1": {
            "text": "Hi, I'm having trouble logging into my account. I keep getting an error message saying 'invalid credentials' even though I'm sure my password is correct. Can you help?",
            "kb_sources": [
                KBHit(retriever="account", summary="For login issues, first verify the email address is correct, then try password reset if needed. Check for browser cache issues."),
                KBHit(retriever="technical", summary="Common login errors include caps lock, browser cookies, or account lockout after multiple failed attempts.")
            ],
            "context": "Login issues are typically resolved by verifying credentials, clearing browser cache, or using password reset functionality."
        },
        "2": {
            "text": "I was charged twice for my subscription this month. I only have one account but see two charges on my credit card. Please refund one of them immediately.",
            "kb_sources": [
                KBHit(retriever="billing", summary="Double billing can occur due to payment processing delays or account synchronization issues. Check payment history and issue refunds for duplicate charges."),
                KBHit(retriever="account", summary="Review account activity and payment methods to identify duplicate billing scenarios.")
            ],
            "context": "Double billing issues require investigation of payment history and potential refund processing for duplicate charges."
        },
        "3": {
            "text": "Your product stopped working after the latest update. The main feature I use daily is completely broken. This is very frustrating and I'm considering switching to a competitor.",
            "kb_sources": [
                KBHit(retriever="technical", summary="Product issues after updates may require rollback procedures or patch deployment. Escalate to technical team for urgent fixes."),
                KBHit(retriever="product", summary="Feature breakages should be prioritized based on user impact and business criticality.")
            ],
            "context": "Post-update issues require immediate technical attention and may need escalation to development team for resolution."
        }
    }
    
    print("Select a sample ticket to test:")
    for key, ticket in ticket_options.items():
        print(f"{key}. {ticket['text'][:80]}...")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in ticket_options:
            selected = ticket_options[choice]
            break
        print("Invalid choice. Please enter 1, 2, or 3.")
    
    state = TicketState(
        ticket_text=selected["text"],
        meta=TicketMeta(
            source="email",
            customer_id="CUST123",
            created_at=datetime.now(timezone.utc)
        )
    )
    
    state.kb_result = KBResult(
        retrieved_sources=selected["kb_sources"],
        consolidated_context=selected["context"]
    )
    
    return state

def interactive_test():
    """Run interactive testing session"""
    print("🚀 Interactive Reply Drafting Workflow Test")
    print("=" * 60)
    
    # Create sample ticket
    state = create_sample_ticket_state()
    
    print(f"\n📧 Selected Ticket:")
    print(f"Text: {state.ticket_text}")
    print(f"KB Sources: {len(state.kb_result.retrieved_sources)} available")
    
    while True:
        print("\n" + "-" * 50)
        print("CURRENT STATE:")
        print(f"Redraft Count: {state.redraft_count}")
        print(f"Has Feedback: {'Yes' if state.human_feedback else 'No'}")
        if state.reply_draft:
            print(f"Current Reply Length: {len(state.reply_draft)} characters")
            print(f"Reply Preview: {state.reply_draft[:200]}...")
        
        print("\nWhat would you like to do?")
        print("1. Generate initial draft (or redraft if feedback provided)")
        print("2. Provide feedback for redrafting")
        print("3. View full current reply")
        print("4. Reset and start over")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🔄 Generating reply...")
            try:
                state = draft_reply(state)
                print("✅ Reply generated successfully!")
                print(f"Reply Length: {len(state.reply_draft)} characters")
                print(f"Preview: {state.reply_draft[:300]}...")
            except Exception as e:
                print(f"❌ Error generating reply: {e}")
        
        elif choice == "2":
            if state.redraft_count >= 2:  # MAX_REDACTS
                print("⚠️  Maximum redraft limit reached. Cannot accept more feedback.")
                continue
                
            feedback = input("\n💬 Enter your feedback for redrafting: ").strip()
            if feedback:
                state.human_feedback = feedback
                print(f"✅ Feedback recorded: {feedback[:100]}...")
            else:
                print("❌ No feedback provided.")
        
        elif choice == "3":
            if state.reply_draft:
                print("\n📝 FULL CURRENT REPLY:")
                print("-" * 40)
                print(state.reply_draft)
                print("-" * 40)
            else:
                print("❌ No reply generated yet.")
        
        elif choice == "4":
            state = create_sample_ticket_state()
            print("✅ Reset complete. New ticket selected.")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")

def main():
    """Main function"""
    print("Choose test mode:")
    print("1. Interactive test (manual feedback)")
    print("2. Automated test (predefined scenarios)")
    
    while True:
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == "1":
            interactive_test()
            break
        elif choice == "2":
            # Import and run the automated test
            try:
                import tests.test_redrafting_workflow as test_redrafting_workflow
                test_redrafting_workflow.main()
            except ImportError:
                print("❌ Automated test file not found. Running interactive test instead.")
                interactive_test()
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()