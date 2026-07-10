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
    # 🛡️ CRITICAL: Enable mandatory approval by default
    st.session_state.orchestrator = QwenDevSwarmOrchestrator(max_retries=2, require_approval=True)

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

# 🛡️ NEW: State for HITL Approval Checkpoint
if "pending_approval_code" not in st.session_state:
    st.session_state.pending_approval_code = None

# ─────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Workspace Controls")
    
    if "blueprint_input" not in st.session_state:
        st.session_state.blueprint_input = st.session_state.orchestrator.state["current_blueprint"]
    
    # Disable inputs if waiting for approval, running, or rejecting
    is_disabled = st.session_state.loop_status in ("RUNNING", "AWAITING_APPROVAL", "REJECTING")
    
    blueprint_input = st.text_area(
        "System Blueprint Specification", 
        value=st.session_state.blueprint_input,
        disabled=is_disabled,
        help="Describe the feature you want to build. The swarm will generate a hardened implementation."
    )
    
    if not is_disabled:
        st.session_state.orchestrator.state["current_blueprint"] = blueprint_input
        st.session_state.blueprint_input = blueprint_input
    
    col_launch, col_cancel = st.columns(2)
    with col_launch:
        start_btn = st.button(
            "🚀 Launch Swarm", 
            disabled=is_disabled,
            use_container_width=True
        )
    
    with col_cancel:
        cancel_btn = st.button(
            "⏹️ Cancel",
            disabled=(st.session_state.loop_status not in ("RUNNING", "AWAITING_APPROVAL", "REJECTING", "PAUSED")),
            use_container_width=True
        )
    
    if st.session_state.loop_status in ("RUNNING", "PAUSED", "AWAITING_APPROVAL", "REJECTING"):
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
        "AWAITING_APPROVAL": ("⚠️ AWAITING HUMAN APPROVAL", "background-color: #78350f; color: #fbbf24;"),
        "REJECTING": ("📝 PROVIDING REJECTION HINT", "background-color: #78350f; color: #fbbf24;"),
        "PAUSED": ("🔴 HITL PAUSED FOR REVIEW", "background-color: #7f1d1d; color: #ef4444;"),
        "BLOCKED": ("🛑 SECURITY BLOCKED", "background-color: #7f1d1d; color: #f87171;"),
        "COMPLETED": ("✅ COMPLETED SUCCESSFULLY", "background-color: #064e3b; color: #10b981;"),
        "ERROR": ("❌ EXECUTION ERROR", "background-color: #7f1d1d; color: #f87171;")
    }
    label, style = status_map.get(state_key, ("🟢 ACTIVE", "background-color: #10b981; color: white;"))
    display_text = f"{label} — {custom_msg}" if custom_msg else label
    status_placeholder.markdown(f'<div class="status-pill" style="{style}">{display_text}</div>', unsafe_allow_html=True)

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
    
    display_code = st.session_state.final_code or st.session_state.current_code_text
    code_container.code(display_code, language="python")
    
    if st.session_state.final_code or st.session_state.loop_status == "COMPLETED":
        try:
            with open(st.session_state.orchestrator.state["file_path"], "r") as f:
                final_code = f.read()
            st.session_state.final_code = final_code  
            
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
def run_swarm_pipeline(hint_text: Optional[str] = None, approved_code: Optional[str] = None):
    """Executes the orchestrator loop with proper error handling and UI updates."""
    
    # Clear previous state if starting fresh
    if st.session_state.loop_status not in ("PAUSED", "AWAITING_APPROVAL", "REJECTING"):
        st.session_state.thinking_text = ""
        st.session_state.current_code_text = "# Connecting to Qwen Swarm Crew..."
        st.session_state.final_code = None
        st.session_state.error_message = None
    
    st.session_state.loop_status = "RUNNING"
    
    try:
        # 🛡️ Pass approved_code to the orchestrator to bypass generation if approved
        event_stream = st.session_state.orchestrator.execute_self_correction_loop(
            human_hint=hint_text, 
            approved_code=approved_code
        )
        
        for event_data in event_stream:
            current_agent = event_data.get("active_agent", "")
            current_event = event_data.get("event", "")
            
            if "retry_count" in event_data:
                st.session_state.retry_count = event_data["retry_count"]
            
            if current_event == "security_blocked":
                st.session_state.loop_status = "BLOCKED"
                st.session_state.error_message = event_data.get("message", "Prompt injection intercepted.")
                update_status_pill("BLOCKED", st.session_state.error_message)
                st.error(f"🛑 **Execution Halted:** {st.session_state.error_message}")
                return
            
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
            
            if "message" in event_data:
                log_line = f"⚙️ [{current_agent}] {event_data['message']}\n"
                st.session_state.thinking_text += log_line
                thinking_container.markdown(
                    f'<div class="thinking-log">{st.session_state.thinking_text}</div>',
                    unsafe_allow_html=True
                )
            
            if current_event == "agent_start":
                if "Coder" in current_agent:
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
            
            # 🛡️ CRITICAL SECURITY CHECKPOINT: Pause for Human Approval
            elif current_event == "await_human_approval":
                generated = event_data.get("generated_code")
                if generated:
                    st.session_state.current_code_text = generated
                    st.session_state.pending_approval_code = generated
                st.session_state.loop_status = "AWAITING_APPROVAL"
                update_status_pill("AWAITING_APPROVAL", "Mandatory human review required before execution.")
                return
                
            elif current_event == "hitl_paused":
                st.session_state.loop_status = "PAUSED"
                update_status_pill("PAUSED", "Swarm stalled. Human alignment feedback context requested.")
                return
        
    except Exception as e:
        error_str = str(e)
        # 🛡️ Catch the websocket disconnect error gracefully
        if "websocket.close" in error_str or "Unexpected ASGI" in error_str:
            st.session_state.loop_status = "ERROR"
            st.session_state.error_message = "Connection Lost"
            update_status_pill("ERROR", "UI Disconnected")
            st.warning("⚠️ **Connection Lost:** The UI disconnected, but the Swarm may still be running in the background. Please refresh the page.")
        else:
            # Handle all other exceptions with detailed tracebacks
            st.session_state.loop_status = "ERROR"
            st.session_state.error_message = error_str
            update_status_pill("ERROR", f"Execution failed: {error_str[:50]}...")
            st.error(f"❌ **Execution Error:** {error_str}")
            import traceback
            st.code(traceback.format_exc(), language="python")

# ─────────────────────────────────────────────────────────────
# EVENT HANDLERS
# ─────────────────────────────────────────────────────────────

if start_btn:
    target_workspace_file = st.session_state.orchestrator.state["file_path"]
    if os.path.exists(target_workspace_file):
        try:
            os.remove(target_workspace_file)
        except Exception:
            pass
    
    run_swarm_pipeline()

if cancel_btn:
    st.session_state.loop_status = "IDLE"
    st.session_state.pending_approval_code = None
    st.warning("⏹️ Execution cancelled by user.")
    st.rerun()

# ─────────────────────────────────────────────────────────────
# 🛡️ HITL APPROVAL INTERFACE (Mandatory Security Review)
# ─────────────────────────────────────────────────────────────
if st.session_state.loop_status == "AWAITING_APPROVAL":
    with hitl_container:
        st.warning("⚠️ **MANDATORY SECURITY REVIEW:** The AI has generated code. You must explicitly approve it before it is executed in the sandbox.")
        
        col_approve, col_reject = st.columns(2)
        with col_approve:
            if st.button("✅ Approve & Execute", use_container_width=True, type="primary"):
                approved_code = st.session_state.pending_approval_code
                st.session_state.pending_approval_code = None
                run_swarm_pipeline(approved_code=approved_code)
                st.rerun()
                
        with col_reject:
            if st.button("❌ Reject & Provide Hint", use_container_width=True):
                st.session_state.loop_status = "REJECTING"
                st.rerun()

if st.session_state.loop_status == "REJECTING":
    with hitl_container:
        st.info("📝 Please provide a hint to guide the AI to fix the code.")
        with st.form(key="reject_hint_form"):
            user_hint = st.text_area("Developer Hint:", placeholder="e.g., The logic for X is incorrect, please use Y instead.")
            submit_hint = st.form_submit_button("🛠️ Transmit Hint & Regenerate", use_container_width=True)
            if submit_hint:
                hint_text = user_hint
                st.session_state.pending_approval_code = None
                run_swarm_pipeline(hint_text=hint_text)
                st.rerun()

# ─────────────────────────────────────────────────────────────
# HITL FORM (Shown when max retries exhausted)
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
                st.session_state.orchestrator.max_retries = 3
                st.toast("Instruction packet loaded into model context matrix!", icon="🛠️")
                run_swarm_pipeline(hint_text=user_hint)
                st.rerun()

if st.session_state.error_message and st.session_state.loop_status == "ERROR":
    st.error(f"❌ {st.session_state.error_message}")