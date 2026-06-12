import asyncio
import logging
from threading import Lock
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

# Compile the LangGraph pipeline once at module import time and expose it
# as a module-level singleton to avoid recompiling on every frame.
_logger = logging.getLogger("app.agents.agent_graph")
_COMPILED_AGENT_PIPELINE = None
_COMPILED_AGENT_PIPELINE_LOCK = Lock()

try:
    _COMPILED_AGENT_PIPELINE = build_agent_graph()
    _logger.info("Compiled LangGraph agent pipeline at module import")
except Exception as _exc:  # pragma: no cover - defensive logging on import
    _logger.exception("Failed to compile LangGraph pipeline at import: %s", _exc)
    _COMPILED_AGENT_PIPELINE = None

async def run_agent_pipeline(raw_cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point to be called by the FastAPI/CV pipeline.
    Passes raw frame data into the LangGraph execution.
    """
    initial_state = {"raw_data": raw_cv_data}

    # Reuse the module-level compiled pipeline. If compilation failed at
    # import time, attempt a lazy, thread-safe compile on first use.
    pipeline = _COMPILED_AGENT_PIPELINE
    if pipeline is None:
        with _COMPILED_AGENT_PIPELINE_LOCK:
            # Double-check inside the lock
            if _COMPILED_AGENT_PIPELINE is None:
                try:
                    _logger.info("Lazy-compiling LangGraph pipeline on first use")
                    globals()['_COMPILED_AGENT_PIPELINE'] = build_agent_graph()
                except Exception as exc:  # pragma: no cover - runtime fallback
                    _logger.exception("Failed to compile LangGraph pipeline on demand: %s", exc)
                    raise
            pipeline = _COMPILED_AGENT_PIPELINE

    # Invoke the LangGraph pipeline on a worker thread; it is safe to call
    # concurrently as the compiled pipeline instance is stateless per-invocation.
    final_state = await asyncio.to_thread(pipeline.invoke, initial_state)

    return final_state
