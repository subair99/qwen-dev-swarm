import os
import sys
import subprocess
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any

# ─────────────────────────────────────────────────────────────
# 🤖 AUTOMATIC DOCKER IMAGE BUILDER
# ─────────────────────────────────────────────────────────────
def _ensure_sandbox_image():
    """Checks if the Docker image exists and builds it if missing."""
    image_name = "qwen-dev-swarm-sandbox:latest"
    dockerfile_path = "Dockerfile.sandbox"
    
    try:
        # 1. Check if image exists
        check_result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True, text=True
        )
        
        if check_result.returncode != 0:
            print(f"📦 Sandbox image missing. Building '{image_name}' automatically...")
            
            # 2. Build the image
            build_result = subprocess.run(
                ["docker", "build", "-t", image_name, "-f", dockerfile_path, "."],
                capture_output=True, text=True
            )
            
            if build_result.returncode != 0:
                print(f" Failed to build Docker image:\n{build_result.stderr}")
                sys.exit(1)
            print("✅ Sandbox image built successfully!")
        else:
            print(f"✅ Sandbox image '{image_name}' is ready.")
            
    except FileNotFoundError:
        print("❌ Docker command not found. Is Docker installed and in your PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        sys.exit(1)

# Run the check immediately when sandbox.py is imported
_ensure_sandbox_image()
# ─────────────────────────────────────────────────────────────

# Setup logger for the sandbox module
logger = logging.getLogger(__name__)


def check_docker_installed():
    """Ensure Docker is available on the host system."""
    if shutil.which("docker") is None:
        raise EnvironmentError(
            "Docker is required for secure sandbox execution. "
            "Please install Docker Desktop or Docker Engine."
        )


def run_in_sandbox(
    script_path: str | Path, 
    timeout: float = 10.0, 
    max_memory_mb: int = 256,
    max_output_bytes: int = 1_000_000,  # 1MB limit on stdout/stderr
    command: list[str] | None = None    # <--- NEW PARAMETER
) -> Dict[str, Any]:
    """
    Executes a script in a strictly isolated Docker container.
    
    SECURITY FEATURES:
    - True OS-level isolation via Docker namespaces and cgroups.
    - Network disabled (prevents data exfiltration).
    - Read-only root filesystem.
    - Non-root user execution.
    - Strict resource limits (memory, CPU, PIDs).
    - Environment variables are NOT inherited from the host (implicit sanitization).
    
    Args:
        script_path: The path to the Python script or command file to run.
        timeout: Maximum execution time in seconds to prevent infinite loops.
        max_memory_mb: RAM limit in megabytes (mapped to Docker --memory flag).
        max_output_bytes: Maximum size of stdout/stderr to capture (prevents memory exhaustion).
        command: Optional list of strings to override the default execution command.
                 If None, defaults to ["python", "/workspace/{script_name}"].
        
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

    check_docker_installed()
    
    # 1. Prepare an isolated temporary workspace
    workspace_dir = tempfile.mkdtemp(prefix="qwen_sandbox_")
    script_name = os.path.basename(path)
    target_path = os.path.join(workspace_dir, script_name)
    
    # Copy the generated script to the workspace
    shutil.copy(path, target_path)
    
    # 2. Define Docker run command with strict security flags
    # Map max_memory_mb to Docker memory limit format (e.g., "256m")
    mem_limit = f"{max_memory_mb}m"
    
    # Determine the execution command
    if command is None:
        exec_cmd = ["python", f"/workspace/{script_name}"]
    else:
        exec_cmd = command

    docker_cmd = [
        "docker", "run",
        "--rm",                     # Auto-remove container after execution
        "--network", "none",        # 🛑 CRITICAL: Disable network (prevents data exfiltration)
        "--read-only",              # 🛑 CRITICAL: Read-only root filesystem
        "--security-opt", "no-new-privileges", # Prevent privilege escalation
        "--tmpfs", "/tmp:noexec,size=128M", # Writable space for /tmp only, no execution
        "--memory", mem_limit,      # Limit RAM (e.g., 256m)
        "--cpus", "1.0",            # Limit to 1 CPU core
        "--pids-limit", "64",       # Prevent fork bombs
        "--user", "1000:1000",      # Run as non-root user defined in Dockerfile
        "-v", f"{workspace_dir}:/workspace:ro", # Mount code as READ-ONLY
        "qwen-dev-swarm-sandbox:latest" # The image name we will build
    ] + exec_cmd  # <--- APPEND THE COMMAND HERE
    
    try:
        logger.info(f"Executing {script_name} in isolated Docker sandbox...")
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 3.0 # Add 3s buffer for container startup time
        )
        
        # Truncate output if it exceeds the limit (prevents memory exhaustion)
        stdout = result.stdout[:max_output_bytes] if result.stdout else ""
        stderr = result.stderr[:max_output_bytes] if result.stderr else ""
        
        # Check if process crashed due to memory limits (OOMKilled in Docker usually returns 137)
        is_mem_err = "MemoryError" in stderr or result.returncode == 137 or "OOM" in stderr
        status_flag = "MEMORY_EXHAUSTED" if is_mem_err else ("SUCCESS" if result.returncode == 0 else "RUNTIME_ERROR")
        
        return {
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "status": status_flag
        }
        
    except subprocess.TimeoutExpired as e:
        # Prevent runaway agent loops from stalling orchestrator core execution threads
        logger.warning(f"Sandbox execution timed out after {timeout} seconds.")
        stdout = (e.stdout or "")[:max_output_bytes]
        stderr = f"Execution timed out after {timeout} seconds."
        return {
            "exit_code": -1,
            "stdout": stdout,
            "stderr": stderr,
            "status": "TIMEOUT"
        }
    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"An unexpected sandbox error occurred: {str(e)}",
            "status": "SANDBOX_EXCEPTION"
        }
    finally:
        # 3. Clean up workspace
        shutil.rmtree(workspace_dir, ignore_errors=True)


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