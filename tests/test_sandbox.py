# tests/test_sandbox.py
# run with: uv run pytest tests/test_sandbox.py -v

"""
Tests for Docker Sandbox Isolation and Security.

This suite verifies that the Docker sandbox enforces strict security boundaries,
including network isolation, read-only filesystems, and timeout enforcement.

NOTE: These tests require Docker to be running on your host machine.
"""
import os
import tempfile
import pytest
import sys

# Ensure the root directory is in the path so imports work from the tests/ folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sandbox import run_in_sandbox


# ==============================================================================
# Helper to safely execute code in the sandbox
# ==============================================================================

def run_sandbox_test(code: str, timeout: float = 5.0):
    """Writes code to a temp file, runs it in the sandbox, and cleans up."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        return run_in_sandbox(temp_path, timeout=timeout)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ==============================================================================
# 1. Happy Path Execution
# ==============================================================================

class TestSandboxHappyPath:
    """Verifies the sandbox can successfully execute standard Python code."""

    def test_basic_execution(self):
        """Ensures a simple print statement executes successfully."""
        code = """
print("SANDBOX_HELLO_WORLD")
"""
        result = run_sandbox_test(code, timeout=5.0)
        assert result["exit_code"] == 0
        assert "SANDBOX_HELLO_WORLD" in result["stdout"]


# ==============================================================================
# 2. Network Isolation
# ==============================================================================

class TestSandboxNetworkIsolation:
    """Verifies the sandbox has NO internet access (--network none)."""

    def test_network_blocked(self):
        """Attempts to make an HTTP request. Should fail due to network isolation."""
        code = """
import urllib.request
try:
    urllib.request.urlopen("http://1.1.1.1", timeout=2)
    print("NETWORK_ACCESS_GRANTED")
except Exception:
    print("NETWORK_BLOCKED")
"""
        result = run_sandbox_test(code, timeout=10.0)
        assert result["exit_code"] == 0
        assert "NETWORK_BLOCKED" in result["stdout"]
        assert "NETWORK_ACCESS_GRANTED" not in result["stdout"]


# ==============================================================================
# 3. Filesystem Read-Only Enforcement
# ==============================================================================

class TestSandboxFilesystem:
    """Verifies the sandbox root filesystem is read-only (--read-only)."""

    def test_filesystem_write_blocked(self):
        """Attempts to write to a protected directory. Should fail with PermissionError."""
        code = """
try:
    with open("/etc/sandbox_test_file", "w") as f:
        f.write("malicious payload")
    print("WRITE_GRANTED")
except PermissionError:
    print("WRITE_BLOCKED")
except Exception as e:
    print(f"WRITE_BLOCKED_BY_OTHER: {e}")
"""
        result = run_sandbox_test(code, timeout=5.0)
        assert result["exit_code"] == 0
        # It should be blocked by either PermissionError or Read-only filesystem error
        assert "WRITE_GRANTED" not in result["stdout"]
        assert "WRITE_BLOCKED" in result["stdout"]


# ==============================================================================
# 4. Timeout Enforcement
# ==============================================================================

class TestSandboxTimeout:
    """Verifies the sandbox kills infinite loops to prevent resource hogging."""

    def test_infinite_loop_timeout(self):
        """Runs an infinite loop. Should be killed by the timeout mechanism."""
        code = """
while True:
    pass
"""
        # Set a very short timeout to fail fast
        result = run_sandbox_test(code, timeout=3.0)
        
        # Exit code should be non-zero (usually -9 for SIGKILL or similar)
        assert result["exit_code"] != 0
        
        # Check for timeout indicators in stderr or message
        stderr_lower = result.get("stderr", "").lower()
        assert "timed out" in stderr_lower or "killed" in stderr_lower or result["exit_code"] < 0