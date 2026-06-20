import os
import requests
from typing import Tuple
from dotenv import load_dotenv

load_dotenv(override=True)

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS", "").strip('"').strip("'")

def geocode_city(city_name: str) -> Tuple[float, float]:
    """
    Resolves a city name to a (latitude, longitude) coordinate pair using Google Geocoding API.
    Raises ValueError if API key is missing, or RuntimeError if geocoding fails.
    """
    if not GOOGLE_MAPS_KEY:
        raise ValueError("[Geocoding Tool] Error: GOOGLE_MAPS API key is missing in the environment. Please add it to your .env file.")
        
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": city_name,
        "key": GOOGLE_MAPS_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
            
        raise RuntimeError(f"[Geocoding Tool] Geocoding API returned status '{data.get('status')}' for address: '{city_name}'")
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise e
        raise RuntimeError(f"[Geocoding Tool] Error querying Geocoding API: {e}") from e
