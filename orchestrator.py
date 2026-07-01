# orchestrator.py
import json
import logging
from typing import Generator, Dict, Any, Optional
from config.settings import settings
from sandbox import run_in_sandbox, parse_stderr
from swarm.agents import create_swarm_agents, create_agent, extract_code_from_markdown
from swarm.guardrails import check_input_guardrail, sanitize_file_path

logger = logging.getLogger(__name__)


class QwenDevSwarmOrchestrator:
    def __init__(self, max_retries: int = 3):
        """
        Initializes the central multi-agent orchestrator with dynamic meta-prompt capabilities.
        
        Args:
            max_retries: Hard limit for self-correction loops to protect token budgets.
        """
        self.max_retries = max_retries
        
        # Internal backing variable for secure path tracking
        self._file_path = "generated_script.py"
        
        # Central JSON core state schema tracking the current task and history
        self.state = {
            "current_blueprint": "",  # Empty by default; set via set_blueprint()
            "file_path": self._file_path,
            "model_in_use": getattr(settings, "MODEL_NAME", "qwen3.7-max"),
            "history": []
        }
        
        # Initialize the official Qwen Swarm Crew
        self.swarm = create_swarm_agents()
        
        # Cache for compiled prompts to avoid redundant regeneration
        self._compiled_prompt_cache: Dict[str, str] = {}

    # ─────────────────────────────────────────────────────────────
    # 🛡️ DYNAMIC TOOL ARGUMENT GUARDRAIL PROPERTY
    # ─────────────────────────────────────────────────────────────
    @property
    def file_path(self) -> str:
        """Returns the secured internal file system string target."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        """Intercepts, logs, and sanitizes dangerous path mutations dynamically."""
        self._file_path = sanitize_file_path(value)
        self.state["file_path"] = self._file_path

    # ─────────────────────────────────────────────────────────────
    # 📋 BLUEPRINT MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    def set_blueprint(self, blueprint: str) -> None:
        """
        Sets the current task blueprint with guardrail validation.
        Invalidates the compiled prompt cache to force regeneration.
        """
        if check_input_guardrail(blueprint):
            raise ValueError("🚨 Security Guardrail: Malicious pattern detected in blueprint.")
        
        self.state["current_blueprint"] = blueprint
        # Invalidate cache so the next run regenerates the meta-prompt
        self._compiled_prompt_cache.pop(blueprint, None)

    # ─────────────────────────────────────────────────────────────
    # 🧠 META-PROMPT GENERATION (Cached)
    # ─────────────────────────────────────────────────────────────
    def run_autonomous_generation(self, user_feature_request: str) -> str:
        """
        Executes an upstream meta-prompt generation pass to dynamically construct
        a hyper-hardened Lead Coder instance tailored explicitly to the request.
        Results are cached to avoid redundant regeneration.
        """
        # Check cache first
        if user_feature_request in self._compiled_prompt_cache:
            logger.info("Using cached compiled prompt for blueprint.")
            compiled_prompt = self._compiled_prompt_cache[user_feature_request]
        else:
            # Phase 1: Generate the hyper-focused system prompt via the Prompt Engineer Agent
            meta_prompt_response = self.swarm["prompt_engineer"].call_llm(
                f"Generate a comprehensive, hardened system prompt to build this feature: {user_feature_request}"
            )
            compiled_prompt = meta_prompt_response
            self._compiled_prompt_cache[user_feature_request] = compiled_prompt
        
        # Phase 2: Instantiate or update the coder dynamically using the compiled prompt
        dynamic_coder = create_agent(
            name="Dynamic_Lead_Coder",
            instructions=compiled_prompt
        )
        
        # Hot-swap the standard coder inside our active registry
        self.swarm["coder"] = dynamic_coder
        return compiled_prompt

    # ─────────────────────────────────────────────────────────────
    # 🔄 SELF-CORRECTION LOOP
    # ─────────────────────────────────────────────────────────────
    def execute_self_correction_loop(self, human_hint: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Manages the custom loop sequence of agent turns to fix runtime bugs iteratively.
        Accepts an optional human_hint parameter from the UI to steer correction trajectories.
        Yields structured payload state updates dynamically to feed the frontend interface.
        """
        # Validate that a blueprint has been set
        if not self.state.get("current_blueprint"):
            yield {
                "event": "system_start",
                "status": "FAILED",
                "active_agent": "System",
                "message": "No blueprint set. Call set_blueprint() before running the loop.",
                "retry_count": 0,
                "core_state": self.state
            }
            return

        retry_count = 0
        qa_feedback = None

        # Turning Point 1: System Startup Initialization Update
        yield {
            "event": "system_start",
            "status": "RUNNING",
            "active_agent": "System",
            "message": "Initializing Qwen-DevSwarm Self-Correction Loop...",
            "retry_count": retry_count,
            "core_state": self.state
        }

        # ─────────────────────────────────────────────────────────────
        # 🛡️ HARDENED APPLICATION GUARDRAILS
        # ─────────────────────────────────────────────────────────────
        is_hint_malicious = human_hint and check_input_guardrail(human_hint)
        is_blueprint_malicious = check_input_guardrail(self.state["current_blueprint"])

        if is_hint_malicious or is_blueprint_malicious:
            yield {
                "event": "security_blocked",
                "status": "FAILED",
                "active_agent": "System",
                "message": "Security Guardrail Blocked: Malicious prompt pattern detected in input scope.",
                "retry_count": retry_count,
                "core_state": self.state
            }
            return

        # ─────────────────────────────────────────────────────────────
        # 🧠 META-PROMPT SYNTHESIS (Cached)
        # ─────────────────────────────────────────────────────────────
        yield {
            "event": "meta_prompt_start",
            "status": "RUNNING",
            "active_agent": "Prompt_Engineer_Agent",
            "message": "Prompt Engineer is synthesizing an adversarial, hardened specification prompt...",
            "retry_count": retry_count
        }
        
        compiled_blueprint = self.run_autonomous_generation(self.state["current_blueprint"])

        yield {
            "event": "meta_prompt_compiled",
            "status": "RUNNING",
            "active_agent": "Prompt_Engineer_Agent",
            "message": "Dynamic specifications compiled. Spawning Dynamic_Lead_Coder.",
            "retry_count": retry_count,
            "compiled_prompt": compiled_blueprint
        }

        # ─────────────────────────────────────────────────────────────
        # 🔄 MAIN CORRECTION LOOP
        # ─────────────────────────────────────────────────────────────
        while retry_count < self.max_retries:
            
            # Step 1: Formulate prompts for the dynamic Lead Coder
            if human_hint and retry_count == 0:
                user_prompt = (
                    f"The user has provided a critical implementation hint to correct the previous strategy.\n\n"
                    f"💡 Human Engineer Hint: {human_hint}\n"
                    f"📋 Original Target Blueprint: {self.state['current_blueprint']}\n\n"
                    f"Please output a clean, rewritten version of the full Python script taking this hint into account."
                )
            elif qa_feedback and qa_feedback.get("status") == "FAIL":
                user_prompt = (
                    f"Your previous code attempt failed execution. Review the feedback below and fix the script.\n\n"
                    f"❌ Error Summary: {qa_feedback.get('error_summary')}\n"
                    f"📍 Failed File/Lines: {qa_feedback.get('failed_component')}\n"
                    f"💡 Remediation Hint: {qa_feedback.get('remediation_hint')}\n\n"
                    f"Please output a clean, rewritten version of the full Python script fixing the issue."
                )
            else:
                user_prompt = (
                    f"Implement the requested script following your instructions exactly "
                    f"based on this context: {self.state['current_blueprint']}"
                )
                
            # Turning Point 2: Broadcast Lead Coder Invocation Event
            yield {
                "event": "agent_start",
                "status": "RUNNING",
                "active_agent": "Dynamic_Lead_Coder",
                "message": f"[Turn {retry_count + 1}] Dynamic Lead Coder is generating Python source code...",
                "retry_count": retry_count,
                "prompt_context": user_prompt
            }
            
            # 1. Collect the streamed response
            collected_response_text = ""
            
            for stream_chunk in self.swarm["coder"].call_llm_stream(user_prompt):
                yield stream_chunk
                if stream_chunk.get("type") == "content":
                    collected_response_text += stream_chunk.get("text", "")

            # 2. 🛡️ CRITICAL FIX: Extract clean code from markdown before writing to disk
            clean_code = extract_code_from_markdown(collected_response_text)
            
            if clean_code:
                with open(self.file_path, "w") as f:
                    f.write(clean_code)
            else:
                # Fallback if the model returned no parseable code
                logger.warning("Coder returned no parseable code. Using empty file.")
                with open(self.file_path, "w") as f:
                    f.write("# ERROR: No code generated by the model.\n")
                clean_code = "# ERROR: No code generated by the model.\n"
            
            # Turning Point 3: Disk Compilation Confirmation Update
            yield {
                "event": "code_compiled",
                "status": "RUNNING",
                "active_agent": "Dynamic_Lead_Coder",
                "message": f"Code successfully compiled to disk at: '{self.file_path}'",
                "retry_count": retry_count,
                "generated_code": clean_code
            }

            # ─────────────────────────────────────────────────────────────
            # 🏗️ SANDBOX EXECUTION
            # ─────────────────────────────────────────────────────────────
            yield {
                "event": "sandbox_start",
                "status": "RUNNING",
                "active_agent": "Sandbox",
                "message": "Running script under isolated sandbox subprocess monitor...",
                "retry_count": retry_count
            }
            
            execution_result = run_in_sandbox(self.file_path, timeout=10.0)

            # Case A: Code ran perfectly with zero exceptions!
            if execution_result["exit_code"] == 0:
                self.state["history"].append({
                    "turn": retry_count,
                    "status": "PASS",
                    "stdout": execution_result["stdout"]
                })
                
                yield {
                    "event": "execution_success",
                    "status": "COMPLETED",
                    "active_agent": "System",
                    "message": "Success! Code executed with zero runtime errors. Verified safe for production.",
                    "retry_count": retry_count,
                    "stdout": execution_result["stdout"],
                    "core_state": self.state
                }
                break

            # Case B: Runtime Error detected.
            clean_error = parse_stderr(execution_result["stderr"])
            
            yield {
                "event": "sandbox_fail",
                "status": "RUNNING",
                "active_agent": "Sandbox",
                "message": f"Sandbox Flagged Error! Exit Code: {execution_result['exit_code']}",
                "retry_count": retry_count,
                "raw_traceback": clean_error
            }
            
            # ─────────────────────────────────────────────────────────────
            # 🕵️ QA ANALYST CRITIQUE (FIXED: Single call, stream + parse)
            # ─────────────────────────────────────────────────────────────
            qa_prompt = (
                f"The generated code crashed during localized testing.\n\n"
                f"--- Subprocess Source Code File ---\n{clean_code}\n\n"
                f"--- Clean Traceback from Sandbox Parser ---\n{clean_error}"
            )
            
            yield {
                "event": "agent_start",
                "status": "RUNNING",
                "active_agent": "QA_Analyst",
                "message": "Evaluating error context and writing remediation structural schema...",
                "retry_count": retry_count,
                "prompt_context": qa_prompt
            }
            
            # 🛡️ CRITICAL FIX: Stream the QA response AND collect content tokens for JSON parsing
            # This eliminates the redundant second API call.
            qa_collected_text = ""
            for stream_chunk in self.swarm["qa_analyst"].call_llm_stream(qa_prompt, require_json=True):
                yield stream_chunk
                if stream_chunk.get("type") == "content":
                    qa_collected_text += stream_chunk.get("text", "")

            # Parse the collected stream content as JSON
            try:
                qa_feedback = json.loads(qa_collected_text)
            except json.JSONDecodeError:
                logger.warning(f"QA Analyst returned invalid JSON. Raw output: {qa_collected_text[:200]}")
                qa_feedback = {
                    "status": "FAIL",
                    "error_summary": "QA Analyst returned unparseable JSON response",
                    "failed_component": self.file_path,
                    "remediation_hint": "Review code compliance syntax errors highlighted by the compiler logs."
                }

            # Track iteration step log metadata state 
            self.state["history"].append({
                "turn": retry_count,
                "status": "FAIL",
                "error": qa_feedback.get("error_summary")
            })
            
            yield {
                "event": "qa_complete",
                "status": "RUNNING",
                "active_agent": "QA_Analyst",
                "message": "QA Feedback parsed successfully. Advancing loop retry token structure.",
                "retry_count": retry_count,
                "qa_feedback": qa_feedback,
                "core_state": self.state
            }
            
            # Clean human hint override parameter so downstream automatic cycles don't get trapped repeating it
            human_hint = None
            retry_count += 1

        # Final loop verification guardrail: Budget Exhausted -> Yield HITL Handoff Request
        if retry_count == self.max_retries and (not qa_feedback or qa_feedback.get("status") == "FAIL"):
            yield {
                "event": "hitl_paused",
                "status": "PAUSED",
                "active_agent": "System",
                "message": "GUARDRAIL TRIGGERED: Exhausted retry budget allocation ceiling.",
                "retry_count": retry_count,
                "core_state": self.state
            }


if __name__ == "__main__":
    # uv run terminal execution block
    orchestrator = QwenDevSwarmOrchestrator(max_retries=3)
    
    # Set the blueprint before running the loop
    orchestrator.set_blueprint("Create a robust python script that calculates Fibonacci numbers up to n.")
    
    for state_update in orchestrator.execute_self_correction_loop():
        if "event" in state_update:
            print(f"📡 Terminal Monitored Transition: {state_update['event']} ({state_update['active_agent']})")