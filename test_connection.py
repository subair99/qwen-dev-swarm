# test_connection.py

# run with: uv run python test_connection.py

import sys
import json
from config.settings import settings, get_llm_client
from swarm.agents import create_swarm_agents

def run_swarm_diagnostics():
    print("🔍 Running Full Swarm Diagnostic...\n")
    
    # 1. Verify Environment & Client
    try:
        client = get_llm_client()
        print(f"✅ OpenAI Client initialized for model: {settings.MODEL_NAME}")
        print(f"🌐 Endpoint: {settings.QWEN_BASE_URL}")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize client. Check your .env file.\nError: {e}")
        sys.exit(1)

    swarm = create_swarm_agents()
    
    # 2. Test Blocking Call (Standard Inference)
    print("\n🤖 [1/3] Testing Blocking Call (Software_Architect)...")
    try:
        # The Architect uses standard blocking calls
        res = swarm["architect"].call_llm("Reply with exactly the phrase: BLOCKING_OK")
        assert "BLOCKING_OK" in res, "Unexpected response format"
        print("✅ Blocking inference successful.")
    except Exception as e:
        print(f"❌ Blocking call failed: {e}")
        sys.exit(1)

    # 3. Test Streaming Call (Real-time Token Generation)
    print("\n🌊 [2/3] Testing Streaming Call (Lead_Coder)...")
    try:
        # The Lead Coder, QA, and Test Generator use streaming for the UI
        stream_text = ""
        for chunk in swarm["coder"].call_llm_stream("Reply with exactly the phrase: STREAMING_OK"):
            if chunk.get("type") == "content":
                stream_text += chunk.get("text", "")
        
        assert "STREAMING_OK" in stream_text, "Unexpected streaming response"
        print("✅ Streaming inference successful.")
    except Exception as e:
        print(f"❌ Streaming call failed (UI will not work if this fails): {e}")
        sys.exit(1)

    # 4. Test Strict JSON Mode (Structured Output)
    print("\n📦 [3/3] Testing Strict JSON Mode (QA_Analyst)...")
    try:
        # The Security Auditor, QA, and Documentation agents require strict JSON
        res = swarm["qa_analyst"].call_llm(
            "Return a valid JSON object with a single key 'status' set to the string 'PASS'.", 
            require_json=True
        )
        data = json.loads(res)
        assert data.get("status") == "PASS", "JSON content mismatch"
        print("✅ Strict JSON enforcement successful.")
    except json.JSONDecodeError:
        print("❌ JSON mode failed: Model returned invalid JSON. Orchestrator parsers will break.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ JSON mode test failed: {e}")
        sys.exit(1)
        
    print("\n" + "="*40)
    print("🎉 ALL DIAGNOSTICS PASSED!")
    print("Your API keys, network, streaming, and JSON modes are fully operational.")
    print("You can safely run: uv run streamlit run ui.py")
    print("="*40)

if __name__ == "__main__":
    run_swarm_diagnostics()