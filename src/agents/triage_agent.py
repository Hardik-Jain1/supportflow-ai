import litellm
import os
from dotenv import load_dotenv
from typing import Dict, Optional
import re
load_dotenv()

with open('config/prompts/agent_1/user_prompt.txt', 'r') as file:
    user_prompt = file.read()

with open('config/prompts/agent_1/system_prompt.txt', 'r') as file:
    system_prompt = file.read()

def triage_agent(ticket: str, model= "gemini/gemini-2.5-flash") -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.replace("{TICKET}", ticket)}
    ]
    output = litellm.completion(model=model,
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
        result_match = re.search(r'<result>(.*?)</result>', content, re.DOTALL)
        if not result_match:
            return None
            
        xml_content = result_match.group(1)
        
        # Extract each field using regex
        fields = {}
        
        category_match = re.search(r'<category>(.*?)</category>', xml_content, re.DOTALL)
        if category_match:
            value = category_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["category"] = value
        
        reason_cat_match = re.search(r'<reason_for_category>(.*?)</reason_for_category>', xml_content, re.DOTALL)
        if reason_cat_match:
            value = reason_cat_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["reason_for_category"] = value
        
        conf_cat_match = re.search(r'<confidence_for_category>(.*?)</confidence_for_category>', xml_content, re.DOTALL)
        if conf_cat_match:
            value = conf_cat_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["confidence_for_category"] = value
        
        urgency_match = re.search(r'<urgency>(.*?)</urgency>', xml_content, re.DOTALL)
        if urgency_match:
            value = urgency_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["urgency"] = value
        
        reason_urg_match = re.search(r'<reason_for_urgency_level>(.*?)</reason_for_urgency_level>', xml_content, re.DOTALL)
        if reason_urg_match:
            value = reason_urg_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["reason_for_urgency_level"] = value
        
        conf_urg_match = re.search(r'<confidence_for_urgency_level>(.*?)</confidence_for_urgency_level>', xml_content, re.DOTALL)
        if conf_urg_match:
            value = conf_urg_match.group(1).strip()
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            fields["confidence_for_urgency_level"] = value
        
        return fields if len(fields) == 6 else None
        
    except Exception as e:
        print(f"Error parsing triage result: {e}")
        return None