from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
import json

mcp = FastMCP("action_executor")

@mcp.tool()
def initiate_refund(order_id: str, amount: str, reason: str) -> str:
    """Initiate a refund for an order."""
    result = {
        "action": "initiate_refund",
        "status": "success",
        "details": f"Refund of {amount} initiated for order {order_id}. Reason: {reason}."
    }
    return json.dumps(result)

@mcp.tool()
def check_order_status(order_id: str) -> str:
    """Check the status of an order."""
    dummy_statuses = ["Processing", "Shipped", "Delivered", "Delayed"]
    simulated_status = dummy_statuses[hash(order_id) % len(dummy_statuses)]
    result = {
        "action": "check_order_status",
        "status": "success",
        "details": f"Order {order_id} is currently: {simulated_status}."
    }
    return json.dumps(result)

@mcp.tool()
def reset_password(account_id: str, delivery_method: str) -> str:
    """Reset password for an account."""
    result = {
        "action": "reset_password",
        "status": "success",
        "details": f"Password reset link sent to account {account_id}."
    }
    return json.dumps(result)

@mcp.tool()
def update_account_info(account_id: str, field: str, new_value: str) -> str:
    """Update account information."""
    result = {
        "action": "update_account_info",
        "status": "success",
        "details": f"Account {account_id} updated: {field} changed to '{new_value}'."
    }
    return json.dumps(result)

@mcp.tool()
def create_support_ticket(issue_summary: str, urgency: str, related_category: str) -> str:
    """Create a support ticket."""
    simulated_ticket_id = f"TCKT-{abs(hash(issue_summary)) % 10000}"
    result = {
        "action": "create_support_ticket",
        "status": "success",
        "details": f"Support ticket {simulated_ticket_id} created ({related_category}, urgency={urgency}). Description: {issue_summary}"
    }
    return json.dumps(result)

@mcp.tool()
def no_action_required(note: str = "No system action needed.") -> str:
    """Mark that no action is required."""
    result = {
        "action": "no_action_required",
        "status": "success",
        "details": note
    }
    return json.dumps(result)

if __name__ == "__main__":
    mcp.run(transport="stdio")
