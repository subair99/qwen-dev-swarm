# swarm/agents.py
import json
import inspect
import re
from typing import List, Dict, Any, Callable, Generator, Optional
from openai import OpenAI

# ✅ CENTRALIZED CONFIGURATION IMPORTS
# These are now strictly enforced to come from the .env file via config.py
from config import QWEN_API_KEY, QWEN_BASE_URL, MODEL_NAME, GUARDRAIL_MODEL_NAME


class StreamParser:
    """
    A non-blocking state machine to parse <thinking> tags from a text stream.
    It only buffers up to the length of the tag minus 1, ensuring that 
    '<' characters in code (like 'a < b') are yielded immediately without blocking.
    """
    def __init__(self):
        self.buffer = ""
        self.inside_thinking = False
        self.thinking_tag = "<thinking>"
        self.end_thinking_tag = "</thinking>"

    def process(self, token: str) -> List[tuple]:
        self.buffer += token
        results = []
        
        while True:
            if self.inside_thinking:
                idx = self.buffer.find(self.end_thinking_tag)
                if idx != -1:
                    results.append(("thinking", self.buffer[:idx]))
                    self.buffer = self.buffer[idx + len(self.end_thinking_tag):]
                    self.inside_thinking = False
                else:
                    # Keep only the last len(tag)-1 chars in buffer to prevent blocking
                    safe_len = len(self.end_thinking_tag) - 1
                    if len(self.buffer) > safe_len:
                        results.append(("thinking", self.buffer[:-safe_len]))
                        self.buffer = self.buffer[-safe_len:]
                    break
            else:
                idx = self.buffer.find(self.thinking_tag)
                if idx != -1:
                    if idx > 0:
                        results.append(("content", self.buffer[:idx]))
                    self.buffer = self.buffer[idx + len(self.thinking_tag):]
                    self.inside_thinking = True
                else:
                    safe_len = len(self.thinking_tag) - 1
                    if len(self.buffer) > safe_len:
                        results.append(("content", self.buffer[:-safe_len]))
                        self.buffer = self.buffer[-safe_len:]
                    break
        return results

    def flush(self) -> List[tuple]:
        if self.buffer:
            type_ = "thinking" if self.inside_thinking else "content"
            return [(type_, self.buffer)]
        return []


class QwenAgent:
    def __init__(
        self, 
        name: str, 
        instructions: str, 
        tools: Optional[List[Callable]] = None,
        mock_fallback: Optional[Callable[[str], str]] = None
    ):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.mock_fallback = mock_fallback
        
        # ✅ USE CENTRALIZED CONFIGURATION DIRECTLY
        self.base_url = QWEN_BASE_URL
        self.api_key = QWEN_API_KEY
        self.model_name = MODEL_NAME
        self.guardrail_model_name = GUARDRAIL_MODEL_NAME
        
        # Guardrail check: Fail fast if environment variables fail to load
        if not self.api_key:
            raise ValueError(f"Critical: QWEN_API_KEY is missing in config for agent: {self.name}")
        
        # Initialize the OpenAI wrapper client
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        # Pre-process tools into OpenAI schema format
        self.tool_schemas = self._generate_tool_schemas(self.tools)

    def _generate_tool_schemas(self, tools: List[Callable]) -> List[Dict[str, Any]]:
        """Converts Python callables into OpenAI tool schemas using inspect."""
        schemas = []
        for func in tools:
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                param_type = "string" # default
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation in (list, List):
                        param_type = "array"
                    elif param.annotation in (dict, Dict):
                        param_type = "object"
                
                properties[param_name] = {"type": param_type}
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
                    
            schemas.append({
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return schemas

    def _execute_tool(self, name: str, arguments: str) -> str:
        """Executes a tool by name with the provided JSON arguments."""
        tool_map = {t.__name__: t for t in self.tools}
        if name not in tool_map:
            return json.dumps({"error": f"Tool {name} not found"})
        
        try:
            args_dict = json.loads(arguments)
            result = tool_map[name](**args_dict)
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def call_llm(self, user_prompt: str, require_json: bool = False) -> str:
        """
        Executes a blocking inference call to the Qwen model.
        Includes tool calling support and thinking preservation.
        """
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            # DashScope standard for QwQ/Qwen3 thinking models
            "extra_body": {"enable_thinking": True} 
        }

        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        if self.tool_schemas:
            kwargs["tools"] = self.tool_schemas
            kwargs["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            
            # Handle tool calls loop
            if message.tool_calls:
                messages.append(message)
                for tool_call in message.tool_calls:
                    result = self._execute_tool(tool_call.function.name, tool_call.function.arguments)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                
                # Recursive call to get final response after tool execution
                kwargs.pop("tools", None)
                kwargs.pop("tool_choice", None)
                kwargs["messages"] = messages
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
                
            return message.content
            
        except Exception as e:
            print(f"⚠️ OpenAI Client Error on {self.name}: {e}")
            if self.mock_fallback:
                return self.mock_fallback(user_prompt)
            raise

    def call_llm_stream(self, user_prompt: str, require_json: bool = False) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a real-time streaming inference call.
        Uses a non-blocking state machine to cleanly isolate <thinking> tags 
        without blocking the stream on standard '<' characters in code.
        """
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "stream": True,
            "stream_options": {"include_usage": True},
            "extra_body": {"enable_thinking": True}
        }

        if require_json:
            kwargs["response_format"] = {"type": "json_object"}

        if self.tool_schemas:
            kwargs["tools"] = self.tool_schemas
            kwargs["tool_choice"] = "auto"

        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            print(f"⚠️ Streaming Error on {self.name}: {e}")
            if self.mock_fallback:
                yield {"type": "content", "text": self.mock_fallback(user_prompt)}
            return

        parser = StreamParser()
        tool_calls_buffer = {}

        for chunk in stream:
            if not getattr(chunk, "choices", None) or len(chunk.choices) == 0:
                continue
                
            delta = chunk.choices[0].delta
            
            # 1. Native Reasoning Token (DashScope standard for QwQ/Qwen3)
            reasoning_token = getattr(delta, "reasoning_content", None)
            if reasoning_token:
                yield {"type": "thinking", "text": reasoning_token}
                continue

            # 2. Tool Calls (Streaming)
            if getattr(delta, "tool_calls", None):
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id: tool_calls_buffer[idx]["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name: tool_calls_buffer[idx]["name"] += tc_delta.function.name
                    if tc_delta.function and tc_delta.function.arguments: tool_calls_buffer[idx]["arguments"] += tc_delta.function.arguments
                continue

            # 3. Standard Content Token
            token = getattr(delta, "content", None) or ""
            if not token:
                continue

            # Process through non-blocking state machine
            for type_, text in parser.process(token):
                yield {"type": type_, "text": text}

        # Flush remaining buffer
        for type_, text in parser.flush():
            yield {"type": type_, "text": text}

        # Yield tool calls at the end
        for idx, tc in tool_calls_buffer.items():
            yield {"type": "tool_call", "id": tc["id"], "name": tc["name"], "arguments": tc["arguments"]}


def extract_code_from_markdown(text: str) -> str:
    """Extracts code from markdown blocks, falling back to raw text."""
    match = re.search(r'```(?:python)?\n(.*?)```', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def create_agent(
    name: str, 
    instructions: str, 
    tools: Optional[List[Callable]] = None,
    mock_fallback: Optional[Callable[[str], str]] = None
) -> QwenAgent:
    """Standard deterministic agent creation factory engine."""
    return QwenAgent(
        name=name, 
        instructions=instructions, 
        tools=tools,
        mock_fallback=mock_fallback
    )


def create_swarm_agents() -> Dict[str, QwenAgent]:
    """Initializes the complete dev swarm crew with distinct engineering behaviors."""

    prompt_engineer = create_agent(
        name="Prompt_Engineer_Agent",
        instructions=(
            "You are an expert Meta-Prompt Engineer. Your exclusive job is to translate raw, high-level "
            "feature requests into comprehensive, production-hardened system prompts for a Lead Coder agent.\n\n"
            "PROMPT CONSTRUCTION MANDATES:\n"
            "- Analyze the request for hidden technical traps (e.g., concurrency race conditions, I/O bottlenecks).\n"
            "- Inject explicit algorithmic requirements into the prompt.\n"
            "- Enforce strict structural guardrails: mandate type validation, negative bounds checking, and DRY principles.\n"
            "- Output ONLY the final compiled system prompt. Do not include conversational preambles."
        )
    )
    
    architect = create_agent(
        name="Software_Architect",
        instructions=(
            "You are an expert Software Architect. Your core mandate is to decompose complex feature requests "
            "into strict, modular technical specifications and highly structured implementation plans.\n\n"
            "SYSTEM BLUEPRINT MANDATES:\n"
            "- Break tasks into clean, decoupled class interfaces or standalone pure functions.\n"
            "- DESIGN FOR DRY: Explicitly identify where parameters or mathematical limits can consolidate separate execution loops.\n"
            "- DESIGN FOR I/O EFFICIENCY: Factor in memory-buffered states and explicit transactional commit gates.\n"
            "- DEFENSIVE TYPE ARCHITECTURE: Map out strict parameter types and edge-case exceptions up front.\n"
            "- TESTING ARCHITECTURE: Mandate that all test suites must be DETERMINISTIC. "
            "Explicitly forbid time-based assertions (e.g., assertLess with elapsed time, time.time() comparisons) "
            "as they cause flaky tests on CI. Instead, require correctness-based assertions that verify actual values.\n"
            "- Require test coverage for: boundary values (0, 1, 2), known reference values (e.g., fib(10)=55, fib(20)=6765), "
            "type rejections (including booleans), and negative bounds.\n"
            "- Respond ONLY with structural requirements, method signatures, or architectural workflow blueprints."
        )
    )
    
    coder = create_agent(
        name="Lead_Coder",
        instructions=(
            "You are an expert Software Engineer and Technical Architect. Your task is to write production-grade, "
            "highly optimized code based on the provided architectural specifications.\n\n"
            "CORE DIRECTIVES:\n"
            "1. DRY & MODULARITY: Consolidate redundant logic. If multiple execution modes share algorithmic "
            "structures, calculate loop boundaries mathematically upfront rather than duplicating code blocks.\n"
            "2. DEFENSIVE PROGRAMMING: Include strict type validation, bounds checking, and explicit error "
            "handling (TypeError, ValueError) for all edge cases.\n"
            "3. I/O OPTIMIZATION: Avoid eager disk/network writes in loops. Implement stateful dirty-tracking "
            "(e.g., self._is_dirty) and batch-processing entry points to consolidate I/O into single atomic transactions.\n"
            "4. TESTING QUALITY: All tests must be deterministic. Never use time-based assertions. "
            "Verify actual output values, not just counts or lengths. Include tests for boundary values, "
            "known reference values, type rejections, and edge cases.\n"
            "5. FORMATTING: Always wrap your code in standard markdown code blocks (```python ... ```). "
            "Do not include conversational filler before or after the code block."
            "6. STANDARD LIBRARY ONLY: You are executing in a strictly isolated Docker sandbox. "
            "You MUST ONLY use Python standard library modules (e.g., os, sys, json, math, re). "
            "DO NOT import external libraries like requests, pandas, numpy, or bs4, as they will cause an immediate crash."
            "7. NO TEST IMPORTS IN MAIN SCRIPT: Never import 'pytest' or any testing frameworks in the main generated script. "
            "The main script must contain ONLY the core logic and execution code. Testing logic will be handled separately."
        )
    )
 
    qa_analyst = create_agent(
        name="QA_Analyst",
        instructions=(
            "You are an expert, adversarial QA Analyst and Code Reviewer. Your objective is to audit "
            "execution outputs, analyze runtime tracebacks, and identify logical bugs, structural "
            "redundancies, resource-heavy anti-patterns, AND testing deficiencies.\n\n"
            
            "AUDIT MANDATES:\n"
            "- Mark 'FAIL' if the script crashed, timed out, violated the DRY principle, or included "
            "redundant loops.\n"
            "- Mark 'FAIL' if the test suite contains FLAKY TESTS (e.g., time-based assertions that "
            "will fail on slow CI machines, use of time.time() or time.sleep() in assertions).\n"
            "- Mark 'FAIL' if the test suite lacks CORRECTNESS TESTS for larger/edge-case values "
            "(e.g., only testing fib(0), fib(1), fib(2) but not fib(10)=55 or fib(20)=6765).\n"
            "- Mark 'FAIL' if tests only verify counts/lengths but not actual output values "
            "(e.g., checking len(result) but not result itself).\n"
            "- Mark 'FAIL' if type validation tests don't explicitly reject booleans (True/False).\n"
            "- Mark 'PASS' only if the execution status is SUCCESS, the architecture is optimized, "
            "AND the test suite is comprehensive, deterministic, and verifies actual values.\n\n"
            
            "OUTPUT FORMAT:\n"
            "Respond with a valid JSON object matching the following schema:\n"
            "{\n"
            '  "status": "FAIL" or "PASS",\n'
            '  "error_summary": "Precise classification of the issue",\n'
            '  "failed_component": "Target class, method name, or line range",\n'
            '  "remediation_hint": "Concrete instruction on how to fix"\n'
            "}"
        )
    )
    
    code_reviewer = create_agent(
        name="Code_Reviewer",
        instructions=(
            "You are an expert Code Reviewer specializing in test quality, CI reliability, and code correctness. "
            "Your job is to scan generated code for common anti-patterns and testing deficiencies BEFORE it reaches "
            "the QA Analyst.\n\n"
            
            "CHECK FOR:\n"
            "1. FLAKY TESTS: Any use of time.time(), time.sleep(), or assertLess/assertGreater with elapsed time "
            "in test assertions. These cause non-deterministic test failures on CI.\n"
            "2. WEAK ASSERTIONS: Tests that only check length/count/size but not actual values. "
            "For example, checking len(result) == 5 but not verifying result == [1, 2, 3, 4, 5].\n"
            "3. MISSING EDGE CASES: No tests for boundary values (0, 1, empty inputs), type rejections "
            "(especially booleans which are technically ints in Python), or negative/invalid inputs.\n"
            "4. MISLEADING COMMENTS: Comments that contradict the code, make unsupported performance claims, "
            "or describe behavior that doesn't match the implementation.\n"
            "5. MISSING REFERENCE VALUES: No tests against known correct outputs for larger inputs "
            "(e.g., no test that fib(10) == 55 or fib(20) == 6765).\n\n"
            
            "OUTPUT FORMAT:\n"
            "Respond with a JSON object:\n"
            "{\n"
            '  "issues_found": ["list", "of", "issues"],\n'
            '  "severity": "HIGH" or "MEDIUM" or "LOW",\n'
            '  "fix_instructions": "Detailed instructions for the Lead Coder"\n'
            "}\n\n"
            
            "If no issues are found, return:\n"
            "{\n"
            '  "issues_found": [],\n'
            '  "severity": "NONE",\n'
            '  "fix_instructions": "Code passes review."\n'
            "}"
        )
    )

    # ─────────────────────────────────────────────────────────────
    # 🆕 NEW AGENTS FOR SWARM EXPANSION
    # ─────────────────────────────────────────────────────────────
    test_generator = create_agent(
        name="Test_Generator_Agent",
        instructions=(
            "You are an expert Test Automation Engineer. Your task is to generate comprehensive, "
            "deterministic `pytest` unit tests based on the provided feature request and code implementation.\n\n"
            "TEST GENERATION MANDATES:\n"
            "- Generate tests that verify logical correctness, not just syntactic validity.\n"
            "- Include tests for boundary values, edge cases, and expected exceptions.\n"
            "- Ensure all tests are deterministic (no time-based assertions).\n"
            "- Output ONLY the python code for the test file, wrapped in ```python ... ```.\n"
            "- Do not include conversational filler."
        )
    )

    security_auditor = create_agent(
        name="Security_Auditor_Agent",
        instructions=(
            "You are an expert Application Security Engineer. Your task is to audit the generated code "
            "for security vulnerabilities before it is approved for execution.\n\n"
            "AUDIT MANDATES:\n"
            "- Scan for common vulnerabilities: SQL injection, XSS, insecure deserialization, hardcoded secrets, "
            "path traversal, and unsafe subprocess usage.\n"
            "- Evaluate the risk level of any findings.\n"
            "- Output a valid JSON object matching the following schema:\n"
            "{\n"
            '  "status": "PASS" or "FAIL",\n'
            '  "vulnerabilities": ["list of identified vulnerabilities"],\n'
            '  "risk_level": "HIGH", "MEDIUM", "LOW", or "NONE",\n'
            '  "remediation_hint": "Instructions on how to fix the vulnerabilities"\n'
            "}\n"
            "- If no vulnerabilities are found, return status PASS and empty vulnerabilities list."
        )
    )

    documentation_agent = create_agent(
        name="Documentation_Agent",
        instructions=(
            "You are an expert Technical Writer. Your task is to generate comprehensive documentation "
            "for the generated code to ensure it is production-ready.\n\n"
            "DOCUMENTATION MANDATES:\n"
            "- Generate detailed docstrings for all functions and classes.\n"
            "- Ensure strict type hints are present and correct.\n"
            "- Generate a comprehensive README.md that explains the purpose, usage, and dependencies of the code.\n"
            "- Output a valid JSON object with two keys:\n"
            "{\n"
            '  "documented_code": "The full python code with docstrings and type hints added",\n'
            '  "readme_md": "The content of the README.md file"\n'
            "}\n"
            "- Do not include conversational filler."
        )
    )
    
    return {
        "prompt_engineer": prompt_engineer,
        "architect": architect,
        "coder": coder,
        "qa_analyst": qa_analyst,
        "code_reviewer": code_reviewer,
        "test_generator": test_generator,
        "security_auditor": security_auditor,
        "documentation_agent": documentation_agent
    }