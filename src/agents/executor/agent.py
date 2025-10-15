from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import asyncio

async def execute_actions(actions_parsed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute parsed actions by calling MCP server tools.
    
    Args:
        actions_parsed: List of action dictionaries with 'name' and 'arguments'
        
    Returns:
        List of execution results
    """
    
    server_params = StdioServerParameters(
        command="python",
        args=["agents/executor/mcp_tools.py"]
    )
    
    results = []
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Execute each action individually
            for action in actions_parsed:
                name = action["name"]
                args = action["arguments"]
                
                try:
                    if name == "initiate_refund":
                        result = await session.call_tool(
                            "initiate_refund",
                            arguments=args
                        )
                    
                    elif name == "check_order_status":
                        result = await session.call_tool(
                            "check_order_status",
                            arguments=args
                        )
                    
                    elif name == "reset_password":
                        result = await session.call_tool(
                            "reset_password",
                            arguments=args
                        )
                    
                    elif name == "update_account_info":
                        result = await session.call_tool(
                            "update_account_info",
                            arguments=args
                        )
                    
                    elif name == "create_support_ticket":
                        result = await session.call_tool(
                            "create_support_ticket",
                            arguments=args
                        )
                    
                    elif name == "no_action_required":
                        result = await session.call_tool(
                            "no_action_required",
                            arguments=args
                        )
                    
                    else:
                        # Unknown action type
                        results.append({
                            "action": name,
                            "status": "error",
                            "details": f"Unknown action type: {name}"
                        })
                        continue
                    
                    # Parse the result from MCP tool
                    action_result = json.loads(result.content[0].text)
                    results.append(action_result)
                    
                except Exception as e:
                    results.append({
                        "action": name,
                        "status": "error",
                        "details": f"Error executing action: {str(e)}"
                    })
            
            return results
