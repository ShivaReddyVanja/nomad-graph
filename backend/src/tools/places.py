import os
import requests
from typing import List
from src.graph.state import Place, Location, PlaceCategory
from src.tools.geocoding import geocode_city

# Load key from .env (cleaned from quotes)
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS", "").strip('"').strip("'")

def query_google_places(
    lat: float,
    lng: float,
    text_query: str,
    category: PlaceCategory,
    limit: int = 5
) -> List[Place]:
    """
    Queries Google Places API (New) for places near the given coordinates.
    Raises ValueError or RuntimeError on configuration/API errors.
    """
    if not GOOGLE_MAPS_KEY:
        raise ValueError("[Google Places Tool] Error: GOOGLE_MAPS API key is missing in the environment. Please add it to your .env file.")

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_KEY,
        # Restrict returned fields to optimize costs and retrieve needed data
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.editorialSummary,places.photos"
    }
    
    payload = {
        "textQuery": text_query,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": 5000.0  # 5 km search radius
            }
        },
        "maxResultCount": limit
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        results = response.json().get("places", [])
        
        places = []
        for r in results:
            display_name = r.get("displayName", {}).get("text", "Unknown Place")
            location_coords = r.get("location", {})
            latitude = location_coords.get("latitude", lat)
            longitude = location_coords.get("longitude", lng)
            
            # Map Google's price levels to a cost estimate number (1 to 4)
            price_level = r.get("priceLevel", "")
            cost_estimate = 2.0  # default to moderate
            if "INEXPENSIVE" in price_level:
                cost_estimate = 1.0
            elif "MODERATE" in price_level:
                cost_estimate = 2.0
            elif "EXPENSIVE" in price_level:
                cost_estimate = 3.0
            elif "VERY_EXPENSIVE" in price_level:
                cost_estimate = 4.0
                
            # Get editorial description if available, fallback to display name
            description = r.get("editorialSummary", {}).get("text", f"A local {category.value} recommendation: {display_name}.")

            # Extract the first photo's media URL if available
            photos = r.get("photos", [])
            photo_url = None
            if photos:
                photo_name = photos[0].get("name")
                if photo_name:
                    photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?key={GOOGLE_MAPS_KEY}&maxHeightPx=400"

            places.append(
                Place(
                    id=r.get("id"),
                    name=display_name,
                    category=category,
                    location=Location(
                        name=display_name,
                        address=r.get("formattedAddress", "Address unavailable"),
                        latitude=latitude,
                        longitude=longitude
                    ),
                    rating=r.get("rating"),  # Google ratings are out of 5.0 (no conversion needed)
                    cost_estimate=cost_estimate,
                    description=description,
                    photo_url=photo_url
                )
            )
        return places
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise e
        raise RuntimeError(f"[Google Places Tool] Error querying Google Places API: {e}") from e

def get_dynamic_food_fallback(destination: str, lat: float, lng: float) -> List[Place]:
    """
    Generates dynamic dining candidates using actual destination coordinates.
    """
    return [
        Place(
            id="fallback_food_1",
            name="Scenic Cafe & Restaurant",
            category=PlaceCategory.FOOD,
            location=Location(
                name="Scenic Cafe & Restaurant",
                address=f"Central Hub, {destination}, India",
                latitude=lat,
                longitude=lng
            ),
            rating=4.5,
            cost_estimate=2.0,
            description=f"A popular local dining spot in {destination} offering fresh local delicacies and coffee."
        ),
        Place(
            id="fallback_food_2",
            name="Traditional Kitchen Bistro",
            category=PlaceCategory.FOOD,
            location=Location(
                name="Traditional Kitchen Bistro",
                address=f"Market Street, {destination}, India",
                latitude=lat + 0.005,
                longitude=lng + 0.005
            ),
            rating=4.3,
            cost_estimate=2.0,
            description=f"A charming bistro in {destination} specializing in traditional local cuisine and dishes."
        ),
        Place(
            id="fallback_food_3",
            name="Spice Route Grill",
            category=PlaceCategory.FOOD,
            location=Location(
                name="Spice Route Grill",
                address=f"Food Street, {destination}, India",
                latitude=lat - 0.003,
                longitude=lng + 0.003
            ),
            rating=4.4,
            cost_estimate=3.0,
            description=f"An upscale grill house in {destination} showcasing regional spices and local recipes."
        ),
        Place(
            id="fallback_food_4",
            name="The Green Garden Cafe",
            category=PlaceCategory.FOOD,
            location=Location(
                name="The Green Garden Cafe",
                address=f"Nature Avenue, {destination}, India",
                latitude=lat + 0.002,
                longitude=lng - 0.004
            ),
            rating=4.6,
            cost_estimate=1.0,
            description=f"A cozy garden cafe in {destination} offering organic, farm-to-table breakfast and artisan beverages."
        ),
        Place(
            id="fallback_food_5",
            name="Sunset View Rooftop",
            category=PlaceCategory.FOOD,
            location=Location(
                name="Sunset View Rooftop",
                address=f"Skyline Heights, {destination}, India",
                latitude=lat - 0.005,
                longitude=lng - 0.002
            ),
            rating=4.7,
            cost_estimate=4.0,
            description=f"A scenic rooftop dining experience in {destination} with spectacular views and signature fusion dishes."
        ),
        Place(
            id="fallback_food_6",
            name="Local Street Food Plaza",
            category=PlaceCategory.FOOD,
            location=Location(
                name="Local Street Food Plaza",
                address=f"Bazaar Lane, {destination}, India",
                latitude=lat + 0.004,
                longitude=lng + 0.001
            ),
            rating=4.2,
            cost_estimate=1.0,
            description=f"A vibrant food plaza in {destination} featuring the city's best local street food vendors under one roof."
        )
    ]

def get_dynamic_activity_fallback(destination: str, lat: float, lng: float) -> List[Place]:
    """
    Generates dynamic activity candidates using actual destination coordinates.
    """
    return [
        Place(
            id="fallback_act_1",
            name=f"Historic Landmark {destination}",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Historic Landmark {destination}",
                address=f"Heritage Site, {destination}, India",
                latitude=lat - 0.005,
                longitude=lng - 0.005
            ),
            rating=4.7,
            cost_estimate=1.0,
            description=f"A highly recommended landmark and must-visit historical sightseeing point in {destination}."
        ),
        Place(
            id="fallback_act_2",
            name=f"Central Park & Viewpoint",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Central Park & Viewpoint",
                address=f"Park Area, {destination}, India",
                latitude=lat + 0.002,
                longitude=lng - 0.002
            ),
            rating=4.5,
            cost_estimate=0.0,
            description=f"A beautiful green space in {destination} offering walking paths and scenery."
        ),
        Place(
            id="fallback_act_3",
            name=f"Cultural Heritage Museum",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Cultural Heritage Museum",
                address=f"Museum Road, {destination}, India",
                latitude=lat + 0.006,
                longitude=lng - 0.003
            ),
            rating=4.6,
            cost_estimate=2.0,
            description=f"An informative museum in {destination} preserving regional art, costumes, and historical artifacts."
        ),
        Place(
            id="fallback_act_4",
            name=f"Botanical Gardens & Walkway",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Botanical Gardens & Walkway",
                address=f"Green Ring, {destination}, India",
                latitude=lat - 0.004,
                longitude=lng + 0.004
            ),
            rating=4.4,
            cost_estimate=1.0,
            description=f"A peaceful botanical sanctuary in {destination} exhibiting exotic plant species and glass greenhouses."
        ),
        Place(
            id="fallback_act_5",
            name=f"Ancient Temple Ruins",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Ancient Temple Ruins",
                address=f"Sacred Valley, {destination}, India",
                latitude=lat + 0.002,
                longitude=lng + 0.005
            ),
            rating=4.8,
            cost_estimate=0.0,
            description=f"A spiritual site in {destination} containing preserved temple carvings and archaeological architecture."
        ),
        Place(
            id="fallback_act_6",
            name=f"Artisanal Craft Market",
            category=PlaceCategory.SIGHTSEEING,
            location=Location(
                name=f"Artisanal Craft Market",
                address=f"Handicraft Quarter, {destination}, India",
                latitude=lat - 0.002,
                longitude=lng - 0.006
            ),
            rating=4.3,
            cost_estimate=0.0,
            description=f"A bustling craft market in {destination} where local artisans sell handmade pottery, textiles, and art."
        )
    ]

def search_food(destination: str, travel_styles: List[str]) -> List[Place]:
    """
    Resolves destination coordinates and fetches real restaurants/cafes from Google Places.
    Falls back to dynamic fallback locations on Places API query failure.
    """
    try:
        coords = geocode_city(destination)
    except Exception as e:
        print(f"[Places Tool] Geocoding failed for food search in {destination}: {e}. Raising error.")
        raise
        
    lat, lng = coords
    query_str = f"top restaurants cafe in {destination}"
    if travel_styles:
        query_str += f" specializing in {', '.join(travel_styles)}"
        
    try:
        places = query_google_places(lat, lng, query_str, PlaceCategory.FOOD, limit=12)
        if not places:
            print(f"[Places Tool] Places API returned empty results for food. Generating dynamic fallback at ({lat}, {lng}).")
            return get_dynamic_food_fallback(destination, lat, lng)
        return places
    except Exception as e:
        print(f"[Places Tool] Places API food query failed: {e}. Generating dynamic fallback at ({lat}, {lng}).")
        return get_dynamic_food_fallback(destination, lat, lng)

def search_activities(destination: str, travel_styles: List[str]) -> List[Place]:
    """
    Resolves destination coordinates and fetches tourist attractions/sights from Google Places.
    Falls back to dynamic fallback locations on Places API query failure.
    """
    try:
        coords = geocode_city(destination)
    except Exception as e:
        print(f"[Places Tool] Geocoding failed for activities search in {destination}: {e}. Raising error.")
        raise
        
    lat, lng = coords
    query_str = f"tourist attractions sights things to do in {destination}"
    if travel_styles:
        query_str += f" for {', '.join(travel_styles)}"
        
    try:
        places = query_google_places(lat, lng, query_str, PlaceCategory.SIGHTSEEING, limit=12)
        if not places:
            print(f"[Places Tool] Places API returned empty results for activities. Generating dynamic fallback at ({lat}, {lng}).")
            return get_dynamic_activity_fallback(destination, lat, lng)
        return places
    except Exception as e:
        print(f"[Places Tool] Places API activities query failed: {e}. Generating dynamic fallback at ({lat}, {lng}).")
        return get_dynamic_activity_fallback(destination, lat, lng)
