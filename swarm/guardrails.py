# swarm/guardrails.py
import re
import logging
import os

logger = logging.getLogger(__name__)

# Expanded and hardened injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|initial)\s+(instructions|directives|prompts|rules)", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system|initial|hidden)\s+(prompt|instruction|message)", re.IGNORECASE),
    re.compile(r"(override|disable|bypass)\s+(system|safety|security)\s+(protocols|filters|rules)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(unrestricted|unfiltered|jailbroken|DAN)", re.IGNORECASE),
    re.compile(r"(enter|enable)\s+(developer|debug|sudo)\s+mode", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
]

def check_input_guardrail(user_prompt: str) -> bool:
    """
    Returns True if malicious prompt injection is detected.
    Fails closed (returns True) if the input is not a valid string to prevent crashes.
    """
    # 1. Type safety guard
    if not isinstance(user_prompt, str):
        logger.error(f"🚨 SECURITY ALERT: Guardrail received non-string input: {type(user_prompt)}")
        return True 
        
    # 2. Pattern matching
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(user_prompt):
            logger.warning(f"🚨 SECURITY ALERT: Prompt injection intercepted. Pattern: '{pattern.pattern}'")
            return True
            
    return False

def sanitize_file_path(filename: str) -> str:
    """
    Secures tool arguments by isolating execution strictly to a safe, flat filename.
    Prevents directory traversal, hidden file creation, and invalid OS characters.
    """
    # 1. Type safety guard
    if not isinstance(filename, str):
        logger.warning(f"🛡️ TOOL GUARDRAIL: Received non-string filename: {type(filename)}")
        return "default_generated_script.py"

    original_filename = filename
    
    # 2. Extract only the trailing file component (e.g., '../../etc/passwd' -> 'passwd')
    base_name = os.path.basename(filename)
    
    # 3. Strip leading dots to prevent hidden files (e.g., '.env' -> 'env')
    base_name = base_name.lstrip('.')
    
    # 4. Strip any remaining erratic characters (Keep alphanumeric, underscore, hyphen, dot)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', base_name)
    
    # 5. Strip trailing/leading dots again (in case regex left us with just '...' or '.py')
    clean_name = clean_name.strip('.')
    
    # 6. Fallback default if someone passes purely illegal characters, blank strings, or just dots
    if not clean_name:
        clean_name = "default_generated_script.py"
        
    # 7. Log using the standard logger, not print()
    if clean_name != original_filename:
        logger.info(f"🛡️ TOOL GUARDRAIL: Sanitized risky filename '{original_filename}' -> '{clean_name}'")
        
    return clean_name