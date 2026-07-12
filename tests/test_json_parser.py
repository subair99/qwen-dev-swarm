# tests/test_json_parser.py
# run with: uv run pytest tests/test_json_parser.py -v

"""
Tests for the Robust QA JSON Parser.

This suite verifies that the orchestrator's parse_qa_feedback function 
can handle perfect JSON, markdown-wrapped JSON, conversational filler, 
and completely broken LLM outputs without crashing.
"""
import pytest
import sys
import os

# Ensure the root directory is in the path so imports work from the tests/ folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import parse_qa_feedback


class TestQaJsonParser:
    """Tests the multi-stage JSON parser and heuristic fallback."""

    # --- 1. Perfect & Standard Formats ---

    def test_perfect_json(self):
        """Verifies parsing of a perfectly formatted JSON string."""
        raw = '{"status": "PASS", "error_summary": "None", "failed_component": "None", "remediation_hint": "All good."}'
        result = parse_qa_feedback(raw)
        
        assert result["status"] == "PASS"
        assert result["error_summary"] == "None"

    def test_markdown_wrapped_json(self):
        """Verifies parsing when the LLM wraps JSON in markdown code blocks."""
        # Fixed: Using standard string with \n to prevent triple-quote/backtick syntax clashes
        raw = "Here is the analysis:\n```json\n{\n  \"status\": \"FAIL\",\n  \"error_summary\": \"Index out of bounds\",\n  \"failed_component\": \"line 42\",\n  \"remediation_hint\": \"Check array length\"\n}\n```\nHope this helps!"
        
        result = parse_qa_feedback(raw)
        assert result["status"] == "FAIL"
        assert result["error_summary"] == "Index out of bounds"

    def test_conversational_filler_with_json(self):
        """Verifies parsing when the LLM adds conversational text around the JSON."""
        raw = "Sure! I analyzed the code. {\"status\": \"FAIL\", \"error_summary\": \"Typo\", \"failed_component\": \"var x\", \"remediation_hint\": \"Fix typo\"} Let me know if you need more help."
        result = parse_qa_feedback(raw)
        
        assert result["status"] == "FAIL"
        assert result["error_summary"] == "Typo"

    # --- 2. Edge Cases & Empty Inputs ---

    def test_empty_string_input(self):
        """Verifies graceful handling of an empty string."""
        result = parse_qa_feedback("")
        assert result["status"] == "FAIL"
        assert "Empty QA response" in result["error_summary"]

    def test_none_input(self):
        """Verifies graceful handling of NoneType input."""
        result = parse_qa_feedback(None)
        assert result["status"] == "FAIL"
        assert "Empty QA response" in result["error_summary"]

    # --- 3. Broken & Malformed JSON (Heuristic Fallback) ---

    def test_truncated_json(self):
        """Verifies the parser doesn't crash on truncated JSON and uses heuristics."""
        raw = '{"status": "FAIL", "error_sum'
        result = parse_qa_feedback(raw)
        
        # Should fall back to heuristic. Since it contains "FAIL", it should be FAIL.
        assert result["status"] == "FAIL"
        assert "QA parsing failed" in result["error_summary"]

    def test_invalid_json_values(self):
        """Verifies handling of JSON with invalid values (e.g., unquoted strings)."""
        raw = '{"status": FAIL, "error_summary": None}'
        result = parse_qa_feedback(raw)
        
        # json.loads will fail, regex will fail, bracket extraction will fail.
        # Falls back to heuristic.
        assert result["status"] == "FAIL"

    def test_heuristic_fallback_pass(self):
        """Verifies the heuristic correctly identifies a PASS when JSON is totally broken."""
        raw = "I looked at the code and it looks good. No errors found. Perfect execution."
        result = parse_qa_feedback(raw)
        
        assert result["status"] == "PASS"
        assert "heuristic analysis" in result["remediation_hint"].lower()

    def test_heuristic_fallback_fail(self):
        """Verifies the heuristic correctly identifies a FAIL when JSON is totally broken."""
        raw = "There was a massive exception in the traceback. The bug is in the loop."
        result = parse_qa_feedback(raw)
        
        assert result["status"] == "FAIL"
        assert "raw feedback" in result["error_summary"]

    def test_mixed_heuristic_signals(self):
        """Verifies heuristic behavior when both pass and fail keywords are present."""
        # "error" is present, so is_fail will be True. 
        raw = "The code passed the first test, but there was an error in the second."
        result = parse_qa_feedback(raw)
        
        # Because is_fail is True, it defaults to FAIL in the heuristic logic
        assert result["status"] == "FAIL"