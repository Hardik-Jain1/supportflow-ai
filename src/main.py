from flows.triage_workflow import create_triage_workflow
from flows.state.ticket_state import TicketState

def main():
    """Main entry point for the customer support triage agent."""
    # Create workflow
    triage_flow = create_triage_workflow()
    
    # Example usage
    if __name__ == "__main__":
        ticket_text = input("Enter ticket text: ")
        initial_state = TicketState(ticket_text=ticket_text)
        
        # Run workflow
        result = triage_flow.invoke(initial_state)
        
        print("\nWorkflow completed!")
        print(f"Final state: Posted={result["posted"]}, Escalated={result["escalated"]}")

if __name__ == "__main__":
    main()