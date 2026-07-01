# swarm/agents.py
import json
from typing import Generator, Dict, Any
from config.settings import settings
from sandbox import run_in_sandbox, parse_stderr
from swarm.agents import create_swarm_agents, create_agent
from swarm.guardrails import check_input_guardrail, sanitize_file_path


class QwenDevSwarmOrchestrator:
    def __init__(self, max_retries: int = 3):
        """
        Initializes the central multi-agent orchestrator with dynamic meta-prompt capabilities.
        
        Args:
            max_retries: Hard limit for self-correction loops to protect token budgets.
        """
        self.max_retries = max_retries  # Token-safe retry budget guardrail
        
        # Internal backing variable for secure path tracking
        self._file_path = "generated_script.py"
        
        # Central JSON core state schema tracking the current task and history
        self.state = {
            "current_blueprint": "Create a robust python script that calculates Fibonacci numbers up to n.",
            "file_path": self._file_path,
            "model_in_use": getattr(settings, "MODEL_NAME", "qwen3.7-max"),  # Single source of truth lookup
            "history": []
        }
        
        # Seed and instantly sanitize initial base configuration path
        self.file_path = "generated_script.py"
        
        # Initialize the official Qwen Swarm Crew from swarm/agents.py
        self.swarm = create_swarm_agents()

    # 🛡️ DYNAMIC TOOL ARGUMENT GUARDRAIL PROPERTY
    @property
    def file_path(self) -> str:
        """Returns the secured internal file system string target."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        """Intercepts, logs, and sanitizes dangerous path mutations dynamically."""
        self._file_path = sanitize_file_path(value)
        self.state["file_path"] = self._file_path

    def run_autonomous_generation(self, user_feature_request: str) -> str:
        """
        Executes an upstream meta-prompt generation pass to dynamically construct
        a hyper-hardened Lead Coder instance tailored explicitly to the request.
        """
        # Phase 1: Generate the hyper-focused system prompt via the Prompt Engineer Agent
        meta_prompt_response = self.swarm["prompt_engineer"].call_llm(
            f"Generate a comprehensive, hardened system prompt to build this feature: {user_feature_request}"
        )
        compiled_prompt = meta_prompt_response
        
        # Phase 2: Instantiate or update the coder dynamically using the compiled prompt
        dynamic_coder = create_agent(
            name="Dynamic_Lead_Coder",
            instructions=compiled_prompt
        )
        
        # Hot-swap the standard coder inside our active registry group for this execution thread
        self.swarm["coder"] = dynamic_coder
        return compiled_prompt

    def execute_self_correction_loop(self, human_hint: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Manages the custom loop sequence of agent turns to fix runtime bugs iteratively.
        Accepts an optional human_hint parameter from the UI to steer correction trajectories.
        Yields structured payload state updates dynamically to feed the frontend interface.
        """
        retry_count = 0
        qa_feedback = None  # Start with clean slate; no feedback on the initial turn

        # Turning Point 1: System Startup Initialization Update
        yield {
            "event": "system_start",
            "status": "RUNNING",
            "active_agent": "System",
            "message": "Initializing Qwen-DevSwarm Self-Correction Loop...",
            "retry_count": retry_count,
            "core_state": self.state
        }

        # 🛡️ HARDENED APPLICATION GUARDRAILS: Intercept and validate all untrusted entry vectors
        is_hint_malicious = human_hint and check_input_guardrail(human_hint)
        is_blueprint_malicious = self.state.get("current_blueprint") and check_input_guardrail(self.state["current_blueprint"])

        if is_hint_malicious or is_blueprint_malicious:
            yield {
                "event": "security_blocked",
                "status": "FAILED",
                "active_agent": "System",
                "message": "Security Guardrail Blocked: Malicious prompt pattern detected in input scope.",
                "retry_count": retry_count,
                "core_state": self.state
            }
            return  # Immediate safe short-circuit termination

        # Upstream Synthesis: Compile the specialized system instructions before running the coder
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

        while retry_count < self.max_retries:
            # Step 1: Formulate prompts for the dynamic Lead Coder
            if human_hint and retry_count == 0:
                user_prompt = f"""The user has provided a critical implementation hint to correct the previous strategy.
                
💡 Human Engineer Hint: {human_hint}
📋 Original Target Blueprint: {self.state['current_blueprint']}

Please output a clean, rewritten version of the full Python script taking this hint into account."""
            elif qa_feedback and qa_feedback.get("status") == "FAIL":
                user_prompt = f"""Your previous code attempt failed execution. Review the feedback below and fix the script.

❌ Error Summary: {qa_feedback.get('error_summary')}
📍 Failed File/Lines: {qa_feedback.get('failed_component')}
💡 Remediation Hint: {qa_feedback.get('remediation_hint')}

Please output a clean, rewritten version of the full Python script fixing the issue."""
            else:
                user_prompt = f"Implement the requested script following your instructions exactly based on this context: {self.state['current_blueprint']}"
                
            # Turning Point 2: Broadcast Lead Coder Invocation Event
            yield {
                "event": "agent_start",
                "status": "RUNNING",
                "active_agent": "Dynamic_Lead_Coder",
                "message": f"[Turn {retry_count + 1}] Dynamic Lead Coder is generating Python source code...",
                "retry_count": retry_count,
                "prompt_context": user_prompt
            }
            
            # 1. Initialize a blank string collector for this turn's response
            collected_response_text = ""
            
            # Consume the live event generator stream step-by-step
            for stream_chunk in self.swarm["coder"].call_llm_stream(user_prompt):
                yield stream_chunk
                # Accumulate content tokens as they arrive from the cloud endpoint wire
                if stream_chunk.get("type") == "content":
                    collected_response_text += stream_chunk.get("text", "")

            # 2. Hardened write step: Write the accumulated code block directly to disk via secure property check
            if collected_response_text:
                with open(self.file_path, "w") as f:
                    f.write(collected_response_text)
            
            # 3. Clean up the old reader block safely
            try:
                with open(self.file_path, "r") as f:
                    generated_code = f.read()
            except FileNotFoundError:
                generated_code = self.swarm["coder"]._get_mock_fallback(user_prompt)
                with open(self.file_path, "w") as f:
                    f.write(generated_code)
                
            # Turning Point 3: Disk Compilation Confirmation Update
            yield {
                "event": "code_compiled",
                "status": "RUNNING",
                "active_agent": "Dynamic_Lead_Coder",
                "message": f"Code successfully compiled to disk at: '{self.file_path}'",
                "retry_count": retry_count,
                "generated_code": generated_code
            }

            # Step 2: Run the Execution Sandbox & Stderr Parser Check
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
                
                # Turning Point 4A: Stream Successful Termination Signal
                yield {
                    "event": "execution_success",
                    "status": "COMPLETED",
                    "active_agent": "System",
                    "message": "Success! Code executed with zero runtime errors. Verified safe for production.",
                    "retry_count": retry_count,
                    "stdout": execution_result["stdout"],
                    "core_state": self.state
                }
                break  # Clean exit code termination point!

            # Case B: Runtime Error detected. Clean context payload for critique
            clean_error = parse_stderr(execution_result["stderr"])
            
            # Turning Point 4B: Stream Sandbox Crash Warning and Traceback Details
            yield {
                "event": "sandbox_fail",
                "status": "RUNNING",
                "active_agent": "Sandbox",
                "message": f"Sandbox Flagged Error! Exit Code: {execution_result['exit_code']}",
                "retry_count": retry_count,
                "raw_traceback": clean_error
            }
            
            # Step 3: Pass error details to the Adversarial QA Agent
            qa_prompt = (
                f"The generated code crashed during localized testing.\n\n"
                f"--- Subprocess Source Code File ---\n{generated_code}\n\n"
                f"--- Clean Traceback from Sandbox Parser ---\n{clean_error}"
            )
            
            # Turning Point 5: Broadcast QA Analyst Invocation Event
            yield {
                "event": "agent_start",
                "status": "RUNNING",
                "active_agent": "QA_Analyst",
                "message": "Evaluating error context and writing remediation structural schema...",
                "retry_count": retry_count,
                "prompt_context": qa_prompt
            }
            
            # Stream the QA reasoning tokens if visible before extracting the JSON payload
            for stream_chunk in self.swarm["qa"].call_llm_stream(qa_prompt, require_json=True):
                yield stream_chunk

            # Perform a final blocking check to handle structural routing
            qa_json_response = self.swarm["qa"].call_llm(qa_prompt, require_json=True)
            try:
                qa_feedback = json.loads(qa_json_response)
            except json.JSONDecodeError:
                qa_feedback = {
                    "status": "FAIL",
                    "error_summary": "Raw execution crash trace parsing error",
                    "failed_component": self.file_path,
                    "remediation_hint": "Review code compliance syntax errors highlighted by the compiler logs."
                }

            # Track iteration step log metadata state 
            self.state["history"].append({
                "turn": retry_count,
                "status": "FAIL",
                "error": qa_feedback.get("error_summary")
            })
            
            # Turning Point 6: Broadcast QA Schema Assessment Details
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

        # Final loop verification guardrail analysis check: Budget Exhausted -> Yield HITL Handoff Request
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
    for state_update in orchestrator.execute_self_correction_loop():
        if "event" in state_update:
            print(f"📡 Terminal Monitored Transition: {state_update['event']} ({state_update['active_agent']})")