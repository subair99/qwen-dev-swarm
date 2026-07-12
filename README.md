#  Qwen-Dev-Swarm

**Zero-trust, autonomous code generation powered by an AI swarm.**

Qwen-Dev-Swarm is a production-grade, multi-agent AI framework designed to autonomously generate, test, and debug complex Python scripts. By leveraging a specialized "swarm" of AI agents, a strictly isolated Docker execution sandbox, multi-layered security guardrails, and a real-time Streamlit dashboard, it transforms high-level feature requests into verified, production-ready code through iterative self-correction and mandatory human oversight.

---

##  Video Demonstration

> *https://youtu.be/pP3VpTm1bN4*
> 
> Watch the Qwen-Dev-Swarm Mission Control Panel in action: from prompt to verified, secure code in minutes.

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
- 🐳 **True Docker Sandbox Isolation**: Executes generated code and tests in a strictly isolated, read-only, network-disabled Docker container with enforced memory, CPU, and PID limits.
- 🧠 **Multi-Layered Prompt Defense**: Defeats obfuscation and semantic jailbreaks using a 3-tier guardrail system (Input Normalization → Regex Heuristics → Semantic LLM Analysis).
- 🤝 **Mandatory Human-in-the-Loop (HITL) Approval**: Requires explicit human review and approval of generated code *before* it is ever executed in the sandbox, ensuring zero-trust execution.
- 🔄 **Autonomous Self-Correction Loop**: Automatically detects runtime or test errors, analyzes tracebacks, and iteratively refactors code until it passes the sandbox.
- 🧪 **Automated Test Generation & Execution**: Automatically generates and runs `pytest` suites to verify logical correctness, not just syntactic validity.
- 🕵️ **Pre-Execution Security Auditing**: Scans code for vulnerabilities and assesses risk levels before human approval.
- 📝 **Mandatory Documentation Enforcement**: Ensures every generated script starts with a comprehensive module-level docstring via prompt engineering, AST review, and post-processing regex fallbacks.
- 📊 **Robust QA Parsing**: Features a multi-stage JSON parser with regex and heuristic fallbacks to prevent infinite retry loops caused by LLM formatting quirks.
- 🔐 **API Key Hardening**: Features secret masking for safe UI/log display, strict `.env` file permission checks, and zero environment variable leakage to the sandbox.
- ️🖥️ **Real-Time Mission Control UI**: A beautiful Streamlit dashboard featuring live token streaming, deep-thinking visualization, and interactive HITL checkpoints.

---

## ️🏗️ Architecture & Workflow

1. **Blueprint Ingestion & Guardrails**: The user provides a feature request. The multi-layered guardrail normalizes the input, checks regex patterns, and runs semantic analysis to block prompt injections.
2. **Meta-Prompt Synthesis**: The `Prompt_Engineer_Agent` translates the request into a hardened, adversarial system prompt.
3. **Architectural Decomposition**: The `Software_Architect` breaks the request into modular, DRY technical specifications and testing requirements.
4. **Dynamic Code Generation**: A dynamically spawned `Dynamic_Lead_Coder` writes the initial implementation based on the architectural blueprint.
5. **Security Audit**: The `Security_Auditor_Agent` scans the generated code for vulnerabilities and outputs a risk assessment.
6. **Test Generation**: The `Test_Generator_Agent` creates comprehensive, deterministic `pytest` unit tests for the implementation.
7. **️ MANDATORY HUMAN APPROVAL**: The UI pauses. The generated code, tests, and security report are displayed. The user must explicitly click **"Approve & Execute"** or **"Reject & Provide Hint"**.
8. **Docker Sandbox Execution**: Upon approval, the main script is written to disk and executed in an isolated Docker container (`--network none`, `--read-only`, `--user 1000:1000`).
9. **Test Execution**: If the main script passes, the generated `pytest` suite is executed in the sandbox to verify correctness.
10. **Adversarial QA & Self-Correction**: If the code or tests fail, the `QA_Analyst` and `Code_Reviewer` analyze the tracebacks. The Lead Coder receives the feedback and rewrites the code. This loop continues until success or the retry budget is exhausted.
11. **Documentation Generation**: Once all tests pass, the `Documentation_Agent` generates comprehensive docstrings, type hints, and a README for the final code.

---

## 📁 Project Structure

```text
qwen-dev-swarm/
│
├── .streamlit/                  # Streamlit UI configuration
│   └── config.toml              # Streamlit theme, server, and UI settings
├── config/                      # Modular configuration settings
│   ├── __init__.py              # Initializes the config module and exports centralized settings
│   └── settings.py              # Centralized settings and environment variable loading
├── scripts/                     # Utility scripts
│   └── check_deps.sh            # Shell script to verify system and Python dependencies
├── swarm/                       # Where agents and guardrails are located
│   ├── agents.py                # Core definitions for the specialized AI agents
│   └── guardrails.py            # Multi-layered prompt defense & path sanitization
├── tests/                       # Comprehensive pytest suite for the swarm itself
│   ├── test_agent_outputs.py    # Tests agent initialization, prompts, and StreamParser
│   ├── test_connection.py       # Suite to verify API connectivity, streaming, and JSON modes
│   ├── test_generated_script.py # Structural and security gatekeeper tests for AI-generated code
│   ├── test_guardrails.py       # Tests the multi-layered prompt defense and path sanitization
│   ├── test_json_parser.py      # Tests the robust QA JSON parser and heuristic fallbacks
│   ├── test_orchestrator.py     # Tests the state machine, HITL, and retry logic
│   ├── test_sandbox.py          # Tests Docker isolation, network, and filesystem limits
│   └── test_ui.py               # Tests Streamlit rendering and secret masking
├── .gitignore                   # Rules for virtual environments, temp files, and secrets
├── .python-version              # Python version pin (3.12+)
├── Dockerfile.sandbox           # Docker config for the secure, isolated execution environment
├── LICENSE                      # Project license information
├── README.md                    # Project documentation, features, and deployment guides
├── config.py                    # Configuration file handling environment variable loading
├── generated_script.py          # Temporary scratchpad file holding the latest AI-generated code
├── inspiration.md               # Reflection detailing inspiration, learnings, and challenges
├── orchestrator.py              # Main engine managing the agent workflow and self-correction loop
├── pyproject.toml               # Python project metadata, build system config, and pytest settings
├── requirements.txt             # Fallback dependencies list for standard pip installations
├── sandbox.py                   # Manages the Docker container lifecycle and resource limits
├── ui.py                        # The Streamlit frontend (Mission Control Dashboard)
└── uv.lock                      # Cryptographically locked dependencies for uv
```

---

## 📋 Prerequisites

- **Python 3.12+**
- **uv** (Recommended package manager)
- **Docker Engine / Docker Desktop** (Required for the secure sandbox)
- An **API Key** for Aliyun DashScope (Qwen API) or a compatible OpenAI endpoint.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/subair99/qwen-dev-swarm.git
cd qwen-dev-swarm
```

### 2. Install Dependencies

```bash
# Sync dependencies exactly as pinned in the cryptographically hashed uv.lock
uv sync
```

### 3. Automated Sandbox Provisioning

**No manual Docker builds required!** The system features an **Always-Fresh Docker Image Builder** that runs automatically in the background whenever the application starts. It removes outdated images, rebuilds a fresh minimal image from `Dockerfile.sandbox` (including `pytest`), and ensures the environment is perfectly synchronized.

### 4. Configure Environment Variables

Create a `.env` file in the project root. **Note: All variables below are strictly required.**

```env
# Required: Your Aliyun DashScope / Qwen API Key
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Required: The base URL for your Qwen API endpoint
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Required: The main model used by the swarm agents
MODEL_NAME=qwen3.7-max

# Required: The model used for semantic guardrail analysis (qwen-plus recommended)
GUARDRAIL_MODEL_NAME=qwen-plus
```

### 5. Secure Your Secrets

```bash
chmod 600 .env
```

---

## 🎮 Usage

### 1. Launch the Mission Control UI (Recommended)

Start the Streamlit dashboard to interact with the swarm visually:

```bash
uv run streamlit run ui.py
```

### 2. Run the Comprehensive Test Suite

To verify that the guardrails, orchestrator state machine, JSON parsers, and sandbox isolation are functioning correctly:

```bash
uv run pytest tests/ -v
```

### 3. Run via Terminal (CLI Mode)

To test the orchestrator directly in the terminal without the UI:

```bash
uv run python orchestrator.py
```

---

## ☁️ Deploying on Alibaba Cloud (ECS)

### To run Qwen-Dev-Swarm in the cloud, use an Alibaba Cloud Elastic Compute Service (ECS) instance.

1. **Provision an ECS Instance**: Choose Ubuntu 22.04/24.04, at least 2 vCPUs and 4GB RAM.

2. **Security Group**: Allow inbound traffic on Port 22 (SSH) and Port 8501 (Streamlit UI).

3. **Install Prerequisites**:

bash

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env
```

4. **Clone, Configure, and Launch**:

bash

```bash
git clone <your-repo-url> && cd qwen-dev-swarm
uv sync
# Add your .env file here
uv run streamlit run ui.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false
```

5. **Optimize for VPC**: Update `QWEN_BASE_URL` in your `.env` to use the DashScope internal VPC endpoint (e.g., `https://dashscope-vpc.cn-hangzhou.aliyuncs.com/compatible-mode/v1`) to reduce latency and avoid egress costs.

---

## 🛡️ Security & Guardrails

### Qwen-Dev-Swarm implements a defense-in-depth security model:

1. **True Docker Sandbox Isolation**: `--network none` (no internet), `--read-only` (immutable filesystem), `--user 1000:1000` (non-root), and strict cgroup limits for Memory, CPU, and PIDs.

2. **Multi-Layered Prompt Defense**: Normalization (strips zero-width chars), Regex (fast heuristic checks), and Semantic LLM (intent analysis).

3. **Mandatory Execution Approval (Zero-Trust)**: The orchestrator physically cannot execute code in the sandbox without explicit human approval via the UI.

4. **API Key Hardening**: Secret masking in UI/logs, zero environment variable leakage to the sandbox, and strict `.env` permission auditing.

5. **Path Traversal Prevention**: The `sanitize_file_path` guardrail strictly isolates file writes to the base filename.

---

## 🌟 Inspiration

### Genesis

The genesis of **Qwen-Dev-Swarm** stemmed from a recurring frustration in modern AI-assisted development: LLMs excel at generating syntactically correct code, but consistently fail at producing production-ready artifacts. Snippets often lack defensive typing, skip edge-case handling, ignore security best practices, and omit deterministic tests.

I wanted to bridge the gap between "AI code snippet" and "verifiable, deployable software" by treating code generation not as a single-shot prompt, but as a formalized engineering pipeline. Inspired by CI/CD guardrails, multi-agent orchestration research, and zero-trust execution models, I set out to build a system that doesn't just write code, but architects, audits, tests, secures, and self-corrects until it meets strict production standards.

### What I Learned

Building this project was a deep dive into the intersection of LLM orchestration, systems security, and stateful workflow design:

- **Multi-Agent Orchestration vs. Monolithic Prompts**: Splitting responsibilities across specialized agents (Architect, Coder, Reviewer, Security_Auditor, QA_Analyst) drastically improved output quality. The separation of concerns reduced context pollution and enabled targeted feedback loops.

- **True Sandbox Isolation**: I learned that `docker run` alone is insufficient for security. True isolation requires a combination of flags: `--network none`, `--read-only`, `--user 1000:1000`, `--pids-limit`, and `cgroup`-enforced memory/CPU caps. The attack surface **A** approaches zero when:

  **(net = ∅) AND (fs = ro) AND (uid = 0)**

- **Streaming LLM Responses & Buffer Management**: Parsing `<thinking>` tags and code blocks in real-time requires a non-blocking state machine. A naive buffer causes deadlocks when LLMs output `<` in code. I implemented a safe-length buffer where:

  **B_safe = max(|tag|) - 1**

  ensuring zero character latency while preserving tag boundaries.

- **Robust JSON Extraction**: LLMs rarely output perfect JSON. I learned to build a multi-stage parser with regex fallback, bracket extraction, and heuristic scoring rather than relying on `json.loads()` alone.

- **Human-in-the-Loop (HITL) State Persistence**: Pausing an async generator mid-stream without losing context required careful state serialization. The orchestrator now maintains a persistent state dictionary that survives UI pauses and retry resumptions.

### How I Built It

The project was constructed iteratively across seven architectural phases:

#### 1. Core Agent Engine (`swarm/agents.py`)
Built a `QwenAgent` class with streaming inference, tool-calling support, and a non-blocking `StreamParser`. Implemented deterministic agent factories to instantiate specialized roles with hardened system prompts.

#### 2. Secure Execution Sandbox (`sandbox.py` + `Dockerfile.sandbox`)
Designed a minimal Alpine/Debian-based container with `pytest` pre-installed. Configured strict runtime flags to enforce read-only filesystems, network isolation, and resource caps. All code execution routes through this sandbox before touching the host.

#### 3. Multi-Layer Prompt Defense (`swarm/guardrails.py`)
Implemented a 3-tier guardrail system:
- **Layer 1**: Unicode normalization & zero-width character stripping
- **Layer 2**: Regex heuristic matching against known injection patterns
- **Layer 3**: Semantic LLM scoring using a fast auxiliary model

The composite guardrail function is defined as:

**G(x) = True ⟺ [L₁(x) = PASS] AND [L₂(x) = PASS] AND [L₃(x) = PASS]**

#### 4. Orchestrator & Self-Correction Loop (`orchestrator.py`)
Engineered the state machine that manages generation, sandbox execution, QA analysis, and retries. Implemented bounded retry logic where:

**n ≤ N_max**

with decaying hint injection to prevent oscillation. Added mandatory HITL checkpoints before any sandbox execution.

#### 5. Swarm Expansion
Added `Software_Architect`, `Code_Reviewer`, `Test_Generator_Agent`, `Security_Auditor_Agent`, and `Documentation_Agent`. Each agent enforces domain-specific constraints (e.g., deterministic tests, O-notation complexity checks, vulnerability scanning).

#### 6. Mission Control UI (`ui.py`)
Built a Streamlit dashboard with real-time token streaming, deep-thinking visualization, interactive approval buttons, and state-aware resumption. API keys are masked using:

**k_display = k[4] + ... + k[-4:]**

to prevent leakage.

#### 7. Hardening & Polish
Integrated `uv` for cryptographic dependency locking, enforced `.env` permission checks (`chmod 600`), added mandatory module docstring validation via regex, and implemented path traversal sanitization:

**sanitize_path(p) → basename(p)**

### Challenges Faced & Solutions

| Challenge | Root Cause | Solution |
|-----------|------------|----------|
| **Infinite Retry Loops** | QA feedback sometimes caused the Coder to oscillate between two flawed implementations. | Implemented bounded retries **n ≤ N_max** with a convergence threshold. If **Δ_error < ε** for 3 iterations, the loop forces a structural rewrite. |
| **Sandbox Resource Leaks** | Early Docker runs allowed unlimited PIDs and memory, enabling fork bombs. | Enforced group limits: `--memory=512m --cpus=1.0 --pids-limit=50`. Added `--tmpfs /tmp:noexec` to block binary drops. |
| **Streaming Parser Deadlocks** | LLMs output `<` in comparisons (e.g., `if a < b:`), causing the `<thinking>` buffer to hang. | Built a non-blocking state machine with safe-length buffering: only retain **B_safe** characters. |
| **Flaky AI-Generated Tests** | Tests used `time.time()` or `assertLess(elapsed, threshold)`, causing CI failures. | Added explicit guardrails in `Software_Architect` and `Code_Reviewer` prompts forbidding time-based assertions. Enforced value-correctness tests: **assert_f(x) = y_known**. |
| **Prompt Injection Evasion** | Attackers used Unicode escapes, zero-width chars, and semantic role-play to bypass regex. | Implemented 3-tier defense. Semantic layer uses a fast model to compute intent confidence: <br> **P(malicious | x) > θ → BLOCK**. |
| **HITL State Loss on Pause** | Stopping the generator mid-stream dropped context, forcing full regeneration. | Serialized orchestrator state into `self.state` dict. UI yields `await_human_approval` events and resumes via `approved_code` injection without resetting retry counters. |

### Final Reflection

Building **Qwen-Dev-Swarm** transformed my understanding of what it takes to move from "AI-assisted scripting" to **autonomous, verifiable software engineering**. The project proved that with strict guardrails, true isolation, and iterative self-correction, LLMs can be elevated from creative typists to reliable engineering partners.


---


## 🤖 AI Tools Leveraged

- **Qwen (Tongyi Qianwen)**: The core LLM driving the multi-agent swarm (`qwen3.7-max` and `qwen-plus`).
- **Alibaba Cloud DashScope**: The cloud API infrastructure hosting the Qwen model inference.
- **OpenAI Python SDK**: The standardized client wrapper for seamless streaming and tool-calling.
- **Qwen Studio / Qwen Chat**: Used for architectural brainstorming and debugging async generators.
- **Google Gemini**: Used for cross-referencing Python documentation and troubleshooting edge cases.

---


## 🛠️ Installation & Setup

```bash

```


---







