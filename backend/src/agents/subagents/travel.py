from typing import Dict, Any
from src.graph.state import AgentState
from src.tools.flights import search_transit

def travel_node(state: AgentState) -> Dict[str, Any]:
    """
    Travel Agent Node:
    Fetches candidate flights/trains based on destination and start date.
    """
    params = state.get("parsed_parameters", {})
    origin = params.get("origin", "Delhi")
    destination = params.get("destination", "")
    start_date = params.get("start_date", "")
    
    # Query flight/train tool
    print(f"[Travel Agent] Searching transit options from {origin} to {destination} starting on {start_date or 'default date'}...")
    transit_options = search_transit(origin, destination, start_date)
    
    return {
        "transit": transit_options
    }
