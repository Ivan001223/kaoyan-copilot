import json
import re
from typing import Any, Dict, Union, List

def parse_json_from_llm(content: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Parses JSON from LLM output, handling common issues like Markdown code blocks,
    <think> tags, and minor formatting errors.
    """
    # 1. Remove <think> tags if present
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    # 2. Remove Markdown code blocks
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```', '', content)
    
    # 3. Strip whitespace
    content = content.strip()
    
    # 4. Parse JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object if mixed with text
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Attempt to fix escaped backslashes in the extracted JSON string
                json_str_fixed = json_str.replace('\\', '\\\\')
                try:
                    return json.loads(json_str_fixed)
                except:
                    pass
        
        # If no JSON object found, check for list
        match_list = re.search(r'\[.*\]', content, re.DOTALL)
        if match_list:
            json_str = match_list.group(0)
            try:
                return json.loads(json_str)
            except:
                pass

        raise ValueError(f"Could not parse JSON from content: {content[:100]}...")
