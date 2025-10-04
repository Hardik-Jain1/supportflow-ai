from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from agents.triage_agent import triage_agent, parse_triage_result
from agents.kb_agent import build_retrievers_from_csvs, build_agent, parse_agent2_output_text, parse_agent2_output_json
from agents.reply_agent.crew import reply_agent, redraft_reply_agent
from agents.action_suggester_agent import action_suggester_agent, parse_action_suggester_result
from agents.action_executor_agent import action_executor_agent
from utils.helpers import get_narrative_context
from utils.config import config
import json

server = Server()

@server.agent(name="triage_agent")
async def agent_1(input: list[Message],
                       context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    An agent that triages customer inquiries based on their content.
    """
    input_text = str(input[0].parts[0].content)
    
    try:
        input_data = json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"triage_agent: Input is not valid JSON. Error: {e}. Input received: {input_text[:200]}")
    
    agent_1_output = triage_agent(input_data.get("ticket_text", ""), model=input_data.get("model", config.reply_model))
    agent_1_output_json = parse_triage_result(agent_1_output.choices[0].message.content)

    yield Message(parts=[MessagePart(content=json.dumps(agent_1_output_json))])

@server.agent(name="kb_agent")
async def agent_2(input: list[Message],
                       context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    An agent that retrieves relevant knowledge base articles based on the triage result.
    """    
    input_text = str(input[0].parts[0].content)
    
    try:
        input_data = json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"kb_agent: Input is not valid JSON. Error: {e}. Input received: {input_text[:200]}")
    
    kb_retrievers = build_retrievers_from_csvs()
    kb_agent = build_agent(kb_retrievers, model=config.kb_model)
    
    agent_output_xml = kb_agent.invoke({
        "ticket_text": input_data.get("ticket_text", ""),
        "category": input_data.get("category", "")
    })["output"]
    agent_parsed_json = parse_agent2_output_json(agent_output_xml)
    
    yield Message(parts=[MessagePart(content=json.dumps(agent_parsed_json))])

@server.agent(name="reply_agent")
async def agent_3(input: list[Message],
                       context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    An agent that generates a reply to the customer based on the triage result and knowledge base articles.
    """
    input_text = str(input[0].parts[0].content)
    
    try:
        input_data = json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"reply_agent: Input is not valid JSON. Error: {e}. Input received: {input_text[:200]}")
    
    if input_data.get("redraft", False):
        agent3_output = redraft_reply_agent(
            ticket=input_data.get("ticket_text"),
            context=input_data.get("context"),
            previous_draft=input_data.get("reply_draft"),
            human_feedback=input_data.get("human_feedback"),
            model=input_data.get("model", config.reply_model)
        )
    else:
        agent3_output = reply_agent(
            ticket=input_data.get("ticket_text", ""),
            context=input_data.get("context"),
            model=input_data.get("model", config.reply_model)
        )
    yield Message(parts=[MessagePart(content=agent3_output.raw)])

@server.agent(name="action_suggester_agent")
async def agent_4(input: list[Message],
                       context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    An agent that suggests actions based on the ticket and reply draft.
    """
    input_text = str(input[0].parts[0].content)
    
    try:
        input_data = json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"action_suggester_agent: Input is not valid JSON. Error: {e}. Input received: {input_text[:200]}")
    
    agent_4_input = {
        "ticket_text": input_data.get("ticket_text"),
        "category": input_data.get("category"),
        "urgency": input_data.get("urgency"),
        "narrative_context": input_data.get("narrative_context")
    }

    agent_4_output = action_suggester_agent(agent_4_input, model=input_data.get("model", config.action_suggester_model))
    agent_4_output_json = parse_action_suggester_result(agent_4_output)
    
    yield Message(parts=[MessagePart(content=json.dumps(agent_4_output_json))])

@server.agent(name="action_executor_agent")
async def agent_5(input: list[Message],
                       context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    An agent that executes approved actions.
    """
    input_text = str(input[0].parts[0].content)
    try:
        input_data = json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"action_executor_agent: Input is not valid JSON. Error: {e}. Input received: {input_text[:200]}")
    
    # Get actions list
    actions = input_data.get("actions", [])
    
    # Ensure arguments field is a dict (not a JSON string)
    for action in actions:
        if "arguments" in action and isinstance(action["arguments"], str):
            try:
                action["arguments"] = json.loads(action["arguments"])
            except json.JSONDecodeError:
                pass  # Keep as string if it's not valid JSON
    
    agent_5_output = action_executor_agent(actions)

    yield Message(parts=[MessagePart(content=json.dumps(agent_5_output))])

if __name__ == "__main__":
    server.run(port=8001)