# swarm/guardrails.py
import re
import logging
import os

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system|initial)\s+(prompt|instruction)", re.IGNORECASE),
    re.compile(r"override\s+(system|safety)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(unrestricted|unfiltered|jailbroken)", re.IGNORECASE),
]

def check_input_guardrail(user_prompt: str) -> bool:
    """Returns True if malicious prompt injection is detected."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(user_prompt):
            logger.warning(f"🚨 SECURITY ALERT: Prompt injection intercepted: {pattern.pattern}")
            return True
    return False

def sanitize_file_path(filename: str) -> str:
    """
    Secures tool arguments by isolating execution strictly to the local base filename.
    """
    # 1. Extract only the trailing file component (e.g., '../../etc/passwd' -> 'passwd')
    base_name = os.path.basename(filename)
    
    # 2. Strip any remaining erratic characters
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', base_name)
    
    # 3. Fallback default if someone passes purely illegal characters or blank strings
    if not clean_name or clean_name in (".", ".."):
        clean_name = "default_generated_script.py"
        
    if clean_name != filename:
        print(f"🛡️ TOOL GUARDRAIL: Sanitized risky filename '{filename}' -> '{clean_name}'")
        
    return clean_name