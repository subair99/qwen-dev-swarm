import os
from openai import OpenAI
from config.settings import settings
from swarm.agents import create_swarm_agents

def test_qwen_connection(agent, prompt: str):
    # Initialize the client with Qwen endpoints
    client = OpenAI(
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL
    )
    
    print(f"🤖 [{agent.name}] processing request...")
    
    response = client.chat.completions.create(
        model="qwen-turbo",  # Or qwen-max / local model name depending on your setup
        messages=[
            {"role": "system", "content": agent.instructions},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def main():
    # 1. Validate Env configuration
    try:
        settings.validate()
    except ValueError as e:
        print(e)
        return

    # 2. Spin up the swarm crew
    crew = create_swarm_agents()
    
    # 3. Quick dry-run using the Architect Agent
    user_request = "Design a basic fastAPI logging middleware."
    result = test_qwen_connection(crew["architect"], user_request)
    
    print("\n--- Architect Response ---")
    print(result)

if __name__ == "__main__":
    main()