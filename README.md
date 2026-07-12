#  Qwen-Dev-Swarm

**Zero-trust, autonomous code generation powered by an AI swarm.**

Qwen-Dev-Swarm is a production-grade, multi-agent AI framework designed to autonomously generate, test, and debug complex Python scripts. By leveraging a specialized "swarm" of AI agents, a strictly isolated Docker execution sandbox, multi-layered security guardrails, and a real-time Streamlit dashboard, it transforms high-level feature requests into verified, production-ready code through iterative self-correction and mandatory human oversight.

---

##  Video Demonstration

> *[https://youtu.be/pP3VpTm1bN4]*
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
- 🛡️ **True Docker Sandbox Isolation**: Executes generated code and tests in a strictly isolated, read-only, network-disabled Docker container with enforced memory, CPU, and PID limits.
- 🧠 **Multi-Layered Prompt Defense**: Defeats obfuscation and semantic jailbreaks using a 3-tier guardrail system (Input Normalization → Regex Heuristics → Semantic LLM Analysis).
- 🤝 **Mandatory Human-in-the-Loop (HITL) Approval**: Requires explicit human review and approval of generated code *before* it is ever executed in the sandbox, ensuring zero-trust execution.
- 🔄 **Autonomous Self-Correction Loop**: Automatically detects runtime or test errors, analyzes tracebacks, and iteratively refactors code until it passes the sandbox.
- 🧪 **Automated Test Generation & Execution**: Automatically generates and runs `pytest` suites to verify logical correctness, not just syntactic validity.
- 🕵️ **Pre-Execution Security Auditing**: Scans code for vulnerabilities and assesses risk levels before human approval.
- 📝 **Mandatory Documentation Enforcement**: Ensures every generated script starts with a comprehensive module-level docstring via prompt engineering, AST review, and post-processing regex fallbacks.
- 📊 **Robust QA Parsing**: Features a multi-stage JSON parser with regex and heuristic fallbacks to prevent infinite retry loops caused by LLM formatting quirks.
- 🔐 **API Key Hardening**: Features secret masking for safe UI/log display, strict `.env` file permission checks, and zero environment variable leakage to the sandbox.
- ️ **Real-Time Mission Control UI**: A beautiful Streamlit dashboard featuring live token streaming, deep-thinking visualization, and interactive HITL checkpoints.

---

## ️ Architecture & Workflow

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

qwen-dev-swarm/
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
└── uv.lock                      # Cryptographically locked dependencies for `uv`

---









