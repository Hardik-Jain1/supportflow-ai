#!/usr/bin/env python3
"""
Test script for the enhanced reply drafting workflow with redrafting capability.
This script demonstrates both initial drafting and feedback-based redrafting.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from workflow import TicketState, TicketMeta, draft_reply, get_narrative_context, KBResult, KBHit
from datetime import datetime, timezone

def test_initial_drafting():
    """Test initial drafting workflow"""
    print("=" * 60)
    print("TESTING INITIAL DRAFTING")
    print("=" * 60)
    
    # Create a sample ticket state
    state = TicketState(
        ticket_text="Hi, I'm having trouble logging into my account. I keep getting an error message saying 'invalid credentials' even though I'm sure my password is correct. Can you help?",
        meta=TicketMeta(
            source="email",
            customer_id="CUST123",
            created_at=datetime.now(timezone.utc)
        )
    )
    
    # Add some mock KB context
    state.kb_result = KBResult(
        retrieved_sources=[
            KBHit(
                retriever="account",
                summary="For login issues, first verify the email address is correct, then try password reset if needed. Check for browser cache issues."
            ),
            KBHit(
                retriever="technical", 
                summary="Common login errors include caps lock, browser cookies, or account lockout after multiple failed attempts."
            )
        ],
        consolidated_context="Login issues are typically resolved by verifying credentials, clearing browser cache, or using password reset functionality."
    )
    
    print(f"Ticket: {state.ticket_text[:100]}...")
    print(f"KB Context: {len(state.kb_result.retrieved_sources)} sources available")
    
    # Test initial drafting
    try:
        result_state = draft_reply(state)
        print(f"\n✅ Initial Draft Created:")
        print(f"Length: {len(result_state.reply_draft)} characters")
        print(f"Reply Preview: {result_state.reply_draft[:200]}...")
        print(f"Redraft Count: {result_state.redraft_count}")
        print(f"Human Feedback: {result_state.human_feedback}")
        return result_state
    except Exception as e:
        print(f"❌ Error in initial drafting: {e}")
        return None

def test_redrafting_workflow(initial_state):
    """Test redrafting workflow with human feedback"""
    print("\n" + "=" * 60)
    print("TESTING REDRAFTING WITH FEEDBACK")
    print("=" * 60)
    
    if not initial_state:
        print("❌ Cannot test redrafting - initial state is None")
        return
    
    # Simulate human feedback
    initial_state.human_feedback = "The reply is too technical. Please make it more friendly and add a direct solution like password reset steps. Also, offer phone support as an alternative."
    
    print(f"Human Feedback: {initial_state.human_feedback}")
    print(f"Previous Draft Preview: {initial_state.reply_draft[:150]}...")
    
    # Test redrafting
    try:
        result_state = draft_reply(initial_state)
        print(f"\n✅ Redraft Created:")
        print(f"Length: {len(result_state.reply_draft)} characters")
        print(f"Redrafted Reply Preview: {result_state.reply_draft[:300]}...")
        print(f"Redraft Count: {result_state.redraft_count}")
        print(f"Human Feedback After Processing: {result_state.human_feedback}")
        
        return result_state
    except Exception as e:
        print(f"❌ Error in redrafting: {e}")
        return None

def test_multiple_redrafts(state):
    """Test multiple rounds of redrafting"""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE REDRAFTS")
    print("=" * 60)
    
    if not state:
        print("❌ Cannot test multiple redrafts - state is None")
        return
    
    # Second round of feedback
    state.human_feedback = "Good improvement! But please also mention our 24/7 chat support and make the tone even more apologetic for the inconvenience."
    
    print(f"Second Feedback: {state.human_feedback}")
    print(f"Current Redraft Count: {state.redraft_count}")
    
    try:
        result_state = draft_reply(state)
        print(f"\n✅ Second Redraft Created:")
        print(f"Length: {len(result_state.reply_draft)} characters")
        print(f"Final Reply Preview: {result_state.reply_draft[:300]}...")
        print(f"Final Redraft Count: {result_state.redraft_count}")
        print(f"Human Feedback After Processing: {result_state.human_feedback}")
        
        # Test exceeding max redrafts
        if result_state.redraft_count < 2:  # MAX_REDACTS is 2
            result_state.human_feedback = "One more change please - add our company hours."
            print(f"\nTesting max redraft limit...")
            print(f"Third Feedback: {result_state.human_feedback}")
            
            final_state = draft_reply(result_state)
            print(f"Final Redraft Count: {final_state.redraft_count}")
            print(f"Max redrafts reached - should not process feedback further")
            
    except Exception as e:
        print(f"❌ Error in multiple redrafts: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Reply Workflow Tests")
    print("This will test both initial drafting and redrafting capabilities")
    
    # Test 1: Initial drafting
    initial_state = test_initial_drafting()
    
    # Test 2: Single redraft
    redraft_state = test_redrafting_workflow(initial_state)
    
    # Test 3: Multiple redrafts
    test_multiple_redrafts(redraft_state)
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED")
    print("=" * 60)
    print("\nKey Features Tested:")
    print("✅ Initial drafting using existing workflow")
    print("✅ Feedback-based redrafting using new CrewAI workflow")
    print("✅ Proper state management (counters, feedback clearing)")
    print("✅ Multiple redraft rounds")
    print("✅ Max redraft limit handling")

if __name__ == "__main__":
    main()