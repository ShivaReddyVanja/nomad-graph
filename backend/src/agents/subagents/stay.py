from typing import Dict, Any
from src.graph.state import AgentState
from src.tools.hotels import search_accommodation

def stay_node(state: AgentState) -> Dict[str, Any]:
    """
    Stay Agent Node:
    Loops over all planned destinations and gathers candidate hotel options for each city.
    """
    params = state.get("parsed_parameters", {})
    budget = params.get("budget_level", "mid_range")
    planned_dests = state.get("planned_destinations", [])
    
    if not planned_dests:
        destination = params.get("destination", "")
        print(f"[Stay Agent] Warning: No planned_destinations. Searching accommodation in {destination}...")
        hotel_options = search_accommodation(destination, budget)
        return {"accommodation": hotel_options}
        
    hotel_options = []
    print(f"[Stay Agent] Searching accommodations across planned destinations: {[d.destination for d in planned_dests]}...")
    for alloc in planned_dests:
        dest = alloc.destination
        print(f"[Stay Agent] Searching stays in: {dest}...")
        hotels = search_accommodation(dest, budget)
        if hotels:
            hotel_options.extend(hotels)
            
    return {
        "accommodation": hotel_options
    }
