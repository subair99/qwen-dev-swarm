# qwen-dev-swarm
Hierarchical and collaborative multi-agent swarm built on Qwen LLMs. Features native code execution, stateful memory orchestration, and adaptive task routing. qwen • multi-agent-systems • agent-swarm • llm-agents • langgraph • ai-agents



Here is a comprehensive, production-ready `README.md` for your project. It captures the architecture, security features, and setup instructions based on all the code we've built and refined.

```markdown
# 🚀 Qwen-Dev-Swarm

**An Autonomous Multi-Agent Code Generation & Self-Correction Engine powered by Qwen.**

Qwen-Dev-Swarm is a production-hardened, multi-agent AI framework designed to autonomously generate, test, and debug complex Python scripts. By leveraging a specialized "swarm" of AI agents, a secure execution sandbox, and a real-time Streamlit dashboard, it transforms high-level feature requests into verified, production-ready code through iterative self-correction.

---

## ✨ Key Features

- 🤖 **Specialized Agent Swarm**: Distinct roles (Prompt Engineer, Architect, Lead Coder, QA Analyst, Code Reviewer) collaborate to ensure high-quality output.
- 🔄 **Autonomous Self-Correction Loop**: Automatically detects runtime errors, analyzes tracebacks, and iteratively refactors code until it passes the sandbox.
- 🛡️ **Hardened Security Sandbox**: Executes generated code in an isolated subprocess with strict resource limits (CPU, Memory, File Size) and sanitized environment variables to prevent data exfiltration.
- 🧠 **Dynamic Meta-Prompting**: The Prompt Engineer dynamically generates hyper-focused system prompts tailored to the specific feature request before coding begins.
- 🖥️ **Real-Time Mission Control UI**: A beautiful Streamlit dashboard featuring live token streaming, deep-thinking visualization, and status tracking.
- 🤝 **Human-in-the-Loop (HITL)**: If the swarm exhausts its retry budget, it gracefully pauses and requests architectural hints from a human engineer to resume execution.
- 🚫 **Advanced Guardrails**: Built-in regex-based prompt injection detection and strict file path sanitization to prevent directory traversal attacks.

---

## 🏗️ Architecture & Workflow

1. **Blueprint Ingestion**: The user provides a feature request via the UI.
2. **Meta-Prompt Synthesis**: The `Prompt_Engineer_Agent` translates the request into a hardened, adversarial system prompt.
3. **Dynamic Code Generation**: A dynamically spawned `Dynamic_Lead_Coder` writes the initial implementation following strict DRY and defensive programming mandates.
4. **Sandbox Execution**: The code is written to disk and executed in the `sandbox.py` secure subprocess.
5. **Adversarial QA**: If the code crashes, the `QA_Analyst` and `Code_Reviewer` analyze the traceback, identify logical flaws or flaky tests, and generate a remediation schema.
6. **Self-Correction**: The Lead Coder receives the QA feedback and rewrites the code. This loop continues until success or the retry budget is exhausted.

---

## 📂 Project Structure

```text
qwen-dev-swarm/
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration and .env loader
├── swarm/
│   ├── __init__.py
│   ├── agents.py            # QwenAgent base class, StreamParser, and Swarm definitions
│   └── guardrails.py        # Prompt injection and path traversal protections
├── orchestrator.py          # Core self-correction loop and state management
├── sandbox.py               # Secure subprocess execution with resource limits
├── ui.py                    # Streamlit Mission Control Dashboard
├── test_connection.py       # Quick API connectivity checker
├── pyproject.toml           # uv project configuration
├── .env                     # Environment variables (API keys)
└── README.md
```

---

## 🛠️ Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recommended package manager)
- An API Key for **Aliyun DashScope** (Qwen API) or compatible OpenAI endpoint.

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd qwen-dev-swarm
```

### 2. Install Dependencies using `uv`
```bash
# Create virtual environment and install core dependencies
uv venv
uv pip install openai streamlit python-dotenv
```

### 3. Configure Environment Variables
Create a `.env` file in the project root and add your API credentials:

```env
# Required: Your Aliyun DashScope / Qwen API Key
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Override the default base URL (Defaults to Aliyun MaaS)
# QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Optional: Override the default model (Defaults to qwen-max)
# MODEL_NAME=qwen3.7-max
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

---

## 🛡️ Security & Guardrails

Qwen-Dev-Swarm takes security seriously when executing LLM-generated code:

1. **Environment Sanitization**: The sandbox automatically strips sensitive variables (`QWEN_API_KEY`, `AWS_SECRET_ACCESS_KEY`, etc.) from the subprocess environment to prevent data exfiltration.
2. **Resource Limiting**: Uses POSIX `resource` limits to cap Virtual Memory (`RLIMIT_AS`), CPU Time (`RLIMIT_CPU`), File Size (`RLIMIT_FSIZE`), and Process Count (`RLIMIT_NPROC`) to prevent fork bombs and OOM crashes.
3. **Path Traversal Prevention**: The `sanitize_file_path` guardrail strictly isolates file writes to the base filename, stripping directory traversal attempts (e.g., `../../etc/passwd` becomes `passwd`).
4. **Prompt Injection Detection**: Input guardrails scan user blueprints and HITL hints for common jailbreak and injection patterns before they reach the agents.

> **⚠️ Production Warning:** While the local sandbox provides robust resource limiting, running untrusted LLM code on a host machine always carries inherent risks. For enterprise production deployments, it is highly recommended to migrate the `sandbox.py` execution backend to **Docker containers**, **WebAssembly (Wasm)**, or **E2B** for true namespace isolation.

---

## 🧠 Agent Prompt Engineering

The swarm's quality is driven by its system prompts. Key mandates injected into the agents include:
- **No Flaky Tests**: The Architect and QA Analyst explicitly forbid time-based assertions (`time.time()`) to ensure CI reliability.
- **DRY & I/O Optimization**: The Lead Coder is forced to consolidate redundant loops and implement stateful dirty-tracking for I/O operations.
- **Defensive Typing**: Strict rejection of booleans masquerading as integers, and mandatory bounds checking.

---

## 🤝 Human-in-the-Loop (HITL)

If the swarm fails to fix a bug after `max_retries` (default: 3), it triggers a `hitl_paused` event. The UI will display a form allowing you to inject a "Developer Hint". 

**Example Hint:**
> *"Change the division variable to check for zero, or import the math module explicitly. Also, remove the flaky time-based assertion in the test suite."*

The swarm will absorb this hint, reset its retry budget, and attempt the correction again with the new context.

---

## 📜 License

This project is provided as-is for educational and development purposes. 

---

*Built with 🧠 Qwen, 🐍 Python, and 🎈 Streamlit.*
```