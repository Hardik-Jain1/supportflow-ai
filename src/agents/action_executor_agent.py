import re
from typing import Dict, Any, List
import utils.actions as actions


def action_executor_agent(actions_parsed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute parsed actions using functions from actions.py.
    Returns list of dict results.
    """
    results = []
    for action in actions_parsed:
        name = action["name"]
        args = action["arguments"]

        # Map action name to function in actions.py
        func = getattr(actions, name, None)

        if not func:
            results.append({
                "action": name,
                "status": "error",
                "details": f"No implementation found for action '{name}'."
            })
            continue

        try:
            result = func(**args)
            results.append(result)
        except Exception as e:
            results.append({
                "action": name,
                "status": "error",
                "details": str(e)
            })

    return results

