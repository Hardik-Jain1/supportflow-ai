import litellm
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from typing import Dict, Optional
load_dotenv()

with open('config/prompts/agent_1/user_prompt.txt', 'r') as file:
    user_prompt = file.read()

with open('config/prompts/agent_1/system_prompt.txt', 'r') as file:
    system_prompt = file.read()

def triage_agent(ticket: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.replace("{TICKET}", ticket)}
    ]
    output = litellm.completion(model="gemini/gemini-2.5-flash",
                                messages=messages,
                                temperature=0,
                                top_p=0.5,
                                max_tokens=2048)
    
    return output


def parse_triage_result(llm_output: str) -> Optional[Dict[str, str]]:
    """
    Parse XML output from the triage agent.
    
    Args:
        llm_output: String containing the LLM response with XML
        
    Returns:
        Dictionary with parsed values or None if parsing fails
    """
    try:
        # Extract content from the completion response
        content = llm_output.strip()
        
        # Find the XML portion
        start_tag = "<result>"
        end_tag = "</result>"
        start_idx = content.find(start_tag)
        end_idx = content.find(end_tag) + len(end_tag)
        
        if start_idx == -1 or end_idx == -1:
            return None
            
        xml_content = content[start_idx:end_idx]
        
        # Parse XML
        root = ET.fromstring(xml_content)
        
        return {
            "category": root.find("category").text.strip(),
            "reason_for_category": root.find("reason_for_category").text.strip(),
            "confidence_for_category": root.find("confidence_for_category").text.strip(),
            "urgency": root.find("urgency").text.strip(),
            "reason_for_urgency_level": root.find("reason_for_urgency_level").text.strip(),
            "confidence_for_urgency_level": root.find("confidence_for_urgency_level").text.strip()
        }
    except Exception:
        return None
