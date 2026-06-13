import json
from typing import List, Dict, Any, Callable, Generator
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
        Executes a blocking inference call to the Qwen model using the OpenAI client wrapper.
        Includes thinking preservation logic and structured JSON formatting adjustments.
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
            # Ensure thinking preservation remains enabled in the local runtime payload
            "extra_body": {"preserve_thinking": True} 
        }

        # Enforce structured JSON constraint if flagged
        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            # Extracted string naturally contains any wrapped <thinking> tags if supported by runtime
            return response.choices[0].message.content
            
        except Exception as e:
            # Safe local fallback structure in case of network or authentication hiccups during tests
            print(f"⚠️ OpenAI Client Error on {self.name}: {e}")
            return self._get_mock_fallback(user_prompt)

    def call_llm_stream(self, user_prompt: str, require_json: bool = False) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a real-time streaming inference call to the Qwen cloud endpoint.
        Maintains a rolling text accumulation state machine buffer to cleanly isolate 
        and route deep <thinking> tags away from raw code/JSON outputs dynamically.
        """
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "stream": True,  # Enables real-time delta chunk allocation
            "extra_body": {"preserve_thinking": True}
        }

        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            print(f"⚠️ Streaming Error on {self.name}: {e}")
            fallback_text = self._get_mock_fallback(user_prompt)
            yield {"type": "content", "text": fallback_text}
            return

        # Stateful stream tracking markers
        inside_thinking = False
        full_buffer = ""

        for chunk in stream:
            # Safeguard against empty choices lists from cloud metadata chunks
            if not getattr(chunk, "choices", None) or len(chunk.choices) == 0:
                continue
                
            delta = chunk.choices[0].delta
            
            # 🔍 Diagnostic Fallback Strategy Check
            # 1. Official Native Aliyun/DashScope Reasoning Stream Attributes
            reasoning_token = getattr(delta, "reasoning_content", None)
            
            # 2. Dictionary Fallback Lookup (In case attribute parsing strips it)
            if not reasoning_token and hasattr(delta, "get"):
                reasoning_token = delta.get("reasoning_content") or delta.get("reasoning")

            if reasoning_token:
                yield {"type": "thinking", "text": reasoning_token}
                continue

            # 3. Fallback check for standard text block elements
            token = getattr(delta, "content", None) or ""
            if not token:
                continue

            full_buffer += token

            # 4. Defensive Tag Checking (In case proxy endpoint wraps thoughts as text strings)
            if "<thinking>" in full_buffer and not inside_thinking:
                inside_thinking = True
                _, trailing = full_buffer.split("<thinking>", 1)
                full_buffer = ""  
                if trailing:
                    yield {"type": "thinking", "text": trailing}
                continue

            elif "</thinking>" in full_buffer and inside_thinking:
                inside_thinking = False
                thinking_chunk, trailing = full_buffer.split("</thinking>", 1)
                full_buffer = trailing  
                if thinking_chunk:
                    yield {"type": "thinking", "text": thinking_chunk}
                continue

            # Route tokens based on active parser fallback state settings
            if inside_thinking:
                yield {"type": "thinking", "text": token}
                full_buffer = ""
            else:
                if "<" not in full_buffer:
                    yield {"type": "content", "text": full_buffer}
                    full_buffer = ""

        # Final flush cleanup pass for content tail tokens left in the buffer
        if full_buffer:
            yield {"type": "content", "text": full_buffer}

    def _get_mock_fallback(self, user_prompt: str) -> str:
        """Fallback mock engine to keep your Phase 2 self-correction loop robust during offline testing."""
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
    """Initializes the minimal dev swarm crew with distinct engineering behaviors."""
    
    architect = QwenAgent(
        name="Software_Architect",
        instructions=(
            "You are a Software Architect. You break down complex feature requests "
            "into step-by-step modular designs and precise technical requirements tasks."
        )
    )
    
    coder = QwenAgent(
        name="Lead_Coder",
        instructions=(
            "You are an expert Developer Agent named Lead_Coder. Your job is to output pure, "
            "functional Python code matching requested specs. Provide raw code ONLY. Do not "
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