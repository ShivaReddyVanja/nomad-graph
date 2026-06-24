import os
import requests
from typing import Tuple
from dotenv import load_dotenv

load_dotenv(override=True)

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS", "").strip('"').strip("'")

# Simple in-memory cache for resolved city/location coordinates
_GEOCODE_CACHE = {}

def geocode_city(city_name: str) -> Tuple[float, float]:
    """
    Resolves a city name to a (latitude, longitude) coordinate pair using Google Geocoding API.
    Raises ValueError if API key is missing, or RuntimeError if geocoding fails.
    """
    if not city_name:
        raise ValueError("[Geocoding Tool] Error: City name cannot be empty.")

    city_key = city_name.strip().lower()
    if city_key in _GEOCODE_CACHE:
        print(f"[Geocoding Tool] Cache hit for '{city_name}': {_GEOCODE_CACHE[city_key]}", flush=True)
        return _GEOCODE_CACHE[city_key]

    if not GOOGLE_MAPS_KEY:
        raise ValueError("[Geocoding Tool] Error: GOOGLE_MAPS API key is missing in the environment. Please add it to your .env file.")
        
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": city_name,
        "key": GOOGLE_MAPS_KEY
    }
    
    import time
    start_time = time.perf_counter()
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        dur = time.perf_counter() - start_time
        print(f"[Latency Metric] Geocoding API call for '{city_name}': {dur:.2f}s", flush=True)
        
        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            coords = (location["lat"], location["lng"])
            _GEOCODE_CACHE[city_key] = coords
            return coords
            
        raise RuntimeError(f"[Geocoding Tool] Geocoding API returned status '{data.get('status')}' for address: '{city_name}'")
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise e
        raise RuntimeError(f"[Geocoding Tool] Error querying Geocoding API: {e}") from e
