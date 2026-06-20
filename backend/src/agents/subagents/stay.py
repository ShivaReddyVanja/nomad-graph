from typing import Dict, Any
from src.graph.state import AgentState
from src.tools.hotels import search_accommodation

def stay_node(state: AgentState) -> Dict[str, Any]:
    """
    Stay Agent Node:
    Fetches candidate hotel lodgings near destination coordinates.
    """
    params = state.get("parsed_parameters", {})
    destination = params.get("destination", "")
    budget = params.get("budget_level", "mid_range")
    
    # Query hotel tool
    print(f"[Stay Agent] Searching accommodation options in {destination} for budget: {budget}...")
    hotel_options = search_accommodation(destination, budget)
    
    return {
        "accommodation": hotel_options
    }
