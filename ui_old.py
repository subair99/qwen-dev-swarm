# ui.py
import os
import streamlit as st
from orchestrator import QwenDevSwarmOrchestrator

st.set_page_config(layout="wide", page_title="Qwen-Dev-Swarm Mission Control")

# --- Custom Styling for Aesthetic ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    
    /* Hardened single-line constraint rule for the main dashboard title */
    h1 {
        font-size: 2.2rem !important;  /* scaled down slightly from default to fit text width */
        white-space: nowrap !important; /* enforces zero text-wrapping down to a second row */
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
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Qwen-Dev-Swarm Mission Control Panel")

# Initialize persistent session states for architecture continuity
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = QwenDevSwarmOrchestrator(max_retries=2)  # Low ceiling to easily demo HITL
if "loop_status" not in st.session_state:
    st.session_state.loop_status = "IDLE"
if "logs" not in st.session_state:
    st.session_state.logs = []
if "thinking_text" not in st.session_state:
    st.session_state.thinking_text = ""
if "current_code_text" not in st.session_state:
    st.session_state.current_code_text = "# Awaiting deployment guidelines..."

# --- UI Sidebar Controls ---
with st.sidebar:
    st.header("Workspace Controls")
    blueprint_input = st.text_area(
        "System Blueprint Specification", 
        value=st.session_state.orchestrator.state["current_blueprint"]
    )
    st.session_state.orchestrator.state["current_blueprint"] = blueprint_input
    
    start_btn = st.button(
        "Launch Autonomous Swarm Sequence", 
        disabled=(st.session_state.loop_status == "RUNNING"),
        use_container_width=True
    )

# --- Dynamic Visual Status Pill Block ---
status_placeholder = st.empty()

def update_status_pill(state_key, custom_msg=None):
    """Renders a striking visual status indicator right above the workspace matrix."""
    status_map = {
        "IDLE": ("⚫ IDLE", "background-color: #262730; color: #a3a8b4;"),
        "RUNNING": ("⚡ RUNNING", "background-color: #1E3A8A; color: #3B82F6;"),
        "THINKING": ("🟠 LEAD CODER THINKING", "background-color: #451a03; color: #f97316;"),
        "SANDBOX": ("🧪 SANDBOX RUNNING", "background-color: #064e3b; color: #10b981;"),
        "QA": ("🔍 QA EVALUATION", "background-color: #581c87; color: #a855f7;"),
        "PAUSED": ("🔴 HITL PAUSED FOR REVIEW", "background-color: #7f1d1d; color: #ef4444;"),
        "BLOCKED": ("🛑 SECURITY BLOCKED", "background-color: #7f1d1d; color: #f87171;"),
        "COMPLETED": ("✅ COMPLETED SUCCESSFULLY", "background-color: #064e3b; color: #10b981;")
    }
    label, style = status_map.get(state_key, ("🟢 ACTIVE", "background-color: #10b981; color: white;"))
    display_text = f"{label} — {custom_msg}" if custom_msg else label
    status_placeholder.markdown(f'<div class="status-pill" style="{style}">{display_text}</div>', unsafe_allow_html=True)

# Render initial status pill states
if st.session_state.loop_status == "IDLE":
    update_status_pill("IDLE", "Awaiting blueprint deployment guidelines...")
elif st.session_state.loop_status == "COMPLETED":
    update_status_pill("COMPLETED", "Script verified and ready for deployment.")
elif st.session_state.loop_status == "BLOCKED":
    update_status_pill("BLOCKED", "Execution terminated due to safety violations.")

# --- Main Layout Matrix Panels ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 Deep Thinking Stream")
    thinking_container = st.empty()
    thinking_container.text_area(
        "Qwen Reasoning Logs...", 
        value=st.session_state.thinking_text, 
        height=400, 
        disabled=True
    )
    hitl_container = st.container()

with col2:
    st.subheader("💻 Compiled Script Workspace")
    code_container = st.empty()
    
    # Render final frozen code or current progress token states safely
    if st.session_state.loop_status == "COMPLETED":
        try:
            with open(st.session_state.orchestrator.state["file_path"], "r") as f:
                saved_code = f.read()
            code_container.code(saved_code, language="python")
        except FileNotFoundError:
            code_container.code("# Verified script asset missing from disk workspace", language="python")
    else:
        code_container.code(st.session_state.current_code_text, language="python")
    
    # 📥 Presentation Download Button Component Integration
    if st.session_state.loop_status == "COMPLETED":
        try:
            with open(st.session_state.orchestrator.state["file_path"], "r") as f:
                final_code = f.read()
            st.download_button(
                label="📥 Download Verified Python Script",
                data=final_code,
                file_name=st.session_state.orchestrator.state["file_path"],
                mime="text/x-python",
                use_container_width=True
            )
        except FileNotFoundError:
            pass

# --- Execution Engine Core Runner ---
def run_swarm_pipeline(hint_text=None):
    # Only wipe historical data if we are starting a fresh run from the sidebar
    if st.session_state.loop_status not in ("COMPLETED", "PAUSED", "BLOCKED"):
        st.session_state.thinking_text = ""
        st.session_state.current_code_text = ""
        
    st.session_state.loop_status = "RUNNING"
    st.session_state.logs = [] 
    
    # Prime the containers visibly right before execution loop launches
    thinking_container.text_area("Qwen Reasoning Logs...", value=st.session_state.thinking_text or "Initializing...", height=400, disabled=True)
    code_container.code(st.session_state.current_code_text or "# Connecting to Qwen Swarm Crew...", language="python")

    # Consume the live event generator stream step-by-step
    event_stream = st.session_state.orchestrator.execute_self_correction_loop(human_hint=hint_text)
    
    for event_data in event_stream:
        current_agent = event_data.get("active_agent", "")
        current_event = event_data.get("event", "")
        
        # 🟢 CRITICAL LOG FORCING: Write orchestrator phase changes directly into thinking window
        if "message" in event_data and "type" not in event_data:
            log_line = f"⚙️ [{current_agent}] {event_data['message']}\n"
            if log_line not in st.session_state.thinking_text:
                st.session_state.thinking_text += log_line
                thinking_container.text_area("Qwen Reasoning Logs...", value=st.session_state.thinking_text, height=400, disabled=True)

        # 🛡️ INTERCEPT SECURITY INJECTION ALERTS IMMEDIATELY
        if current_event == "security_blocked":
            st.session_state.loop_status = "BLOCKED"
            update_status_pill("BLOCKED", event_data.get("message", "Prompt injection intercepted."))
            st.error(f"🛑 **Execution Halted:** {event_data.get('message')}")
            return # Safe breakout termination

        # Handle Raw Token Packets
        if "type" in event_data:
            token_text = event_data.get("text", "")
            
            if event_data["type"] == "thinking":
                st.session_state.thinking_text += token_text
                thinking_container.text_area("Qwen Reasoning Logs...", value=st.session_state.thinking_text, height=400, disabled=True)
            
            elif event_data["type"] == "content":
                if "thinking process" in token_text.lower() or "implementing" in token_text.lower() or "step" in token_text.lower():
                    st.session_state.thinking_text += token_text
                    thinking_container.text_area("Qwen Reasoning Logs...", value=st.session_state.thinking_text, height=400, disabled=True)
                else:
                    if st.session_state.current_code_text == "# Awaiting deployment guidelines...":
                        st.session_state.current_code_text = ""
                    st.session_state.current_code_text += token_text
                    code_container.code(st.session_state.current_code_text, language="python")
            continue 
        
        # Dynamically route milestone state updates to the status pill placeholder
        if current_event == "agent_start" and current_agent == "Lead_Coder":
            update_status_pill("THINKING", "Lead Coder parsing requirements blueprint...")
        elif current_event == "agent_start" and current_agent == "QA_Analyst":
            update_status_pill("QA", "QA Analyst vetting trace exceptions...")
        elif current_event == "sandbox_start":
            update_status_pill("SANDBOX", "Executing generated script within isolated sandbox...")
                
        # Handle Sandbox complete compilation changes
        if current_event == "code_compiled":
            st.session_state.current_code_text = event_data["generated_code"]
            code_container.code(st.session_state.current_code_text, language="python")
            
        # Handle Successful Termination States
        if current_event == "execution_success":
            st.session_state.loop_status = "COMPLETED"
            update_status_pill("COMPLETED", f"Script executed successfully on Turn {event_data.get('retry_count', 0) + 1}!")
            st.balloons()
            st.rerun()
            
        # Handle Hit Ceiling State Handoffs
        if current_event == "hitl_paused":
            st.session_state.loop_status = "PAUSED"
            st.rerun()

# Trigger initial autonomous execution track on button click
if start_btn:
    # Workspace Clean Sweep Pass: Vaporize stale artifacts before looping
    target_workspace_file = st.session_state.orchestrator.state["file_path"]
    if os.path.exists(target_workspace_file):
        try:
            os.remove(target_workspace_file)
        except Exception:
            pass
            
    # Reset loop status flag before kicking off loop updates
    st.session_state.loop_status = "IDLE"
    run_swarm_pipeline()

# --- Human-in-the-Loop Form Component Layout ---
if st.session_state.loop_status == "PAUSED":
    update_status_pill("PAUSED", "Swarm stalled. Human alignment feedback context requested.")
    
    with hitl_container:
        st.error("⚠️ **Self-Correction Budget Exhausted!** The swarm has encountered a complex barrier and requires structural guidance.")
        
        with st.form(key="hitl_feedback_form"):
            user_hint = st.text_input(
                "Inject a developer hint to rescue the architecture execution path:", 
                placeholder="e.g., Change division variable to check for zero, or import math module explicitly"
            )
            submit_hint = st.form_submit_button("Transmit Hint & Resume Swarm Control", use_container_width=True)
            
            if submit_hint and user_hint:
                st.session_state.orchestrator.max_retries = 3
                st.toast("Instruction packet loaded into model context matrix!", icon="🛠️")
                run_swarm_pipeline(hint_text=user_hint)