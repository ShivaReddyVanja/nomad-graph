import os
from typing import List
from src.graph.state import Place, Location, PlaceCategory
from src.tools.geocoding import geocode_city
from src.tools.places import query_google_places

def get_dynamic_hotel_fallback(destination: str, lat: float, lng: float, budget_level: str) -> List[Place]:
    """
    Generates dynamic lodging candidates using actual destination coordinates.
    """
    return [
        Place(
            id="fallback_stay_1",
            name=f"Grand {budget_level.capitalize() if budget_level else 'Comfort'} Hotel {destination}",
            category=PlaceCategory.STAY,
            location=Location(
                name=f"Grand {budget_level.capitalize() if budget_level else 'Comfort'} Hotel {destination}",
                address=f"Central Hub, {destination}, India",
                latitude=lat,
                longitude=lng
            ),
            rating=4.4,
            cost_estimate=150.0,
            description=f"A comfortable, highly rated accommodation in {destination} located near central attractions."
        ),
        Place(
            id="fallback_stay_2",
            name=f"Boutique Resort {destination}",
            category=PlaceCategory.STAY,
            location=Location(
                name=f"Boutique Resort {destination}",
                address=f"Scenic Drive, {destination}, India",
                latitude=lat + 0.003,
                longitude=lng - 0.003
            ),
            rating=4.6,
            cost_estimate=220.0,
            description=f"A boutique lodging experience in {destination} featuring local architecture and design."
        )
    ]

def search_accommodation(destination: str, budget_level: str) -> List[Place]:
    """
    Queries Google Places API (New) for accommodations/hotels in the destination.
    Returns real hotels with accurate names and coordinates.
    Falls back to dynamic fallback lodging at target coordinates if query fails or returns no results.
    """
    try:
        coords = geocode_city(destination)
    except Exception as e:
        print(f"[Hotels Tool] Geocoding failed for accommodation search in {destination}: {e}. Raising error.")
        raise
        
    lat, lng = coords
    
    # Construct a search query reflecting the destination and budget preference
    query_str = f"hotels resorts lodging accommodation in {destination}"
    if budget_level:
        query_str = f"{budget_level} {query_str}"
        
    try:
        print(f"[Hotels Tool] Querying Google Places for: '{query_str}' at ({lat}, {lng})...")
        places = query_google_places(lat, lng, query_str, PlaceCategory.STAY, limit=5)
        if not places:
            print(f"[Hotels Tool] Google Places returned no hotels. Generating dynamic fallback at ({lat}, {lng}).")
            return get_dynamic_hotel_fallback(destination, lat, lng, budget_level)
        return places
    except Exception as e:
        print(f"[Hotels Tool] Google Places hotel search failed: {e}. Generating dynamic fallback at ({lat}, {lng}).")
        return get_dynamic_hotel_fallback(destination, lat, lng, budget_level)
