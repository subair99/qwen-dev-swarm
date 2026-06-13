# swarm/agents.py
import json
from typing import List, Dict, Any, Callable
from openai import OpenAI
from config.settings import settings

class QwenAgent:
    def __init__(
        self, 
        name: str, 
        instructions: str, 
        tools: List[Callable] = None
    ):
        self.name = name
        self.instructions = instructions  # This acts as our system prompt
        self.tools = tools or []
        
        # 1. Pull the direct Aliyun MaaS cloud endpoint layer from settings natively using getattr
        self.base_url = getattr(
            settings, 
            "QWEN_BASE_URL", 
            "https://ws-zp9gpq4ly3nzvc4s.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        )
        
        # 2. Securely extract your Qwen Cloud API key
        self.api_key = getattr(settings, "QWEN_API_KEY", None) or getattr(settings, "DASHSCOPE_API_KEY", None)
        
        # 3. Target your preferred production cloud model name string (Single source of truth)
        self.model_name = getattr(settings, "MODEL_NAME", "qwen3.7-max")
        
        # Guardrail check: Warn you early if environment variables fail to load from config
        if not self.api_key:
            print(f"⚠️ Warning: Cloud access key could not be resolved from settings for agent: {self.name}")
        
        # Initialize the OpenAI wrapper client pointing to your official cloud engine workspace
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )


    def call_llm(self, user_prompt: str, require_json: bool = False) -> str:
        """
        Executes an inference call to the Qwen model using the OpenAI client wrapper.
        Includes thinking preservation logic and structured JSON formatting adjustments[cite: 15, 16, 64, 65].
        """
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_prompt}
        ]

        # Base API keyword args
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,  # Low temperature for highly deterministic engineering output
            # Ensure thinking preservation remains enabled in the local runtime payload [cite: 64]
            "extra_body": {"preserve_thinking": True} 
        }

        # Enforce structured JSON constraint if flagged [cite: 47]
        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            # Extracted string naturally contains any wrapped <thinking> tags if supported by runtime [cite: 65]
            return response.choices[0].message.content
            
        except Exception as e:
            # Safe local fallback structure in case of network or authentication hiccups during tests
            print(f"⚠️ OpenAI Client Error on {self.name}: {e}")
            return self._get_mock_fallback(user_prompt)


    def _get_mock_fallback(self, user_prompt: str) -> str:
        """Fallback mock engine to keep your Phase 2 self-correction loop robust during offline testing[cite: 58]."""
        if self.name == "Lead_Coder":
            if "feedback" in user_prompt.lower():
                return "print('Calculating Fibonacci numbers: 0, 1, 1, 2, 3, 5')"
            return "print('Calculating Fibonacci' "  # Intentionally missing bracket
            
        elif self.name == "QA_Analyst":
            return json.dumps({
                "status": "FAIL",
                "error_summary": "SyntaxError: unexpected EOF while parsing",
                "failed_component": "generated_script.py, Line 1",
                "remediation_hint": "Add a closing parenthesis ')' to the end of your print statement."
            })
        return ""


def create_swarm_agents() -> Dict[str, QwenAgent]:
    """Initializes the minimal dev swarm crew with distinct engineering behaviors[cite: 9]."""
    
    architect = QwenAgent(
        name="Software_Architect",
        instructions=(
            "You are a Software Architect. You break down complex feature requests "
            "into step-by-step modular designs and precise technical requirements tasks[cite: 9]."
        )
    )
    
    coder = QwenAgent(
        name="Lead_Coder",
        instructions=(
            "You are an expert Developer Agent named Lead_Coder. Your job is to output pure, "
            "functional Python code matching requested specs[cite: 9]. Provide raw code ONLY. Do not "
            "wrap your output inside markdown codeblocks (such as ```python ... ```) or conversational filler."
        )
    )
    
    qa_analyst = QwenAgent(
        name="QA_Analyst",
        instructions=(
            "You are an adversarial QA Analyst. Your exclusive objective is to analyze execution errors "
            "and provide structured correction feedback. You must respond ONLY with a raw JSON object matching this schema:\n"
            "{\n"
            '  "status": "FAIL" or "PASS",\n'
            '  "error_summary": "Short description of the runtime exception",\n'
            '  "failed_component": "File path and line range of code containing the issue",\n'
            '  "remediation_hint": "Concrete instruction on how to fix this syntax or runtime error"\n'
            "}"
        )
    )
    
    return {
        "architect": architect,
        "coder": coder,
        "qa": qa_analyst
    }