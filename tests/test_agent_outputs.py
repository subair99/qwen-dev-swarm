# tests/test_agent_outputs.py
# run with : uv run pytest tests/test_agent_outputs.py -v

"""
Tests for Agent Outputs, Prompt Compliance, and Streaming Mechanics.

This suite verifies that the swarm agents are initialized correctly,
that their outputs adhere to structural mandates (like docstrings and stdlib),
and that the StreamParser correctly isolates thinking tags from code.
"""
import ast
import re
import pytest
import sys
import os

# Ensure the root directory is in the path so imports work from the tests/ folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swarm.agents import create_swarm_agents, StreamParser


# ==============================================================================
# 1. Agent Initialization & Prompt Integrity
# ==============================================================================

class TestAgentInitialization:
    """Verifies that the swarm crew is fully assembled and configured."""

    def test_all_agents_present(self):
        """Ensures all 8 specialized agents are instantiated."""
        agents = create_swarm_agents()
        expected_agents = [
            "prompt_engineer", "architect", "coder", "qa_analyst", 
            "code_reviewer", "test_generator", "security_auditor", "documentation_agent"
        ]
        for agent_name in expected_agents:
            assert agent_name in agents, f"Missing agent: {agent_name}"

    def test_agents_have_instructions(self):
        """Ensures no agent has an empty or missing system prompt."""
        agents = create_swarm_agents()
        for name, agent in agents.items():
            assert agent.instructions, f"Agent '{name}' has empty instructions."
            assert len(agent.instructions) > 50, f"Agent '{name}' instructions are suspiciously short."

    def test_coder_has_stdlib_mandate(self):
        """Verifies the Lead Coder is explicitly forbidden from using external libraries."""
        agents = create_swarm_agents()
        coder_prompt = agents["coder"].instructions
        assert "STANDARD LIBRARY ONLY" in coder_prompt
        assert "pandas" in coder_prompt.lower() or "numpy" in coder_prompt.lower()


# ==============================================================================
# 2. Structural & Prompt Compliance (Post-Processing)
# ==============================================================================

class TestStructuralCompliance:
    """Tests the regex and AST checks used to enforce agent mandates."""

    def test_mandatory_docstring_regex(self):
        """Verifies the regex correctly identifies missing module docstrings."""
        valid_code_1 = '"""Module docstring."""\nimport os'
        valid_code_2 = '   """Module docstring."""\nimport os'
        valid_code_3 = '"""Module docstring."""'
        
        invalid_code_1 = 'import os\n"""Docstring"""'
        invalid_code_2 = '# Comment\nimport os'
        invalid_code_3 = 'def hello():\n    """Function docstring"""'

        assert re.match(r'^\s*"""', valid_code_1)
        assert re.match(r'^\s*"""', valid_code_2)
        assert re.match(r'^\s*"""', valid_code_3)
        
        assert not re.match(r'^\s*"""', invalid_code_1)
        assert not re.match(r'^\s*"""', invalid_code_2)
        assert not re.match(r'^\s*"""', invalid_code_3)

    def test_ast_banned_imports_detection(self):
        """Verifies AST parsing correctly flags banned external libraries."""
        banned_code = """
import pandas as pd
from requests import get
import os
import math
"""
        tree = ast.parse(banned_code)
        imported_modules = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split('.')[0])

        banned_libs = {"pandas", "requests", "numpy", "pydantic"}
        violations = imported_modules.intersection(banned_libs)
        
        assert "pandas" in violations
        assert "requests" in violations
        assert "os" not in violations # Standard lib should not be flagged
        assert "math" not in violations


# ==============================================================================
# 3. StreamParser Mechanics (Crucial for UI Streaming)
# ==============================================================================

class TestStreamParser:
    """Tests the non-blocking state machine that parses LLM streams."""

    def test_basic_thinking_isolation(self):
        """Verifies standard thinking tags are correctly isolated."""
        parser = StreamParser()
        tokens = ["<thinking>", "I need to", " write code", "</thinking>", "Here is the code:"]
        
        results = []
        for t in tokens:
            results.extend(parser.process(t))
        results.extend(parser.flush()) # <--- CRITICAL FIX: Empty the safe_len buffer
            
        thinking_text = "".join([text for type_, text in results if type_ == "thinking"])
        content_text = "".join([text for type_, text in results if type_ == "content"])
        
        assert "I need to write code" in thinking_text
        assert "Here is the code:" in content_text

    def test_code_block_less_than_symbol(self):
        """Verifies the parser doesn't hang when code contains '<' (e.g., 'if a < b:')."""
        parser = StreamParser()
        tokens = ["if a ", "< ", "b:", " pass"]
        
        results = []
        for t in tokens:
            results.extend(parser.process(t))
        results.extend(parser.flush()) # <--- CRITICAL FIX
            
        content_text = "".join([text for type_, text in results if type_ == "content"])
        assert "if a < b: pass" in content_text

    def test_flush_remaining_buffer(self):
        """Verifies that unclosed tags or trailing text are flushed at the end of the stream."""
        parser = StreamParser()
        results = parser.process("<thinking>Unclosed thought")
        results.extend(parser.flush()) # Combine process and flush results
        
        thinking_text = "".join([text for type_, text in results if type_ == "thinking"])
        assert thinking_text == "Unclosed thought"

    def test_multiple_thinking_blocks(self):
        """Verifies the parser can handle multiple sequential thinking blocks."""
        parser = StreamParser()
        stream = "<thinking>First thought</thinking> Code <thinking>Second thought</thinking> More code"
        
        results = []
        # Feed character by character to stress test the buffer
        for char in stream:
            results.extend(parser.process(char))
        results.extend(parser.flush()) # <--- CRITICAL FIX
            
        thinking_text = "".join([text for type_, text in results if type_ == "thinking"])
        content_text = "".join([text for type_, text in results if type_ == "content"])
        
        assert "First thought" in thinking_text
        assert "Second thought" in thinking_text
        assert "Code" in content_text
        assert "More code" in content_text