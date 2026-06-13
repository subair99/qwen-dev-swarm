# orchestrator.py
import json
from config.settings import settings
from sandbox import run_in_sandbox, parse_stderr
from swarm.agents import create_swarm_agents 


class QwenDevSwarmOrchestrator:
    def __init__(self, max_retries: int = 3):
        """
        Initializes the central multi-agent orchestrator.
        
        Args:
            max_retries: Hard limit for self-correction loops to protect token budgets.
        """
        self.max_retries = max_retries  # Token-safe retry budget guardrail [cite: 58, 62]
        
        # Central JSON core state schema tracking the current task and history [cite: 4, 5, 6]
        self.state = {
            "current_blueprint": "Create a robust python script that calculates Fibonacci numbers up to n.",
            "file_path": "generated_script.py",
            "model_in_use": getattr(settings, "MODEL_NAME", "qwen3.7-max"),  # Single source of truth lookup
            "history": []
        }
        
        # Initialize the official Qwen Swarm Crew from swarm/agents.py
        self.swarm = create_swarm_agents()


    def execute_self_correction_loop(self):
        """
        Manages the custom loop sequence of agent turns to fix runtime bugs iteratively.
        Sequence: Lead_Coder -> Sandbox -> QA_Analyst -> Lead_Coder (Retry) [cite: 9, 24]
        """
        retry_count = 0
        qa_feedback = None  # Start with clean slate; no feedback on the initial turn [cite: 59]

        print("🚀 Starting Qwen-DevSwarm Self-Correction Loop...")
        print(f"🤖 Current Target Model: {self.state['model_in_use']}")
        print(f"📋 Target Blueprint: {self.state['current_blueprint']}")

        while retry_count < self.max_retries:
            print(f"\n==========================================")
            print(f"🔄 TURN {retry_count + 1} OF {self.max_retries} (Retry Budget)")
            print(f"==========================================")
            
            # Step 1: Formulate prompts for the Lead Coder (Developer Agent) [cite: 25, 59]
            if qa_feedback and qa_feedback.get("status") == "FAIL":
                # Clean triple-quoted f-string block to display the structured QA trace [cite: 59]
                user_prompt = f"""Your previous code attempt failed execution. Review the feedback below and fix the script.

❌ Error Summary: {qa_feedback.get('error_summary')}
📍 Failed File/Lines: {qa_feedback.get('failed_component')}
💡 Remediation Hint: {qa_feedback.get('remediation_hint')}

Please output a clean, rewritten version of the full Python script fixing the issue."""
            else:
                user_prompt = f"Implement code based on this technical design requirements blueprint:\n{self.state['current_blueprint']}"
                
            print("🤖 [Turn: Lead_Coder] -> Generating Python source code...")
            generated_code = self.swarm["coder"].call_llm(user_prompt)
            
            # Persist code change to disk using file setup [cite: 12, 27]
            with open(self.state["file_path"], "w") as f:
                f.write(generated_code)
            print(f"💾 Code successfully compiled to disk at: '{self.state['file_path']}'")

            # Step 2: Run the Execution Sandbox & Stderr Parser Check [cite: 30, 40, 41]
            print("🧪 [Turn: Sandbox Workspace] -> Running script under isolated subprocess monitor...")
            execution_result = run_in_sandbox(self.state["file_path"], timeout=10.0)

            # Case A: Code ran perfectly with zero exceptions! [cite: 37, 38]
            if execution_result["exit_code"] == 0:
                print("\n✅ Success! Code executed with zero runtime errors.")
                print(f"📊 Captured Stdout:\n{execution_result['stdout']}")
                
                # Update tracking matrix core state schema 
                self.state["history"].append({
                    "turn": retry_count,
                    "status": "PASS",
                    "stdout": execution_result["stdout"]
                })
                print("\n🚀 Code verified as safe. Handing over to production deployment layer.")
                break  # Clean exit code termination point! [cite: 38]

            # Case B: Runtime Error detected. Clean context payload for critique [cite: 32, 35, 41]
            print(f"❌ Sandbox Flagged Error! Exit Code: {execution_result['exit_code']} (Status: {execution_result['status']})")
            clean_error = parse_stderr(execution_result["stderr"])
            print(f"📋 Clean Traceback Extracted:\n{clean_error}")
            
            # Step 3: Pass error details to the Adversarial QA Agent [cite: 35, 45, 59]
            qa_prompt = (
                f"The generated code crashed during localized testing.\n\n"
                f"--- Subprocess Source Code File ---\n{generated_code}\n\n"
                f"--- Clean Traceback from Sandbox Parser ---\n{clean_error}"
            )
            
            print("🔍 [Turn: QA_Analyst] -> Evaluating error context and writing remediation structural schema...")
            qa_json_response = self.swarm["qa"].call_llm(qa_prompt, require_json=True)
            
            try:
                # Parse strict feedback constraints [cite: 46, 47]
                qa_feedback = json.loads(qa_json_response)
                print(f"📋 QA Feedback parsed successfully.")
                print(f"   - Status: {qa_feedback.get('status')}")
                print(f"   - Issue: {qa_feedback.get('error_summary')}")
                print(f"   - Hint: {qa_feedback.get('remediation_hint')}")
            except json.JSONDecodeError:
                print("⚠️ Warning: QA Agent failed to output valid JSON framework data. Generating custom retry backup fallback context.")
                qa_feedback = {
                    "status": "FAIL",
                    "error_summary": "Raw execution crash trace parsing error",
                    "failed_component": self.state["file_path"],
                    "remediation_hint": "Review code compliance syntax errors highlighted by the compiler logs."
                }

            # Track iteration step log metadata state 
            self.state["history"].append({
                "turn": retry_count,
                "status": "FAIL",
                "error": qa_feedback.get("error_summary")
            })
            
            # Increment loop index variable to enforce target Retry Budget ceiling safeguards [cite: 58, 59]
            retry_count += 1

        # Final loop verification guardrail analysis check [cite: 60]
        if retry_count == self.max_retries and (not qa_feedback or qa_feedback.get("status") == "FAIL"):
            print("\n🚨 ========================================================")
            print("🚨 GUARDRAIL TRIGGERED: Exhausted retry budget allocation ceiling.")
            print("🚨 Self-correction cycle broke to avoid runaway billing or recursion loops.")
            print("🚨 Escalating logs for Developer review or manual system override.")
            print("==========================================================")


if __name__ == "__main__":
    # Local execution unit check. Sets budget limit to 3 turns. [cite: 58]
    orchestrator = QwenDevSwarmOrchestrator(max_retries=3)
    orchestrator.execute_self_correction_loop()