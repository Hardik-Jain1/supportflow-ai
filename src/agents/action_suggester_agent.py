import litellm
import os
from dotenv import load_dotenv
from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate
import re
load_dotenv()

def read_file_content(file_path: str) -> str:
    """Read and return the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()
    
def action_suggester_agent(inputs, model= "gemini/gemini-2.5-flash") -> str:
    user_prompt_template = read_file_content('config/prompts/agent_4/user_prompt.txt')
    system_prompt_template = read_file_content('config/prompts/agent_4/system_prompt.txt')
    action_catalog = read_file_content('config/prompts/agent_4/action_catalog.txt')

    user_prompt_template = PromptTemplate(
        template=user_prompt_template,
        input_variables=[
            "ticket_text",
            "category",
            "urgency",
            "narrative_context",
            "action_catalog",
        ]
    )

    user_prompt = user_prompt_template.format(
        ticket_text=inputs.get("ticket_text", ""),
        category=inputs.get("category", ""),
        urgency=inputs.get("urgency", ""),
        narrative_context=inputs.get("narrative_context", ""),
        action_catalog=action_catalog
    )

    messages = [
        {"role": "system", "content": system_prompt_template},
        {"role": "user", "content": user_prompt}
    ]

    output = litellm.completion(model=model,
                                messages=messages,
                                temperature=0,
                                top_p=0.5,
                                max_tokens=4096)

    return output.choices[0].message.content


def parse_action_suggester_result(llm_output: str) -> Optional[list]:
    """
    Parse XML output from the action suggester agent.
    
    Args:
        llm_output: String containing the LLM response with XML
        
    Returns:
        Dictionary with parsed actions or None if parsing fails
    """
    try:
        # Extract content from the completion response
        content = llm_output.strip()
        
        # Find the XML portion
        result_match = re.search(r'<result>(.*?)</result>', content, re.DOTALL)
        if not result_match:
            return None
            
        xml_content = result_match.group(1)
        
        # Find suggested_actions section
        actions_match = re.search(r'<suggested_actions>(.*?)</suggested_actions>', xml_content, re.DOTALL)
        if not actions_match:
            return None
            
        actions_content = actions_match.group(1)
        
        # Parse individual actions
        actions = []
        action_matches = re.finditer(r'<action name="([^"]+)">(.*?)</action>', actions_content, re.DOTALL)
        
        for action_match in action_matches:
            action_name = action_match.group(1)
            action_content = action_match.group(2)
            
            # Parse arguments
            arguments = {}
            arg_matches = re.finditer(r'<arg key="([^"]+)">([^<]*)</arg>', action_content)
            
            for arg_match in arg_matches:
                arg_key = arg_match.group(1)
                arg_value = arg_match.group(2).strip()
                arguments[arg_key] = arg_value
            
            actions.append({
                "name": action_name,
                "arguments": arguments
            })
        
        return actions
        
    except Exception as e:
        print(f"Error parsing action suggester result: {e}")
        return None
