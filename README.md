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
- 📦 **True Docker Sandbox Isolation**: Executes generated code and tests in a strictly isolated, read-only, network-disabled Docker container with enforced memory, CPU, and PID limits.
- 🧠 **Multi-Layered Prompt Defense**: Defeats obfuscation and semantic jailbreaks using a 3-tier guardrail system (Input Normalization → Regex Heuristics → Semantic LLM Analysis).
- 🤝 **Mandatory Human-in-the-Loop (HITL) Approval**: Requires explicit human review and approval of generated code _before_ it is ever executed in the sandbox, ensuring zero-trust execution.
- 🧪 **Automated Test Generation & Execution**: Automatically generates and runs `pytest` suites to verify logical correctness, not just syntactic validity.
- 🕵️ **Pre-Execution Security Auditing**: Scans code for vulnerabilities and assesses risk levels before human approval.
- 📝 **Automated Documentation**: Generates comprehensive documentation, including docstrings and type hints, once code passes all tests.
- 🔄 **Autonomous Self-Correction Loop**: Automatically detects runtime or test errors, analyzes tracebacks, and iteratively refactors code until it passes the sandbox.
- 📊 **Robust QA Parsing**: Features a multi-stage JSON parser with heuristic fallbacks to prevent infinite retry loops caused by LLM formatting quirks.
- 🔐 **API Key Hardening**: Features secret masking for safe UI/log display, strict `.env` file permission checks, and zero environment variable leakage to the sandbox.
- 🖥️ **Real-Time Mission Control UI**: A beautiful Streamlit dashboard featuring live token streaming, deep-thinking visualization, and interactive HITL checkpoints.

---

## 🏗️ Architecture & Workflow

1. **Blueprint Ingestion & Guardrails**: The user provides a feature request. The multi-layered guardrail normalizes the input, checks regex patterns, and runs semantic analysis to block prompt injections.
2. **Meta-Prompt Synthesis**: The `Prompt_Engineer_Agent` translates the request into a hardened, adversarial system prompt.
3. **Architectural Decomposition**: The `Software_Architect` breaks the request into modular, DRY technical specifications and testing requirements.
4. **Dynamic Code Generation**: A dynamically spawned `Dynamic_Lead_Coder` writes the initial implementation based on the architectural blueprint.
5. **Security Audit**: The `Security_Auditor_Agent` scans the generated code for vulnerabilities and outputs a risk assessment.
6. **Test Generation**: The `Test_Generator_Agent` creates comprehensive, deterministic `pytest` unit tests for the implementation.
7. **⚠️ MANDATORY HUMAN APPROVAL**: The UI pauses. The generated code, tests, and security report are displayed. The user must explicitly click **"Approve & Execute"** or **"Reject & Provide Hint"**.
8. **Docker Sandbox Execution**: Upon approval, the main script is written to disk and executed in an isolated Docker container (`--network none`, `--read-only`, `--user 1000:1000`).
9. **Test Execution**: If the main script passes, the generated `pytest` suite is executed in the sandbox to verify correctness.
10. **Adversarial QA & Self-Correction**: If the code or tests fail, the `QA_Analyst` and `Code_Reviewer` analyze the tracebacks. The Lead Coder receives the feedback and rewrites the code. This loop continues until success or the retry budget is exhausted.
11. **Documentation Generation**: Once all tests pass, the `Documentation_Agent` generates comprehensive docstrings, type hints, and a README for the final code.

---

## 📂 Project Structure

```text
qwen-dev-swarm/
├── .streamlit/
│   └── config.toml                 # Streamlit UI configuration
├── config/
│   ├── __init__.py
│   └── settings.py                 # Modular configuration settings
├── scripts/
│   └── check_deps.sh               # Utility script to verify dependencies
├── swarm/
│   ├── __init__.py
│   ├── agents.py                   # Core definitions for the specialized AI agents
│   └── guardrails.py               # Multi-layered prompt defense & path sanitization
├── .gitignore
├── .python-version                 # Python version pin (3.12+)
├── Dockerfile.sandbox              # Docker config for the secure, isolated code execution environment
├── LICENSE
├── README.md                       # Project documentation
├── config.py                       # Legacy/root configuration file (env vars)
├── generated_script.py             # Temporary file for the latest generated code
├── orchestrator.py                 # The main engine that manages the agent workflow and Docker execution
├── pyproject.toml                  # Python project metadata
├── requirements.txt                # Fallback dependencies list
├── sandbox.py                      # Manages the Docker container lifecycle and resource limits
├── test_connection.py              # Utility to verify Qwen API connectivity
├── test_generated_script.py        # Temporary file for the generated pytest suite
├── test_guardrails.py              # Pytest suite to test the security guardrails
├── ui.py                           # The Streamlit frontend (Mission Control Dashboard)
└── uv.lock                         # Cryptographically locked dependencies for `uv`
```

---

## 🐛 Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recommended package manager)
- **[Docker Engine / Docker Desktop](https://www.docker.com/)** (Required for the secure sandbox)
- An API Key for **Aliyun DashScope** (Qwen API).

---

## 🔌 Installation & Setup

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

### 3. Automated Sandbox Provisioning

No manual Docker builds required! The system features an **Always-Fresh Docker Image Builder** that runs automatically in the background whenever the application starts. 

It automatically:
- Removes any outdated sandbox images.
- Rebuilds a completely fresh, minimal Docker image from `Dockerfile.sandbox` (including `pytest` for automated testing).
- Ensures the execution environment is always perfectly synchronized with the latest project dependencies.

*Just launch the app, and the sandbox will be ready for you.*

### 4. Configure Environment Variables
Create a `.env` file in the project root and add your API credentials:

```env
# Required: Your Aliyun DashScope / Qwen API Key
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Override the default base URL (Defaults to standard public DashScope)
# QWEN_BASE_URL=https://ws-zp9gpq4ly3nzvc4s.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1

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

## 📜 License

This project is provided as-is for educational and development purposes. 

---

## 🛠️ Built With

[![Qwen](https://img.shields.io/badge/Qwen-FF6600?style=for-the-badge&logo=alibabacloud&logoColor=white)](https://qwenlm.github.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## ☁️ Deploying on Alibaba Cloud (ECS)

To run Qwen-Dev-Swarm in the cloud, we recommend using an **Alibaba Cloud Elastic Compute Service (ECS)** instance. This provides the necessary Docker support and persistent environment for the Streamlit dashboard.

### Step 1: Provision an ECS Instance

1. Log in to the [Alibaba Cloud Console](https://ecs.console.aliyun.com/) and navigate to **ECS**.
2. Click **Create Instance** and configure the following:
   - **Instance Type**: Select a general-purpose instance (e.g., `ecs.g7.large` or `ecs.c7.large`) with at least **2 vCPUs and 4GB RAM** (8GB+ recommended for Docker + LLM processing).
   - **OS Image**: Choose **Ubuntu 22.04 64-bit** or **Ubuntu 24.04 64-bit**.
   - **Storage**: At least 40GB ESSD.
3. **Security Group (Crucial)**: Ensure your Security Group allows inbound traffic on:
   - `Port 22` (SSH)
   - `Port 8501` (Streamlit UI) - *Set source to `0.0.0.0/0` or your specific IP.*

### Step 2: Connect and Install Prerequisites

SSH into your new instance:
```bash
ssh root@<YOUR_ECS_PUBLIC_IP>
```

Update system and install Docker:
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker && systemctl start docker
```

Install uv (handles Python 3.12 automatically):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### Step 3: Clone and Configure the Project

Clone the repository:
```bash
git clone <your-repo-url>
cd qwen-dev-swarm
```

Install project dependencies:
```bash
uv sync
```

Create and configure your environment variables:
```bash
nano .env
```
Paste your `QWEN_API_KEY` and other required variables into the `.env` file, then save and exit.

### Step 4: Launch the Application

Because the app is running on a remote server, you must bind Streamlit to `0.0.0.0` so it accepts external connections:
```bash
uv run streamlit run ui.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false
```

### Step 5: Access the Mission Control UI

Open your web browser and navigate to:
```bash
http://<YOUR_ECS_PUBLIC_IP>:8501
```

---