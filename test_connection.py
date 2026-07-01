# test_connection.py
from config.settings import settings
from swarm.agents import create_swarm_agents

def test_agent_connection(agent, prompt: str, use_streaming: bool = False) -> str:
    """
    Tests the connection by invoking the agent's native LLM call method.
    Supports both blocking and streaming modes to verify the full pipeline.
    """
    print(f"🤖 [{agent.name}] processing request...")
    
    try:
        if use_streaming:
            print("--- Streaming Output ---")
            full_response = ""
            for chunk in agent.call_llm_stream(prompt):
                text = chunk.get("text", "")
                print(text, end="", flush=True)
                full_response += text
            print("\n--- End of Stream ---")
            return full_response
        else:
            # Utilizes the agent's internal client, settings, and temperature (0.2)
            return agent.call_llm(prompt)
            
    except Exception as e:
        print(f"❌ API Call Failed for {agent.name}: {e}")
        return None

def main():
    # 1. Debug line: verify if the key is actually being loaded
    # Note: settings.validate() already runs on import, so if it fails, 
    # the script would have crashed before reaching this line.
    print(f"DEBUG: Found API Key with length {len(settings.QWEN_API_KEY)} characters.")
    print(f"DEBUG: Target URL is {settings.QWEN_BASE_URL}")
    print(f"DEBUG: Target Model is {settings.MODEL_NAME}\n")

    # 2. Spin up the swarm crew
    crew = create_swarm_agents()
    
    # 3. Quick dry-run using the Architect Agent
    user_request = "Design a basic FastAPI logging middleware. Output only the architectural blueprint."
    
    # Test the blocking call
    result = test_agent_connection(crew["architect"], user_request)
    
    if result:
        print("\n--- Architect Response (Blocking) ---")
        print(result)
        
    # 4. Optional: Test the streaming call with the Coder Agent
    # Uncomment to test the streaming parser and state machine
    # coder_prompt = "Write a python function to calculate the nth Fibonacci number using fast doubling."
    # test_agent_connection(crew["coder"], coder_prompt, use_streaming=True)

if __name__ == "__main__":
    main()