import json
import re
import logging

logger = logging.getLogger(__name__)

def extract_json_from_response(response_text):
    """
    Attempts to extract valid JSON from a potentially messy LLM response
    
    Args:
        response_text (str): The raw text response from an LLM
        
    Returns:
        dict: Parsed JSON object, or None if parsing fails
    """
    # Try to extract JSON directly
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON between backticks (common for code blocks)
    try:
        json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Try to extract JSON between curly braces (most JSON objects)
    try:
        json_match = re.search(r'({.*})', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Try to fix common formatting issues that might cause JSON parsing to fail
    try:
        # Replace single quotes with double quotes
        fixed_str = response_text.replace("'", '"')
        # Fix malformed booleans
        fixed_str = re.sub(r':\s*True\b', ': true', fixed_str)
        fixed_str = re.sub(r':\s*False\b', ': false', fixed_str)
        # Fix trailing commas
        fixed_str = re.sub(r',\s*}', '}', fixed_str)
        fixed_str = re.sub(r',\s*]', ']', fixed_str)
        
        # Try to extract a JSON object with the fixes
        json_match = re.search(r'({.*})', fixed_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # If all attempts fail, log the issue and return None
    logger.error("Failed to extract JSON from response")
    return None