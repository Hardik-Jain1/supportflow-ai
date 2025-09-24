from typing import Dict, Any

def initiate_refund(order_id, amount, reason) -> Dict[str, Any]:
    return {
        "action": "initiate_refund",
        "status": "success",
        "details": f"Refund of {amount} initiated for order {order_id}. Reason: {reason}."
    }


def check_order_status(order_id) -> Dict[str, Any]:
    # Dummy statuses for simulation
    dummy_statuses = ["Processing", "Shipped", "Delivered", "Delayed"]
    simulated_status = dummy_statuses[hash(order_id) % len(dummy_statuses)]
    return {
        "action": "check_order_status",
        "status": "success",
        "details": f"Order {order_id} is currently: {simulated_status}."
    }


def reset_password(account_id, delivery_method) -> Dict[str, Any]:
    return {
        "action": "reset_password",
        "status": "success",
        "details": f"Password reset link sent to account {account_id}."
    }


def update_account_info(account_id, field, new_value) -> Dict[str, Any]:
    return {
        "action": "update_account_info",
        "status": "success",
        "details": f"Account {account_id} updated: {field} changed to '{new_value}'."
    }


def create_support_ticket(issue_summary, urgency, related_category) -> Dict[str, Any]:
    simulated_ticket_id = f"TCKT-{abs(hash(issue_summary)) % 10000}"
    return {
        "action": "create_support_ticket",
        "status": "success",
        "details": f"Support ticket {simulated_ticket_id} created ({related_category}, urgency={urgency}). Description: {issue_summary}"
    }


def no_action_required(note="No system action needed.") -> Dict[str, Any]:
    return {
        "action": "no_action_required",
        "status": "success",
        "details": note
    }
