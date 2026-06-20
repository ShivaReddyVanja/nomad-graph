from typing import Dict, Any
from src.graph.state import AgentState
from src.tools.places import search_food

def food_node(state: AgentState) -> Dict[str, Any]:
    """
    Food Agent Node:
    Fetches dining and cafe candidates based on destination and style.
    """
    params = state.get("parsed_parameters", {})
    destination = params.get("destination", "")
    styles = params.get("travel_style", [])
    
    # Query food places tool
    print(f"[Food Agent] Searching dining options in {destination} matching styles: {styles}...")
    food_options = search_food(destination, styles)
    
    return {
        "food": food_options
    }
