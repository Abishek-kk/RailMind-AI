import asyncio
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END
from app.agents.perception_agent import perception_node
from app.agents.reasoning_agent import reasoning_node
from app.agents.intervention_agent import intervention_node

# Define the global state for the LangGraph pipeline
class AgentState(TypedDict):
    raw_data: Dict[str, Any]         # Input from CV/LSTM pipeline
    observation: Dict[str, Any]      # Output of Perception
    decision: Dict[str, Any]         # Output of Reasoning
    alert_payload: Dict[str, Any]    # Output of Intervention
    execution_status: List[str]      # Output of Intervention

def build_agent_graph():
    """Compiles the LangGraph Multi-Agent Workflow."""
    
    # Initialize the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (Agents)
    workflow.add_node("perception", perception_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("intervention", intervention_node)
    
    # Define the data flow (edges)
    workflow.set_entry_point("perception")
    workflow.add_edge("perception", "reasoning")
    workflow.add_edge("reasoning", "intervention")
    workflow.add_edge("intervention", END)
    
    # Compile the graph
    return workflow.compile()

async def run_agent_pipeline(raw_cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point to be called by the FastAPI/CV pipeline.
    Passes raw frame data into the LangGraph execution.
    """
    initial_state = {"raw_data": raw_cv_data}
    agent_pipeline = build_agent_graph()
    
    # Invoke the LangGraph pipeline
    # LangGraph returns the final state object after traversing all nodes
    final_state = await asyncio.to_thread(agent_pipeline.invoke, initial_state)
    
    return final_state
