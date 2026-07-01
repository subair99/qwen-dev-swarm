# ui.py
import os
import streamlit as st
from typing import Optional
from orchestrator import QwenDevSwarmOrchestrator

# ─────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Qwen-Dev-Swarm Mission Control")

# ─────────────────────────────────────────────────────────────
# CUSTOM STYLING
# ─────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    
    h1 {
        font-size: 2.2rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-weight: 700 !important;
        padding-bottom: 0.5rem;
    }
    
    .status-pill {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    .thinking-log {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Qwen-Dev-Swarm Mission Control Panel")

# ─────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = QwenDevSwarmOrchestrator(max_retries=2)

if "loop_status" not in st.session_state:
    st.session_state.loop_status = "IDLE"

if "thinking_text" not in st.session_state:
    st.session_state.thinking_text = ""

if "current_code_text" not in st.session_state:
    st.session_state.current_code_text = "# Awaiting deployment guidelines..."

if "final_code" not in st.session_state:
    st.session_state.final_code = None

if "error_message" not in st.session_state:
    st.session_state.error_message = None

if "retry_count" not in st.session_state:
    st.session_state.retry_count = 0

# ─────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Workspace Controls")
    
    # Use a separate session state key for the input to avoid mutation during execution
    if "blueprint_input" not in st.session_state:
        st.session_state.blueprint_input = st.session_state.orchestrator.state["current_blueprint"]
    
    blueprint_input = st.text_area(
        "System Blueprint Specification", 
        value=st.session_state.blueprint_input,
        disabled=(st.session_state.loop_status == "RUNNING"),
        help="Describe the feature you want to build. The swarm will generate a hardened implementation."
    )
    
    # Only update the orchestrator's blueprint when NOT running
    if st.session_state.loop_status != "RUNNING":
        st.session_state.orchestrator.state["current_blueprint"] = blueprint_input
        st.session_state.blueprint_input = blueprint_input
    
    # Launch button with cancellation option
    col_launch, col_cancel = st.columns(2)
    with col_launch:
        start_btn = st.button(
            "🚀 Launch Swarm", 
            disabled=(st.session_state.loop_status == "RUNNING"),
            use_container_width=True
        )
    
    with col_cancel:
        cancel_btn = st.button(
            "⏹️ Cancel",
            disabled=(st.session_state.loop_status != "RUNNING"),
            use_container_width=True
        )
    
    # Display current retry count
    if st.session_state.loop_status in ("RUNNING", "PAUSED"):
        st.info(f"📊 Current Retry: {st.session_state.retry_count + 1} / {st.session_state.orchestrator.max_retries}")

# ─────────────────────────────────────────────────────────────
# STATUS PILL RENDERER
# ─────────────────────────────────────────────────────────────
status_placeholder = st.empty()

def update_status_pill(state_key: str, custom_msg: Optional[str] = None):
    """Renders a visual status indicator."""
    status_map = {
        "IDLE": ("⚫ IDLE", "background-color: #262730; color: #a3a8b4;"),
        "RUNNING": ("⚡ RUNNING", "background-color: #1E3A8A; color: #3B82F6;"),
        "THINKING": ("🟠 LEAD CODER THINKING", "background-color: #451a03; color: #f97316;"),
        "SANDBOX": ("🧪 SANDBOX RUNNING", "background-color: #064e3b; color: #10b981;"),
        "QA": ("🔍 QA EVALUATION", "background-color: #581c87; color: #a855f7;"),
        "PAUSED": ("🔴 HITL PAUSED FOR REVIEW", "background-color: #7f1d1d; color: #ef4444;"),
        "BLOCKED": ("🛑 SECURITY BLOCKED", "background-color: #7f1d1d; color: #f87171;"),
        "COMPLETED": ("✅ COMPLETED SUCCESSFULLY", "background-color: #064e3b; color: #10b981;"),
        "ERROR": ("❌ EXECUTION ERROR", "background-color: #7f1d1d; color: #f87171;")
    }
    label, style = status_map.get(state_key, ("🟢 ACTIVE", "background-color: #10b981; color: white;"))
    display_text = f"{label} — {custom_msg}" if custom_msg else label
    status_placeholder.markdown(f'<div class="status-pill" style="{style}">{display_text}</div>', unsafe_allow_html=True)

# Render initial status
update_status_pill(st.session_state.loop_status)

# ─────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 Deep Thinking Stream")
    thinking_container = st.empty()
    thinking_container.markdown(
        f'<div class="thinking-log">{st.session_state.thinking_text or "Initializing..."}</div>',
        unsafe_allow_html=True
    )
    hitl_container = st.container()

with col2:
    st.subheader("💻 Compiled Script Workspace")
    code_container = st.empty()
    
    # Display code
    display_code = st.session_state.final_code or st.session_state.current_code_text
    code_container.code(display_code, language="python")
    
    # Download button (show if we have any code)
    if st.session_state.final_code or st.session_state.loop_status == "COMPLETED":
        try:
            with open(st.session_state.orchestrator.state["file_path"], "r") as f:
                final_code = f.read()
            st.session_state.final_code = final_code  # Cache it
            
            st.download_button(
                label="📥 Download Verified Python Script",
                data=final_code,
                file_name=st.session_state.orchestrator.state["file_path"],
                mime="text/x-python",
                use_container_width=True
            )
        except FileNotFoundError:
            pass

# ─────────────────────────────────────────────────────────────
# EXECUTION ENGINE
# ─────────────────────────────────────────────────────────────
def run_swarm_pipeline(hint_text: Optional[str] = None):
    """Executes the orchestrator loop with proper error handling and UI updates."""
    
    # Clear previous state if starting fresh
    if st.session_state.loop_status not in ("PAUSED",):
        st.session_state.thinking_text = ""
        st.session_state.current_code_text = "# Connecting to Qwen Swarm Crew..."
        st.session_state.final_code = None
        st.session_state.error_message = None
    
    st.session_state.loop_status = "RUNNING"
    
    try:
        event_stream = st.session_state.orchestrator.execute_self_correction_loop(human_hint=hint_text)
        
        for event_data in event_stream:
            current_agent = event_data.get("active_agent", "")
            current_event = event_data.get("event", "")
            
            # Update retry count
            if "retry_count" in event_data:
                st.session_state.retry_count = event_data["retry_count"]
            
            # Handle security blocks
            if current_event == "security_blocked":
                st.session_state.loop_status = "BLOCKED"
                st.session_state.error_message = event_data.get("message", "Prompt injection intercepted.")
                update_status_pill("BLOCKED", st.session_state.error_message)
                st.error(f"🛑 **Execution Halted:** {st.session_state.error_message}")
                return
            
            # Handle streaming tokens
            if "type" in event_data:
                token_text = event_data.get("text", "")
                
                if event_data["type"] == "thinking":
                    st.session_state.thinking_text += token_text
                    thinking_container.markdown(
                        f'<div class="thinking-log">{st.session_state.thinking_text}</div>',
                        unsafe_allow_html=True
                    )
                
                elif event_data["type"] == "content":
                    if st.session_state.current_code_text.startswith("#"):
                        st.session_state.current_code_text = ""
                    st.session_state.current_code_text += token_text
                    code_container.code(st.session_state.current_code_text, language="python")
                
                continue
            
            # Handle orchestrator messages
            if "message" in event_data:
                log_line = f"⚙️ [{current_agent}] {event_data['message']}\n"
                st.session_state.thinking_text += log_line
                thinking_container.markdown(
                    f'<div class="thinking-log">{st.session_state.thinking_text}</div>',
                    unsafe_allow_html=True
                )
            
            # Update status pill based on events
            if current_event == "agent_start":
                if "Coder" in current_agent:  # Matches both "Lead_Coder" and "Dynamic_Lead_Coder"
                    update_status_pill("THINKING", f"{current_agent} parsing requirements...")
                elif "QA" in current_agent:
                    update_status_pill("QA", "QA Analyst vetting trace exceptions...")
            elif current_event == "sandbox_start":
                update_status_pill("SANDBOX", "Executing generated script within isolated sandbox...")
            elif current_event == "code_compiled":
                st.session_state.current_code_text = event_data["generated_code"]
                code_container.code(st.session_state.current_code_text, language="python")
            elif current_event == "execution_success":
                st.session_state.loop_status = "COMPLETED"
                st.session_state.final_code = event_data.get("generated_code")
                update_status_pill("COMPLETED", f"Script executed successfully on Turn {event_data.get('retry_count', 0) + 1}!")
                st.balloons()
                return
            elif current_event == "hitl_paused":
                st.session_state.loop_status = "PAUSED"
                update_status_pill("PAUSED", "Swarm stalled. Human alignment feedback context requested.")
                return
        
    except Exception as e:
        st.session_state.loop_status = "ERROR"
        st.session_state.error_message = str(e)
        update_status_pill("ERROR", f"Execution failed: {str(e)[:50]}...")
        st.error(f"❌ **Execution Error:** {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")

# ─────────────────────────────────────────────────────────────
# EVENT HANDLERS
# ─────────────────────────────────────────────────────────────

# Handle launch button
if start_btn:
    # Clean up old artifacts
    target_workspace_file = st.session_state.orchestrator.state["file_path"]
    if os.path.exists(target_workspace_file):
        try:
            os.remove(target_workspace_file)
        except Exception:
            pass
    
    run_swarm_pipeline()

# Handle cancel button
if cancel_btn:
    st.session_state.loop_status = "IDLE"
    st.warning("⏹️ Execution cancelled by user.")
    st.rerun()

# ─────────────────────────────────────────────────────────────
# HITL FORM (Shown when paused)
# ─────────────────────────────────────────────────────────────
if st.session_state.loop_status == "PAUSED":
    with hitl_container:
        st.error("⚠️ **Self-Correction Budget Exhausted!** The swarm has encountered a complex barrier and requires structural guidance.")
        
        with st.form(key="hitl_feedback_form"):
            user_hint = st.text_input(
                "Inject a developer hint to rescue the architecture execution path:", 
                placeholder="e.g., Change division variable to check for zero, or import math module explicitly"
            )
            submit_hint = st.form_submit_button("🛠️ Transmit Hint & Resume Swarm", use_container_width=True)
            
            if submit_hint and user_hint:
                st.session_state.orchestrator.max_retries = 3  # Give it more budget
                st.toast("Instruction packet loaded into model context matrix!", icon="🛠️")
                run_swarm_pipeline(hint_text=user_hint)
                st.rerun()

# Show error message if present
if st.session_state.error_message and st.session_state.loop_status == "ERROR":
    st.error(f"❌ {st.session_state.error_message}")