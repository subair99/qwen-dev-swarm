import streamlit as st
from orchestrator import QwenDevSwarmOrchestrator

st.set_page_config(layout="wide", page_title="Qwen-Dev-Swarm Mission Control")

# --- Custom Styling for Hackathon Aesthetic ---
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

st.title("🚀 Qwen-DevSwarm Mission Control Panel")

# Initialize persistent session states for architecture continuity
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = QwenDevSwarmOrchestrator(max_retries=2)  # Low ceiling to easily demo HITL
if "loop_status" not in st.session_state:
    st.session_state.loop_status = "IDLE"
if "logs" not in st.session_state:
    st.session_state.logs = []

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
        "COMPLETED": ("✅ COMPLETED SUCCESSFULLY", "background-color: #064e3b; color: #10b981;")
    }
    label, style = status_map.get(state_key, ("🟢 ACTIVE", "background-color: #10b981; color: white;"))
    display_text = f"{label} — {custom_msg}" if custom_msg else label
    status_placeholder.markdown(f'<div class="status-pill" style="{style}">{display_text}</div>', unsafe_allow_html=True)

# Render initial status pill
if st.session_state.loop_status == "IDLE":
    update_status_pill("IDLE", "Awaiting blueprint deployment guidelines...")

# --- Main Layout Matrix Panels ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 Deep Thinking Stream")
    thinking_box = st.empty()
    hitl_container = st.container()  # Dedicated space for Human-in-the-Loop interactive forms

with col2:
    st.subheader("💻 Compiled Script Workspace")
    code_box = st.empty()

# --- Execution Engine Core Runner ---
def run_swarm_pipeline(hint_text=None):
    st.session_state.loop_status = "RUNNING"
    st.session_state.logs = [] 
    
    # Use session state so these don't get reset or lost mid-generator loops
    if "thinking_text" not in st.session_state:
        st.session_state.thinking_text = ""
    else:
        st.session_state.thinking_text = "" # Reset for a fresh run
        
    content_accumulator = ""
    
    # Pre-populate empty elements to avoid visual page jumping
    thinking_box.text_area("Qwen Reasoning Logs...", value="", height=400, disabled=True)
    code_box.code("# Workspace Initializing...", language="python")

    # Consume the live event generator stream step-by-step
    event_stream = st.session_state.orchestrator.execute_self_correction_loop(human_hint=hint_text)
    
    for event_data in event_stream:
        # Use .get() with an empty string fallback to stop KeyErrors cold
        current_agent = event_data.get("active_agent", "")
        current_event = event_data.get("event", "")
        
        # Handle Raw Token Packets First
        if "type" in event_data:
            token_text = event_data.get("text", "")
            
            if event_data["type"] == "thinking":
                st.session_state.thinking_text += token_text
                # Update the thinking UI box continuously using persistent state data
                thinking_box.text_area(
                    "Qwen Reasoning Logs...", 
                    value=st.session_state.thinking_text, 
                    height=400, 
                    disabled=True
                )
            elif event_data["type"] == "content":
                # FALLBACK HOOK: If text contains raw thought string patterns, mirror to the logs stream panel
                if "thinking process" in token_text.lower() or "implementing" in token_text.lower():
                    st.session_state.thinking_text += token_text
                    thinking_box.text_area(
                        "Qwen Reasoning Logs...", 
                        value=st.session_state.thinking_text, 
                        height=400, 
                        disabled=True
                    )
                else:
                    content_accumulator += token_text
                    code_box.code(content_accumulator, language="python")
            continue # Skip normal orchestration layout parsing for text chunks
        
        # 1. Dynamically route state indicators to the status pill
        if current_event == "agent_start" and current_agent == "Lead_Coder":
            update_status_pill("THINKING", "Lead Coder parsing requirements blueprint...")
        elif current_event == "agent_start" and current_agent == "QA_Analyst":
            update_status_pill("QA", "QA Analyst vetting trace exceptions...")
        elif current_event == "sandbox_start":
            update_status_pill("SANDBOX", "Executing generated script within isolated sandbox...")
                
        # Handle Sandbox complete compilation changes
        if current_event == "code_compiled":
            code_box.code(event_data["generated_code"], language="python")
            
        # Handle Successful Termination States
        if current_event == "execution_success":
            st.session_state.loop_status = "COMPLETED"
            update_status_pill("COMPLETED", f"Script executed successfully on Turn {event_data.get('retry_count', 0) + 1}!")
            st.balloons()
            
        # Handle Hit Ceiling State Handoffs
        if current_event == "hitl_paused":
            st.session_state.loop_status = "PAUSED"
            update_status_pill("PAUSED", "Swarm stalled. Human alignment feedback context requested.")
            st.rerun()  # Forces a UI refresh to display input forms immediately

# Trigger initial autonomous execution track on button click
if start_btn:
    run_swarm_pipeline()

# --- Human-in-the-Loop Form Component Layout ---
if st.session_state.loop_status == "PAUSED":
    # Ensure status pill shows paused accurately if page refreshes
    update_status_pill("PAUSED", "Swarm stalled. Human alignment feedback context requested.")
    
    with hitl_container:
        st.error("⚠️ **Self-Correction Budget Exhausted!** The swarm has encountered a complex optimization barrier and requires structural guidance.")
        
        with st.form(key="hitl_feedback_form"):
            user_hint = st.text_input(
                "Inject a developer hint to rescue the architecture execution path:", 
                placeholder="e.g., Change division variable to check for zero, or import math module explicitly"
            )
            submit_hint = st.form_submit_button("Transmit Hint & Resume Swarm Control", use_container_width=True)
            
            if submit_hint and user_hint:
                # Reset orchestrator internal loop tracking counts to re-grant token allowances
                st.session_state.orchestrator.max_retries = 3
                st.toast("Instruction packet successfully loaded into model context matrix!", icon="🛠️")
                
                # Execute the loop again, initializing with the custom human payload hint
                run_swarm_pipeline(hint_text=user_hint)