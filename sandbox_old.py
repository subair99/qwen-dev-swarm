import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Conditionally import resource module to maintain clean platform independence
try:
    import resource
except ImportError:
    resource = None


def _set_sandbox_limits(max_mem_bytes: int):
    """
    Child process pre-execution hook to restrict runtime operating limits.
    Executes directly inside the child context before dropping into execve().
    """
    if resource is not None:
        try:
            # Enforce hard/soft limit restrictions on Virtual Memory Address Space (RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (max_mem_bytes, max_mem_bytes))
        except Exception as e:
            # Graceful degraded fallback if kernel permissions restrict modifications
            pass


def run_in_sandbox(
    script_path: str | Path, 
    timeout: float = 10.0, 
    max_memory_mb: int = 256
) -> Dict[str, Any]:
    """
    Executes a script in an isolated local subprocess sandbox with strict resource bounds.
    
    Args:
        script_path: The path to the Python script or command file to run.
        timeout: Maximum execution time in seconds to prevent infinite loops.
        max_memory_mb: RAM limit in megabytes before process termination triggers.
        
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

    # Determine structural keyword args based on OS compatibility flags
    kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout
    }

    # Assign preexec_fn process limit hook only on POSIX systems (Linux/macOS)
    if os.name != "nt":
        kwargs["preexec_fn"] = lambda: _set_sandbox_limits(max_mem_bytes)

    try:
        # Run the script securely, capturing all standard outputs under active resource guard
        result = subprocess.run(
            [python_executable, str(path)],
            **kwargs
        )
        
        # Check if process crashed due to memory limits (Exit code 137 or MemoryError string)
        is_mem_err = "MemoryError" in result.stderr or result.returncode == -9 or result.returncode == 137
        status_flag = "MEMORY_EXHAUSTED" if is_mem_err else ("SUCCESS" if result.returncode == 0 else "RUNTIME_ERROR")
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": status_flag
        }

    except subprocess.TimeoutExpired as e:
        # Prevent runaway agent loops from stalling orchestrator core execution threads
        return {
            "exit_code": -1,
            "stdout": e.stdout if e.stdout else "",
            "stderr": f"Execution timed out after {timeout} seconds.",
            "status": "TIMEOUT"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"An unexpected sandbox error occurred: {str(e)}",
            "status": "SANDBOX_EXCEPTION"
        }


def parse_stderr(stderr_content: str) -> str:
    """
    Cleans up and extracts the vital traceback lines from Python's stderr.
    This saves token budget and removes noise for the QA agent.
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
            
    # If standard traceback formatting wasn't found, return the raw error lines
    if not relevant_lines:
        return "\n".join(lines[-3:]) # Fallback to the last 3 rows (usually the error message)
        
    return "\n".join(relevant_lines)