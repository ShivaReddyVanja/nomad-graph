from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.agents.gatekeeper import gatekeeper_node
from src.agents.planner import planner_node
from src.agents.captain import captain_node
from src.agents.subagents import travel_node, stay_node, food_node, sightseeing_node

def check_gatekeeper_status(state: AgentState) -> str:
    """
    Conditional routing function for the Gatekeeper:
    - If is_validated is True, route to the Planner to break down region/trip.
    - If is_validated is False, route to END (wait for clarifying answers).
    """
    if state.get("is_validated", False):
        return "planner"
    return END

def route_from_captain(state: AgentState) -> str:
    """
    Conditional routing function for the Captain orchestrator:
    Determines which subagent to route to next based on what candidate lists
    are currently missing in the state memory.
    """
    # 1. If final compiled itinerary is present, the graph is complete.
    if state.get("final_itinerary") is not None:
        return END
        
    transit_len = len(state.get("transit") or [])
    accommodation_len = len(state.get("accommodation") or [])
    food_len = len(state.get("food") or [])
    activities_len = len(state.get("activities") or [])
    print(f"[Router Debug] Transit: {transit_len}, Accommodation: {accommodation_len}, Food: {food_len}, Activities: {activities_len}")

    # 2. Sequential candidate routing
    if not state.get("transit"):
        print("[Router Debug] Routing to: travel")
        return "travel"
    if not state.get("accommodation"):
        print("[Router Debug] Routing to: stay")
        return "stay"
    if not state.get("food"):
        print("[Router Debug] Routing to: food")
        return "food"
    if not state.get("activities"):
        print("[Router Debug] Routing to: sightseeing")
        return "sightseeing"
        
    # 3. If all candidates are gathered but final_itinerary is None,
    # route back to captain to compile the final plan (Phase 5).
    print("[Router Debug] All candidates gathered, routing to: captain for compilation")
    return "captain"

from langgraph.checkpoint.memory import MemorySaver

def build_workflow():
    # 1. Initialize StateGraph with AgentState schema
    workflow = StateGraph(AgentState)
    
    # 2. Add Nodes
    workflow.add_node("gatekeeper", gatekeeper_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("captain", captain_node)
    workflow.add_node("travel", travel_node)
    workflow.add_node("stay", stay_node)
    workflow.add_node("food", food_node)
    workflow.add_node("sightseeing", sightseeing_node)
    
    # 3. Add Edges & Conditional Routing
    workflow.set_entry_point("gatekeeper")
    
    # Gatekeeper conditional routing -> routes to planner on success
    workflow.add_conditional_edges(
        "gatekeeper",
        check_gatekeeper_status,
        {
            "planner": "planner",
            END: END
        }
    )
    
    # Planner node runs, updates state with destinations, and routes directly to Captain
    workflow.add_edge("planner", "captain")
    
    # Captain conditional routing (decides next step based on candidate state)
    workflow.add_conditional_edges(
        "captain",
        route_from_captain,
        {
            "travel": "travel",
            "stay": "stay",
            "food": "food",
            "sightseeing": "sightseeing",
            "captain": "captain",
            END: END
        }
    )
    
    # All subagents route back to Captain to sync state and progress
    workflow.add_edge("travel", "captain")
    workflow.add_edge("stay", "captain")
    workflow.add_edge("food", "captain")
    workflow.add_edge("sightseeing", "captain")
    
    # Compile the graph with a memory checkpointer for state preservation
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)