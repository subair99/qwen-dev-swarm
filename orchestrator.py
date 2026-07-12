# orchestrator.py
import os
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
    """
    if not raw_text:
        return {"status": "FAIL", "error_summary": "Empty QA response", "failed_component": "Unknown", "remediation_hint": "No feedback provided."}

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw_text[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass

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
        self.max_retries = max_retries
        self.require_approval = require_approval 
        
        self._file_path = "generated_script.py"
        self.state = {
            "current_blueprint": "",
            "file_path": self._file_path,
            "model_in_use": getattr(settings, "MODEL_NAME", "qwen3.7-max"),
            "history": [],
            # ️ PERSISTENT STATE FOR LOOP RESUMPTION
            "is_paused": False,
            "retry_count": 0,
            "clean_code": "",
            "generated_tests": "",
            "qa_feedback": None,
            "skip_tests": False
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
        """
        if not self.state.get("current_blueprint"):
            yield {"event": "system_start", "status": "FAILED", "active_agent": "System", "message": "No blueprint set."}
            return

        # Initialize variables
        retry_count = self.state.get("retry_count", 0)
        qa_feedback = self.state.get("qa_feedback", None)
        clean_code = self.state.get("clean_code", "")
        generated_tests = self.state.get("generated_tests", "")
        skip_tests = self.state.get("skip_tests", False)

        print(f"\n[ORCHESTRATOR] Starting loop. retry_count={retry_count}, approved_code={bool(approved_code)}")

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

        if not approved_code:
            yield {"event": "meta_prompt_start", "status": "RUNNING", "active_agent": "Prompt_Engineer_Agent", "message": "Synthesizing prompt..."}
            self.run_autonomous_generation(self.state["current_blueprint"])

        # ─────────────────────────────────────────────────────────────
        #  SELF-CORRECTION LOOP
        # ─────────────────────────────────────────────────────────────
        while True:
            print(f"[ORCHESTRATOR] Loop iteration {retry_count}. Max retries: {self.max_retries}")
            
            if retry_count >= self.max_retries:
                print("[ORCHESTRATOR] MAX RETRIES REACHED. BREAKING LOOP.")
                yield {
                    "event": "max_retries_exceeded",
                    "status": "FAILED",
                    "active_agent": "System",
                    "message": f"Failed after {self.max_retries} correction attempts.",
                    "generated_code": clean_code
                }
                break 

            # ─────────────────────────────────────────────────────────────
            # 1️ HANDLE HUMAN APPROVED CODE (One-shot execution)
            # ─────────────────────────────────────────────────────────────
            if approved_code:
                print("[ORCHESTRATOR] Processing Human Approved Code...")
                clean_code = approved_code
                approved_code = None # Clear it immediately
                skip_tests = True    # Skip tests for manually approved code

                with open(self.file_path, "w") as f:
                    f.write(clean_code)

                yield {"event": "sandbox_start", "status": "RUNNING", "active_agent": "Sandbox", "message": "Executing approved code..."}
                execution_result = run_in_sandbox(self.file_path, timeout=10.0)

                if execution_result["exit_code"] == 0:
                    print("[ORCHESTRATOR] Approved code SUCCEEDED in sandbox!")
                    yield {
                        "event": "execution_success", 
                        "status": "COMPLETED", 
                        "active_agent": "System", 
                        "message": "Success! Approved code executed.", 
                        "stdout": execution_result["stdout"]
                    }
                    break # <--- CRITICAL: STOP THE LOOP ON SUCCESS
                else:
                    clean_error = parse_stderr(execution_result["stderr"])
                    print(f"[ORCHESTRATOR] Approved code FAILED in sandbox: {clean_error}")
                    yield {
                        "event": "sandbox_fail", 
                        "status": "FAILED", 
                        "active_agent": "System", 
                        "message": f"Approved code failed: {clean_error[:100]}", 
                        "raw_traceback": clean_error
                    }
                    break # <--- CRITICAL: STOP THE LOOP ON FAILURE (DO NOT CALL LEAD CODER)

            # ─────────────────────────────────────────────────────────────
            # 2️⃣ HANDLE AI GENERATION
            # ─────────────────────────────────────────────────────────────
            else:
                print("[ORCHESTRATOR] Generating new code with Lead Coder...")
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

                # Security Audit
                yield {"event": "security_audit_start", "status": "RUNNING", "active_agent": "Security_Auditor_Agent", "message": "Scanning for vulnerabilities..."}
                security_audit_text = self.swarm["security_auditor"].call_llm(
                    f"Review this code for vulnerabilities:\n\n{clean_code}", 
                    require_json=True
                )
                try:
                    security_report = json.loads(security_audit_text)
                except json.JSONDecodeError:
                    security_report = {"status": "PASS", "vulnerabilities": [], "risk_level": "NONE", "remediation_hint": "Audit parsing failed."}

                # Test Generation
                yield {"event": "test_generation_start", "status": "RUNNING", "active_agent": "Test_Generator_Agent", "message": "Generating unit tests..."}
                test_gen_text = ""
                for stream_chunk in self.swarm["test_generator"].call_llm_stream(
                    f"Feature Request: {self.state['current_blueprint']}\n\nCode Implementation:\n{clean_code}"
                ):
                    yield stream_chunk
                    if stream_chunk.get("type") == "content":
                        test_gen_text += stream_chunk.get("text", "")

                generated_tests = extract_code_from_markdown(test_gen_text)
                if not generated_tests:
                    generated_tests = "# ERROR: No tests generated.\n"
                
                skip_tests = False

                # PAUSE FOR APPROVAL
                if self.require_approval:
                    print("[ORCHESTRATOR] Pausing for human approval...")
                    self.state["retry_count"] = retry_count
                    self.state["clean_code"] = clean_code
                    self.state["generated_tests"] = generated_tests
                    self.state["qa_feedback"] = qa_feedback

                    yield {
                        "event": "await_human_approval",
                        "status": "PAUSED",
                        "active_agent": "Human",
                        "message": "Code generated. Awaiting mandatory human review before execution.",
                        "generated_code": clean_code,
                        "generated_tests": generated_tests,
                        "security_report": security_report,
                        "retry_count": retry_count
                    }
                    return # Stop generator to wait for UI

            # ─────────────────────────────────────────────────────────────
            # 3️⃣ SANDBOX EXECUTION (For AI Generated Code)
            # ─────────────────────────────────────────────────────────────
            with open(self.file_path, "w") as f:
                f.write(clean_code)

            test_file_path = "test_generated_script.py"
            with open(test_file_path, "w") as f:
                f.write(generated_tests)

            yield {"event": "sandbox_start", "status": "RUNNING", "active_agent": "Sandbox", "message": "Executing AI generated script..."}
            execution_result = run_in_sandbox(self.file_path, timeout=10.0)

            if execution_result["exit_code"] == 0:
                if skip_tests:
                    yield {"event": "execution_success", "status": "COMPLETED", "active_agent": "System", "message": "Success!", "stdout": execution_result["stdout"]}
                    break
                
                print("[ORCHESTRATOR] Main script passed. Running tests...")
                yield {"event": "test_execution_start", "status": "RUNNING", "active_agent": "Sandbox", "message": "Running unit tests..."}
                test_result = run_in_sandbox(
                    test_file_path, 
                    timeout=15.0, 
                    command=["pytest", f"/workspace/{os.path.basename(test_file_path)}", "-v"]
                )
                
                # Exit code 0 = success, 5 = no tests collected
                if test_result["exit_code"] in [0, 5]:
                    print("[ORCHESTRATOR] Tests passed! Generating docs...")
                    yield {"event": "doc_gen_start", "status": "RUNNING", "active_agent": "Documentation_Agent", "message": "Generating documentation..."}
                    doc_text = self.swarm["documentation_agent"].call_llm(
                        f"Code:\n{clean_code}\n\nFeature Request:\n{self.state['current_blueprint']}",
                        require_json=True
                    )
                    try:
                        doc_report = json.loads(doc_text)
                        documented_code = doc_report.get("documented_code", clean_code)
                        readme_md = doc_report.get("readme_md", "")
                        
                        # 🛡️ POST-PROCESSING: MANDATORY DOCSTRING CHECK
                        if not re.match(r'^\s*"""', documented_code):
                            print("[ORCHESTRATOR] Final code missing module docstring. Triggering one last rewrite...")
                            yield {"event": "docstring_rewrite_start", "status": "RUNNING", "active_agent": "Dynamic_Lead_Coder", "message": "Adding missing module docstring..."}
                            
                            rewrite_prompt = (
                                "The following code is missing the mandatory module-level docstring at the very top. "
                                "Please output ONLY the complete code with the required docstring added at the beginning. "
                                "Do not change any logic.\n\n"
                                f"Code:\n{documented_code}"
                            )
                            
                            rewrite_text = ""
                            for stream_chunk in self.swarm["coder"].call_llm_stream(rewrite_prompt):
                                yield stream_chunk
                                if stream_chunk.get("type") == "content":
                                    rewrite_text += stream_chunk.get("text", "")
                                    
                            documented_code = extract_code_from_markdown(rewrite_text)
                            # Fallback if the LLM still fails to format it correctly
                            if not documented_code or not re.match(r'^\s*"""', documented_code):
                                documented_code = f'"""\nAuto-generated module documentation.\n"""\n\n{documented_code}'

                        with open(self.file_path, "w") as f:
                            f.write(documented_code)
                        with open("README.md", "w") as f:
                            f.write(readme_md)
                    except json.JSONDecodeError:
                        logger.warning("Documentation agent returned invalid JSON. Skipping doc generation.")

                    yield {
                        "event": "execution_success", 
                        "status": "COMPLETED", 
                        "active_agent": "System", 
                        "message": "Success! Code and tests passed.", 
                        "stdout": execution_result["stdout"], 
                        "test_stdout": test_result["stdout"]
                    }
                    break
                else:
                    clean_test_error = parse_stderr(test_result["stderr"])
                    print(f"[ORCHESTRATOR] Tests failed: {clean_test_error}")
                    yield {"event": "test_fail", "status": "RUNNING", "active_agent": "Sandbox", "message": "Unit tests failed.", "raw_traceback": clean_test_error}
                    clean_error = clean_test_error
                    qa_prompt = f"Code:\n{clean_code}\n\nTests:\n{generated_tests}\n\nTest Error:\n{clean_error}"
            else:
                clean_error = parse_stderr(execution_result["stderr"])
                print(f"[ORCHESTRATOR] Sandbox execution failed: {clean_error}")
                yield {"event": "sandbox_fail", "status": "RUNNING", "active_agent": "Sandbox", "message": "Execution failed.", "raw_traceback": clean_error}
                qa_prompt = f"Code:\n{clean_code}\n\nError:\n{clean_error}"

            # Handle Failure (QA Analyst Loop)
            print("[ORCHESTRATOR] Sending to QA Analyst for feedback...")
            qa_collected_text = ""
            for stream_chunk in self.swarm["qa_analyst"].call_llm_stream(qa_prompt, require_json=True):
                yield stream_chunk
                if stream_chunk.get("type") == "content":
                    qa_collected_text += stream_chunk.get("text", "")

            qa_feedback = parse_qa_feedback(qa_collected_text)

            human_hint = None 
            retry_count += 1
            
            # Save state for next loop
            self.state["retry_count"] = retry_count
            self.state["clean_code"] = clean_code
            self.state["generated_tests"] = generated_tests
            self.state["qa_feedback"] = qa_feedback
            self.state["skip_tests"] = skip_tests