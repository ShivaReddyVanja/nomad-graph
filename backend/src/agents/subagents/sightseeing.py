from typing import Dict, Any
from src.graph.state import AgentState
from src.tools.places import search_activities

def sightseeing_node(state: AgentState) -> Dict[str, Any]:
    """
    Sightseeing Agent Node:
    Fetches attractions, parks, and museums based on destination and style.
    """
    params = state.get("parsed_parameters", {})
    destination = params.get("destination", "")
    styles = params.get("travel_style", [])
    
    # Query activities places tool
    print(f"[Sightseeing Agent] Searching activity and sight options in {destination} matching styles: {styles}...")
    activity_options = search_activities(destination, styles)
    
    return {
        "activities": activity_options
    }
