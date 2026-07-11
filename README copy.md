# 🚀 Qwen-Dev-Swarm

**An Autonomous, Security-Hardened Multi-Agent Code Generation & Self-Correction Engine powered by Qwen.**

Qwen-Dev-Swarm is a production-grade, multi-agent AI framework designed to autonomously generate, test, and debug complex Python scripts. By leveraging a specialized "swarm" of AI agents, a strictly isolated Docker execution sandbox, multi-layered security guardrails, and a real-time Streamlit dashboard, it transforms high-level feature requests into verified, production-ready code through iterative self-correction and mandatory human oversight.

---

## ✨ Key Features

- 🤖 **Expanded Specialized Agent Swarm**: A comprehensive crew of distinct roles collaborating to ensure high-quality output:
  - **Prompt Engineer**: Translates raw requests into hardened system prompts.
  - **Software Architect**: Decomposes complex features into modular, DRY technical specifications.
  - **Lead Coder**: Writes production-grade, defensively typed code.
  - **Code Reviewer**: Scans for anti-patterns, flaky tests, and weak assertions before execution.
  - **QA Analyst**: Adversarially audits execution outputs and tracebacks.
  - **Test Generator**: Creates comprehensive, deterministic `pytest` unit tests.
  - **Security Auditor**: Scans generated code for vulnerabilities (SQLi, XSS, path traversal, etc.).
  - **Documentation Agent**: Auto-generates docstrings, type hints, and READMEs.
- 🛡️ **True Docker Sandbox Isolation**: Executes generated code and tests in a strictly isolated, read-only, network-disabled Docker container with enforced memory, CPU, and PID limits.
- 🧠 **Multi-Layered Prompt Defense**: Defeats obfuscation and semantic jailbreaks using a 3-tier guardrail system (Input Normalization → Regex Heuristics → Semantic LLM Analysis).
- 🤝 **Mandatory Human-in-the-Loop (HITL) Approval**: Requires explicit human review and approval of generated code _before_ it is ever executed in the sandbox, ensuring zero-trust execution.
- 🧪 **Automated Test Generation & Execution**: Automatically generates and runs `pytest` suites to verify logical correctness, not just syntactic validity.
- 🕵️ **Pre-Execution Security Auditing**: Scans code for vulnerabilities and assesses risk levels before human approval.
- 📝 **Automated Documentation**: Generates comprehensive documentation, including docstrings and type hints, once code passes all tests.
- **Autonomous Self-Correction Loop**: Automatically detects runtime or test errors, analyzes tracebacks, and iteratively refactors code until it passes the sandbox.
- 📊 **Robust QA Parsing**: Features a multi-stage JSON parser with heuristic fallbacks to prevent infinite retry loops caused by LLM formatting quirks.
- 🔐 **API Key Hardening**: Features secret masking for safe UI/log display, strict `.env` file permission checks, and zero environment variable leakage to the sandbox.
- 🖥️ **Real-Time Mission Control UI**: A beautiful Streamlit dashboard featuring live token streaming, deep-thinking visualization, and interactive HITL checkpoints.

* * *

---

## 🏗️ Architecture & Workflow

1. **Blueprint Ingestion & Guardrails**: The user provides a feature request. The multi-layered guardrail normalizes the input, checks regex patterns, and runs semantic analysis to block prompt injections.
2. **Meta-Prompt Synthesis**: The `Prompt_Engineer_Agent` translates the request into a hardened, adversarial system prompt.
3. **Dynamic Code Generation**: A dynamically spawned `Dynamic_Lead_Coder` writes the initial implementation.
4. **⚠️ MANDATORY HUMAN APPROVAL**: The UI pauses. The generated code is displayed, and the user must explicitly click **"Approve & Execute"** or **"Reject & Provide Hint"**.
5. **Docker Sandbox Execution**: Upon approval, the code is written to disk and executed in an isolated Docker container (`--network none`, `--read-only`, `--user 1000:1000`).
6. **Adversarial QA & Robust Parsing**: If the code crashes, the `QA_Analyst` analyzes the traceback. The response is parsed using a robust multi-stage JSON extractor.
7. **Self-Correction**: The Lead Coder receives the QA feedback and rewrites the code. This loop continues until success or the retry budget is exhausted (triggering a secondary HITL hint injection).

---

## 📂 Project Structure

```text
qwen-dev-swarm/
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized config, LLM client, API key masking, and .env permission checks
├── swarm/
│   ├── __init__.py
│   ├── agents.py            # QwenAgent base class, StreamParser, and Swarm definitions
│   └── guardrails.py        # Multi-layered prompt injection & path traversal protections
├── orchestrator.py          # Core self-correction loop, HITL checkpoints, and robust QA parsing
├── sandbox.py               # Secure Docker-based subprocess execution
├── ui.py                    # Streamlit Mission Control Dashboard with HITL UI
├── test_guardrails.py       # Comprehensive pytest suite for security guardrails
├── test_connection.py       # Quick API connectivity checker
├── Dockerfile.sandbox       # Minimal, non-root Python image for the secure sandbox
├── uv.lock                  # Cryptographically pinned dependency lockfile
├── pyproject.toml           # uv project configuration
├── .env                     # Environment variables (API keys) - MUST be chmod 600
└── README.md
```

---

## 🛠️ Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recommended package manager)
- **[Docker Engine / Docker Desktop](https://www.docker.com/)** (Required for the secure sandbox)
- An API Key for **Aliyun DashScope** (Qwen API) or compatible OpenAI endpoint.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd qwen-dev-swarm
```

### 2. Install Dependencies & Lockfile
```bash
# Sync dependencies exactly as pinned in the cryptographically hashed uv.lock
uv sync
```

### 3. Build the Secure Sandbox Image
The sandbox requires a dedicated, minimal Docker image to ensure true isolation.
```bash
docker build -f Dockerfile.sandbox -t qwen-dev-swarm-sandbox:latest .
```

### 4. Configure Environment Variables
Create a `.env` file in the project root and add your API credentials:

```env
# Required: Your Aliyun DashScope / Qwen API Key
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Override the default base URL (Defaults to standard public DashScope)
# QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Optional: Override the main swarm model
# MODEL_NAME=qwen3.7-max

# Optional: Override the semantic guardrail model (Defaults to qwen-turbo, qwen-plus recommended)
GUARDRAIL_MODEL_NAME=qwen-plus
```

### 5. Secure Your Secrets
Ensure your `.env` file is not readable by other users on your system:
```bash
chmod 600 .env
```

---

## 🎮 Usage

### Launch the Mission Control UI (Recommended)
Start the Streamlit dashboard to interact with the swarm visually:

```bash
uv run streamlit run ui.py
```
*The UI will open in your browser (usually at `http://localhost:8501`). Enter your blueprint in the sidebar and click "Launch Swarm".*

### Run via Terminal (CLI Mode)
To test the orchestrator directly in the terminal without the UI:

```bash
uv run python orchestrator.py
```

### Verify API Connection
To quickly check if your API keys and endpoints are configured correctly:

```bash
uv run python test_connection.py
```

### Run Automated Security Tests
To verify that the multi-layered guardrails and path sanitization are functioning correctly:

```bash
uv run pytest test_guardrails.py -v
```

---

## 🛡️ Security & Guardrails

Qwen-Dev-Swarm implements a defense-in-depth security model to mitigate the inherent risks of LLM-generated code:

### 1. True Docker Sandbox Isolation
Unlike basic OS-level resource limiting, the sandbox executes code inside a strictly locked-down Docker container:
- `--network none`: Completely disables internet access, preventing data exfiltration.
- `--read-only`: Makes the root filesystem read-only.
- `--user 1000:1000`: Runs as a non-root user to prevent privilege escalation.
- `--tmpfs /tmp:noexec`: Allows temporary file creation but blocks binary execution.
- Strict limits on Memory (`--memory`), CPU (`--cpus`), and Process Count (`--pids-limit`).

### 2. Multi-Layered Prompt Defense
Protects against prompt injections, jailbreaks, and semantic evasion:
- **Layer 1 (Normalization)**: Strips zero-width characters and decodes Unicode escapes to defeat obfuscation.
- **Layer 2 (Regex)**: Fast, local heuristic check for known injection patterns.
- **Layer 3 (Semantic LLM)**: Uses a dedicated, fast model (`qwen-plus`) to analyze the semantic intent of the input, catching novel attacks and authority manipulation.

### 3. Mandatory Execution Approval (Zero-Trust)
The orchestrator physically cannot execute code in the sandbox without explicit human approval via the Streamlit UI. This bypasses the risk of agent collusion or guardrail bypasses.

### 4. API Key Hardening
- **Secret Masking**: API keys are masked (e.g., `sk-12...cdef`) in all UI displays and logs.
- **Zero Leakage**: The Docker sandbox is explicitly configured to not inherit host environment variables.
- **Permission Auditing**: The app automatically warns on startup if the `.env` file has insecure read permissions.

### 5. Dependency Security
- Uses `uv.lock` to cryptographically pin all dependencies to exact versions and hashes, preventing supply-chain attacks.
- Supports automated vulnerability scanning via `pip-audit`.

### 6. Path Traversal Prevention
The `sanitize_file_path` guardrail strictly isolates file writes to the base filename, stripping directory traversal attempts (e.g., `../../etc/passwd` becomes `passwd`).

---

## 🧠 Agent Prompt Engineering

The swarm's quality is driven by its system prompts. Key mandates injected into the agents include:
- **No Flaky Tests**: The Architect and QA Analyst explicitly forbid time-based assertions (`time.time()`) to ensure CI reliability.
- **DRY & I/O Optimization**: The Lead Coder is forced to consolidate redundant loops and implement stateful dirty-tracking for I/O operations.
- **Defensive Typing**: Strict rejection of booleans masquerading as integers, and mandatory bounds checking.

---

## 🤝 Human-in-the-Loop (HITL)

The system features two distinct HITL checkpoints to ensure absolute control over the autonomous agents:

### 1. Mandatory Pre-Execution Approval
Before *any* code is executed in the Docker sandbox, the UI pauses and requires the user to explicitly review the generated script. You must click **"Approve & Execute"** to proceed, or **"Reject & Provide Hint"** to force the coder to rewrite it.

### 2. Architectural Rescue (Retry Budget Exhausted)
If the swarm fails to fix a bug after `max_retries` (default: 3), it triggers a `hitl_paused` event. The UI will display a form allowing you to inject a "Developer Hint" to guide the agents out of the loop. 

**Example Hint:**
> *"Change the division variable to check for zero, or import the math module explicitly. Also, remove the flaky time-based assertion in the test suite."*

The swarm will absorb this hint, reset its retry budget, and attempt the correction again with the new context.

---

## 📜 License

This project is provided as-is for educational and development purposes. 

---

*Built with 🧠 Qwen, 🐍 Python, 🎈 Streamlitand, and 🐳 Docker.*
```