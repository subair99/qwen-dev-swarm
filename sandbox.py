# sandbox.py
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Conditionally import resource module to maintain clean platform independence
try:
    import resource
except ImportError:
    resource = None

# Environment variables to exclude from the sandbox
_BLOCKED_ENV_VARS = {
    "QWEN_API_KEY",
    "DASHSCOPE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "DATABASE_URL",
    "SECRET_KEY",
}


def _set_sandbox_limits(max_mem_bytes: int, max_cpu_seconds: int, max_file_size_bytes: int):
    """
    Child process pre-execution hook to restrict runtime operating limits.
    Executes directly inside the child context before dropping into execve().
    
    WARNING: This function is not safe in multi-threaded applications.
    See Python docs for subprocess.preexec_fn.
    """
    if resource is None:
        return
        
    try:
        # Enforce hard/soft limit restrictions on Virtual Memory Address Space (RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (max_mem_bytes, max_mem_bytes))
        
        # CPU time limit (prevents infinite loops from consuming CPU forever)
        resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, max_cpu_seconds))
        
        # File size limit (prevents disk exhaustion)
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_size_bytes, max_file_size_bytes))
        
        # Process count limit (prevents fork bombs)
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        
    except Exception as e:
        # Graceful degraded fallback if kernel permissions restrict modifications
        pass


def _sanitize_environment() -> Dict[str, str]:
    """
    Creates a sanitized environment dictionary with sensitive variables removed.
    Prevents data exfiltration of API keys and secrets.
    """
    sanitized_env = {}
    for key, value in os.environ.items():
        if key not in _BLOCKED_ENV_VARS:
            sanitized_env[key] = value
    return sanitized_env


def run_in_sandbox(
    script_path: str | Path, 
    timeout: float = 10.0, 
    max_memory_mb: int = 256,
    max_output_bytes: int = 1_000_000  # 1MB limit on stdout/stderr
) -> Dict[str, Any]:
    """
    Executes a script in an isolated local subprocess sandbox with strict resource bounds.
    
    SECURITY LIMITATIONS:
    - This sandbox provides basic resource limiting but NOT full isolation.
    - The script still has access to the file system and network.
    - For production use with untrusted code, use Docker containers or WebAssembly.
    
    Args:
        script_path: The path to the Python script or command file to run.
        timeout: Maximum execution time in seconds to prevent infinite loops.
        max_memory_mb: RAM limit in megabytes before process termination triggers.
        max_output_bytes: Maximum size of stdout/stderr to capture (prevents memory exhaustion).
        
    Returns:
        A dictionary containing stdout, stderr, exit_code, and execution status.
    """
    path = Path(script_path)
    if not path.exists():
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Error: The target file '{path}' does not exist.",
            "status": "FILE_NOT_FOUND"
        }

    # Ensure we use the current uv/virtual environment executable if available
    python_executable = sys.executable
    max_mem_bytes = max_memory_mb * 1024 * 1024
    max_cpu_seconds = int(timeout) + 2  # Give 2s grace period for cleanup
    max_file_size_bytes = 10 * 1024 * 1024  # 10MB file size limit

    # Determine structural keyword args based on OS compatibility flags
    kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
        "stdin": subprocess.DEVNULL,  # Prevent hanging on input() calls
        "env": _sanitize_environment(),  # Remove sensitive environment variables
    }

    # Assign preexec_fn process limit hook only on POSIX systems (Linux/macOS)
    if os.name != "nt":
        # Use a proper function reference, not a lambda, to avoid closure issues
        def preexec_hook():
            _set_sandbox_limits(max_mem_bytes, max_cpu_seconds, max_file_size_bytes)
        kwargs["preexec_fn"] = preexec_hook

    try:
        # Run the script securely, capturing all standard outputs under active resource guard
        result = subprocess.run(
            [python_executable, str(path)],
            **kwargs
        )
        
        # Truncate output if it exceeds the limit (prevents memory exhaustion)
        stdout = result.stdout[:max_output_bytes] if result.stdout else ""
        stderr = result.stderr[:max_output_bytes] if result.stderr else ""
        
        # Check if process crashed due to memory limits (Exit code 137 or MemoryError string)
        is_mem_err = "MemoryError" in stderr or result.returncode == -9 or result.returncode == 137
        status_flag = "MEMORY_EXHAUSTED" if is_mem_err else ("SUCCESS" if result.returncode == 0 else "RUNTIME_ERROR")
        
        return {
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "status": status_flag
        }

    except subprocess.TimeoutExpired as e:
        # Prevent runaway agent loops from stalling orchestrator core execution threads
        stdout = (e.stdout or "")[:max_output_bytes]
        stderr = f"Execution timed out after {timeout} seconds."
        return {
            "exit_code": -1,
            "stdout": stdout,
            "stderr": stderr,
            "status": "TIMEOUT"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"An unexpected sandbox error occurred: {str(e)}",
            "status": "SANDBOX_EXCEPTION"
        }


def parse_stderr(stderr_content: str, max_lines: int = 50) -> str:
    """
    Cleans up and extracts the vital traceback lines from Python's stderr.
    This saves token budget and removes noise for the QA agent.
    
    Args:
        stderr_content: The raw stderr output from the subprocess.
        max_lines: Maximum number of traceback lines to return (prevents token waste).
    """
    if not stderr_content:
        return ""
        
    lines = stderr_content.strip().split("\n")
    relevant_lines = []
    
    # Flag to start capturing when the actual traceback starts
    capture = False
    
    for line in lines:
        if "Traceback (most recent call last):" in line:
            capture = True
            continue
        if capture:
            relevant_lines.append(line)
            # Stop if we've collected enough lines (prevents huge outputs)
            if len(relevant_lines) >= max_lines:
                relevant_lines.append(f"... (truncated, {len(lines) - max_lines} more lines)")
                break
            
    # If standard traceback formatting wasn't found, return the raw error lines
    if not relevant_lines:
        return "\n".join(lines[-5:])  # Fallback to the last 5 rows (usually the error message)
        
    return "\n".join(relevant_lines)