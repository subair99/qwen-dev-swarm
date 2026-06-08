from typing import List, Dict, Any, Callable
from config.settings import settings

class QwenAgent:
    def __init__(
        self, 
        name: str, 
        instructions: str, 
        tools: List[Callable] = None
    ):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []

# Define your first two specialized swarm components
def create_swarm_agents() -> Dict[str, QwenAgent]:
    """Initializes the minimal dev swarm crew."""
    
    architect = QwenAgent(
        name="Software_Architect",
        instructions="You break down complex software engineering feature requests into step-by-step modular designs and technical tasks."
    )
    
    coder = QwenAgent(
        name="Lead_Coder",
        instructions="You implement elegant, efficient, and well-tested Python code according to a software architecture design specification."
    )
    
    return {
        "architect": architect,
        "coder": coder
    }