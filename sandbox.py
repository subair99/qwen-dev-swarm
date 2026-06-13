import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def run_in_sandbox(script_path: str | Path, timeout: float = 10.0) -> Dict[str, Any]:
    """
    Executes a script in a local subprocess sandbox and captures its output.
    
    Args:
        script_path: The path to the Python script or command file to run.
        timeout: Maximum execution time in seconds to prevent infinite loops.
        
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

    try:
        # Run the script securely, capturing all standard outputs
        result = subprocess.run(
            [python_executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "SUCCESS" if result.returncode == 0 else "RUNTIME_ERROR"
        }

    except subprocess.TimeoutExpired as e:
        # Prevent runaway agent scripts from consuming local resources
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