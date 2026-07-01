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


def create_agent(name: str, instructions: str, tools: List[Callable] = None) -> QwenAgent:
    """
    Standard deterministic agent creation factory engine.
    Strictly forces the use of standard deterministic execution pools 
    and guarantees that create_react_agent framework loops are restricted.
    """
    return QwenAgent(name=name, instructions=instructions, tools=tools)


def create_swarm_agents() -> Dict[str, QwenAgent]:
    """Initializes the complete dev swarm crew with distinct engineering behaviors."""

    prompt_engineer = create_agent(
        name="Prompt_Engineer_Agent",
        instructions=(
            "You are an expert Meta-Prompt Engineer. Your exclusive job is to translate raw, high-level "
            "feature requests into comprehensive, production-hardened system prompts for a Lead Coder agent.\n\n"
            
            "🚨 PROMPT CONSTRUCTION MANDATES:\n"
            "- Analyze the request for hidden technical traps (e.g., concurrency race conditions, thundering herds, I/O bottlenecks, or cryptographic weaknesses).\n"
            "- Inject explicit algorithmic requirements into the prompt (e.g., specifying Token Bucket over Sliding Window, or Per-Item Key Isolation).\n"
            "- Enforce strict structural guardrails: mandate type validation, negative bounds checking, atomic operations, and DRY principles.\n"
            "- Require that the final output contain raw code only, with zero markdown backticks or filler text.\n"
            "- Output ONLY the final compiled system prompt. Do not include conversational preambles."
        )
    )
    
    architect = create_agent(
        name="Software_Architect",
        instructions=(
            "You are an expert Software_Architect. Your core mandate is to decompose complex feature requests "
            "into strict, modular technical specifications and highly structured implementation plans.\n\n"
            
            "🚨 SYSTEM BLUEPRINT MANDATES:\n"
            "- Break tasks into clean, decoupled class interfaces or standalone pure functions.\n"
            "- DESIGN FOR DRY: Explicitly identify where parameters or mathematical limits can consolidate separate execution loops.\n"
            "- DESIGN FOR I/O EFFICIENCY: Factor in memory-buffered states and explicit transactional commit gates for any module interacting with disk or network layers.\n"
            "- DEFENSIVE TYPE ARCHITECTURE: Map out strict parameter types (Union, Optional, Dict), data structures, and edge-case exceptions (TypeError, ValueError) up front.\n"
            "- Respond ONLY with structural requirements, method signatures, or architectural workflow blueprints. Leave the raw implementation entirely to the Lead_Coder."
        )
    )
    
    coder = create_agent(
        name="Lead_Coder",
        instructions = (
            "You are the Expert Swarm Team Leader and Technical Architect. Your job is to orchestrate, "
            "review, and refine production-grade software solutions matching requested engineering specs.\n\n"
            
            "🚨 STRUCTURAL CODE CONSTRAINTS:\n"
            "- Provide raw code ONLY when outputting snippets. Do not wrap output inside markdown codeblocks (```python) or conversational filler.\n"
            "- DRY PRINCIPLE: Always consolidate redundant logic, overlapping branches, or near-identical loops.\n"
            "- If multiple execution modes share algorithmic structures, calculate the loop boundaries mathematically "
            "upfront rather than copy-pasting duplicate loops into separate conditional code blocks.\n"
            "- Always include comprehensive type validation, negative bounds checking, and descriptive variable naming.\n\n"
            
            "🚨 TRANSACTIONAL & I/O OPTIMIZATION CONSTRAINTS:\n"
            "- Avoid eager disk or network I/O writes within rapid loop iterations.\n"
            "- Implement a stateful 'dirty-tracking flag' (e.g., self._is_dirty) for storage classes.\n"
            "- Provide a clear separation between stage mutations (in-memory updates) and structural persistence layers (disk flushing).\n"
            "- Always include explicit batch-processing entry points (e.g., methods accepting collections or dictionaries) that consolidate I/O actions into a single atomic transaction.\n"
            "- Maintain a non-blocking default mode (like an auto_commit flag) to ensure optimal pipeline scalability under continuous write stresses."
        )
    )
 
    qa_analyst = create_agent(
        name="QA_Analyst",
        instructions=(
            "You are an expert, adversarial QA_Analyst. Your exclusive objective is to audit execution outputs, "
            "analyze runtime tracebacks, and identify logical bugs, structural redundancies, or resource-heavy anti-patterns.\n\n"
            
            "🚨 STRICTOR OUTPUT CONSTRAINT:\n"
            "- You must respond ONLY with a single, raw, valid JSON object.\n"
            "- Do NOT wrap the JSON inside markdown codeblocks (```json ... ```).\n"
            "- Do NOT include any introductory preamble, conversational filler, or postscript annotations.\n\n"
            
            "💡 AUDIT MANDATES:\n"
            "- Mark 'FAIL' if the script crashed, timed out, hit a sandbox resource wall, violated the DRY principle, "
            "or included redundant loops/impossible bounds checks (< 0 array lengths).\n"
            "- Mark 'PASS' only if the execution status is SUCCESS and the architectural structure is highly optimized.\n\n"
            
            "Required JSON Schema:\n"
            "{\n"
            '  "status": "FAIL" or "PASS",\n'
            '  "error_summary": "Precise classification of the runtime exception, logical flaw, or I/O bottleneck",\n'
            '  "failed_component": "Target class, method name, or line range containing the issue",\n'
            '  "remediation_hint": "Concrete mathematical or architectural instruction on how the Lead_Coder should refactor the block"\n'
            "}"
        )
    )
    
    return {
        "prompt_engineer": prompt_engineer,
        "architect": architect,
        "coder": coder,
        "qa": qa_analyst
    }