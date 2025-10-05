import asyncio
from flows.triage_workflow import create_triage_workflow
from flows.state.ticket_state import TicketState, TicketMeta
from datetime import datetime

async def main():
    """Main entry point for the customer support triage agent."""
    # Create workflow
    triage_flow = create_triage_workflow()
    
    # Get ticket text from user
    ticket_text = input("Enter ticket text: ")
    
    # Create initial state with metadata
    initial_state = TicketState(
        ticket_text=ticket_text,
        meta=TicketMeta(
            source="cli",
            created_at=datetime.now()
        )
    )
    
    # Run workflow asynchronously
    print("\nProcessing ticket...")
    result = await triage_flow.ainvoke(initial_state)
    
    print("\n" + "="*50)
    print("Workflow completed!")
    print("="*50)
    print(f"Final state: Posted={result['posted']}, Escalated={result['escalated']}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
