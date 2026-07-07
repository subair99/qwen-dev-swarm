# orchestrator.py
import json
import re
import logging
from typing import Generator, Dict, Any, Optional
from config.settings import settings, get_llm_client
from sandbox import run_in_sandbox, parse_stderr
from swarm.agents import create_swarm_agents, create_agent, extract_code_from_markdown
from swarm.guardrails import guard_prompt, sanitize_file_path

logger = logging.getLogger(__name__)

# ==============================================================================
# 🛡️ ROBUST QA JSON PARSER (Fixes JSON Parsing Vulnerability)
# ==============================================================================
def parse_qa_feedback(raw_text: str) -> Dict[str, Any]:
    """
    Robustly parses the QA Analyst's response into a structured dictionary.
    Handles markdown wrapping, conversational text, and malformed JSON to prevent 
    infinite retry loops caused by LLM formatting quirks.
    """
    if not raw_text:
        return {"status": "FAIL", "error_summary": "Empty QA response", "failed_component": "Unknown", "remediation_hint": "No feedback provided."}

    # 1. Try direct parsing
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # 2. Extract from markdown blocks (```json ... ```)
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Extract by finding the first '{' and last '}'
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw_text[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass

    # 4. Heuristic Fallback (If all parsing fails, analyze text sentiment)
    logger.warning(f"QA JSON parsing failed. Using heuristic fallback. Raw text: {raw_text[:150]}...")
    lower_text = raw_text.lower()
    
    is_pass = any(word in lower_text for word in ["success", "passed", "looks good", "no errors", "perfect", "correct"])
    is_fail = any(word in lower_text for word in ["error", "failed", "exception", "fix", "bug", "traceback"])

    lines = raw_text.strip().split('\n')
    error_summary = lines[-1] if lines else "Unknown error"

    if is_pass and not is_fail:
        return {
            "status": "PASS",
            "error_summary": "None",
            "failed_component": "None",
            "remediation_hint": "Code looks good based on heuristic analysis."
        }
    else:
        return {
            "status": "FAIL",
            "error_summary": f"QA parsing failed, raw feedback: {error_summary[:100]}",
            "failed_component": "Unknown",
            "remediation_hint": "Review the raw QA feedback and fix potential issues."
        }


class QwenDevSwarmOrchestrator:
    def __init__(self, max_retries: int = 3, require_approval: bool = True):
        """
        Initializes the central multi-agent orchestrator.
        
        Args:
            max_retries: Hard limit for self-correction loops.
            require_approval: If True, mandates human review before ANY code execution.
        """
        self.max_retries = max_retries
        self.require_approval = require_approval # 🛡️ CRITICAL SECURITY FLAG
        
        self._file_path = "generated_script.py"
        self.state = {
            "current_blueprint": "",
            "file_path": self._file_path,
            "model_in_use": getattr(settings, "MODEL_NAME", "qwen3.7-max"),
            "history": []
        }
        
        self.swarm = create_swarm_agents()
        self._compiled_prompt_cache: Dict[str, str] = {}

    @property
    def file_path(self) -> str:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = sanitize_file_path(value)
        self.state["file_path"] = self._file_path

    def set_blueprint(self, blueprint: str) -> None:
        client = get_llm_client()
        guard_result = guard_prompt(blueprint, client=client, use_semantic_guard=True)
        
        if guard_result["blocked"]:
            raise ValueError(f"🚨 Security Guardrail: {guard_result['reason']}")
        
        self.state["current_blueprint"] = blueprint
        self._compiled_prompt_cache.pop(blueprint, None)

    def run_autonomous_generation(self, user_feature_request: str) -> str:
        if user_feature_request in self._compiled_prompt_cache:
            return self._compiled_prompt_cache[user_feature_request]
            
        meta_prompt_response = self.swarm["prompt_engineer"].call_llm(
            f"Generate a comprehensive, hardened system prompt to build this feature: {user_feature_request}"
        )
        self._compiled_prompt_cache[user_feature_request] = meta_prompt_response
        
        dynamic_coder = create_agent(name="Dynamic_Lead_Coder", instructions=meta_prompt_response)
        self.swarm["coder"] = dynamic_coder
        return meta_prompt_response

    def execute_self_correction_loop(
        self, 
        human_hint: Optional[str] = None, 
        approved_code: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Manages the self-correction loop.
        
        Args:
            human_hint: Provided by user if they rejected the previous code.
            approved_code: Provided by user if they approved the generated code. 
                           If provided, skips generation and goes straight to sandbox.
        """
        if not self.state.get("current_blueprint"):
            yield {"event": "system_start", "status": "FAILED", "active_agent": "System", "message": "No blueprint set."}
            return

        retry_count = 0
        qa_feedback = None

        yield {"event": "system_start", "status": "RUNNING", "active_agent": "System", "message": "Initializing Swarm..."}

        # Guardrails check
        client = get_llm_client()
        hint_guard = {"blocked": False}
        if human_hint:
            hint_guard = guard_prompt(human_hint, client=client, use_semantic_guard=True)
        blueprint_guard = guard_prompt(self.state["current_blueprint"], client=client, use_semantic_guard=True)

        if hint_guard["blocked"] or blueprint_guard["blocked"]:
            reason = hint_guard["reason"] if hint_guard["blocked"] else blueprint_guard["reason"]
            yield {"event": "security_blocked", "status": "FAILED", "active_agent": "System", "message": f"Blocked: {reason}"}
            return

        # Meta-prompt synthesis (only needed if we aren't resuming with approved code)
        if not approved_code:
            yield {"event": "meta_prompt_start", "status": "RUNNING", "active_agent": "Prompt_Engineer_Agent", "message": "Synthesizing prompt..."}
            self.run_autonomous_generation(self.state["current_blueprint"])

        while retry_count < self.max_retries:
            
            # ─────────────────────────────────────────────────────────────
            # ️ MANDATORY HUMAN APPROVAL CHECKPOINT
            # ─────────────────────────────────────────────────────────────
            if approved_code:
                # User approved the code, use it directly and skip generation
                clean_code = approved_code
                yield {"event": "approval_received", "status": "RUNNING", "active_agent": "Human", "message": "Human approved code. Proceeding to sandbox execution."}
                approved_code = None # Clear it so we don't skip generation on subsequent retries
            else:
                # Standard Generation Phase
                if human_hint and retry_count == 0:
                    user_prompt = f"Human Hint: {human_hint}\nBlueprint: {self.state['current_blueprint']}\nRewrite script."
                elif qa_feedback and qa_feedback.get("status") == "FAIL":
                    user_prompt = f"Error: {qa_feedback.get('error_summary')}\nHint: {qa_feedback.get('remediation_hint')}\nFix script."
                else:
                    user_prompt = f"Implement script based on: {self.state['current_blueprint']}"
                    
                yield {"event": "agent_start", "status": "RUNNING", "active_agent": "Dynamic_Lead_Coder", "message": "Generating code..."}
                
                collected_response_text = ""
                for stream_chunk in self.swarm["coder"].call_llm_stream(user_prompt):
                    yield stream_chunk
                    if stream_chunk.get("type") == "content":
                        collected_response_text += stream_chunk.get("text", "")

                clean_code = extract_code_from_markdown(collected_response_text)
                if not clean_code:
                    clean_code = "# ERROR: No code generated.\n"

                #  CRITICAL SECURITY PAUSE: If approval is required, stop here.
                if self.require_approval:
                    yield {
                        "event": "await_human_approval",
                        "status": "PAUSED",
                        "active_agent": "Human",
                        "message": "Code generated. Awaiting mandatory human review before execution.",
                        "generated_code": clean_code,
                        "retry_count": retry_count
                    }
                    return # Stop the generator. UI will handle the resume.

            # ─────────────────────────────────────────────────────────────
            # 🏗️ SANDBOX EXECUTION (Only reached if approved or approval disabled)
            # ─────────────────────────────────────────────────────────────
            with open(self.file_path, "w") as f:
                f.write(clean_code)
                
            yield {"event": "sandbox_start", "status": "RUNNING", "active_agent": "Sandbox", "message": "Executing in Docker sandbox..."}
            execution_result = run_in_sandbox(self.file_path, timeout=10.0)

            if execution_result["exit_code"] == 0:
                yield {"event": "execution_success", "status": "COMPLETED", "active_agent": "System", "message": "Success!", "stdout": execution_result["stdout"]}
                break

            # Handle Failure
            clean_error = parse_stderr(execution_result["stderr"])
            yield {"event": "sandbox_fail", "status": "RUNNING", "active_agent": "Sandbox", "message": "Execution failed.", "raw_traceback": clean_error}
            
            qa_prompt = f"Code:\n{clean_code}\n\nError:\n{clean_error}"
            qa_collected_text = ""
            for stream_chunk in self.swarm["qa_analyst"].call_llm_stream(qa_prompt, require_json=True):
                yield stream_chunk
                if stream_chunk.get("type") == "content":
                    qa_collected_text += stream_chunk.get("text", "")

            # 🛡️ REPLACED: Use the robust multi-stage parser instead of raw json.loads()
            qa_feedback = parse_qa_feedback(qa_collected_text)

            human_hint = None # Clear hint for next loop
            retry_count += 1

        if retry_count == self.max_retries:
            yield {"event": "hitl_paused", "status": "PAUSED", "active_agent": "System", "message": "Max retries reached."}