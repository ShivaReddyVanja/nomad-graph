from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.graph.state import AgentState, TransitOption
from src.tools.flights import search_transit

def get_next_date(date_str: str, days: int) -> str:
    """
    Safely adds days to a YYYY-MM-DD date string. Falls back to original string on error.
    """
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        next_dt = dt + timedelta(days=days)
        return next_dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

from langchain_core.runnables import RunnableConfig
from src.utils.logger import log_agent, log_dev, emit_event

def travel_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Travel Agent Node:
    Loops over the planned destinations list and fetches transit candidates for each segment of the journey
    (e.g., Origin -> Destination 1 -> Destination 2 -> Origin).
    """
    from collections import defaultdict
    from src.tools.flights import get_airport_code
    from src.graph.state import TravelMode
    from src.tools.routes import get_route_directions
    
    emit_event(config, {"type": "node_start", "node": "travel"})
    params = state.get("parsed_parameters", {})
    origin = params.get("origin", "Delhi")
    start_date = params.get("start_date", "")
    planned_dests = state.get("planned_destinations", [])
    styles = params.get("travel_style", [])
    
    def get_road_transit(start_city: str, end_city: str) -> List[TransitOption]:
        route_data = get_route_directions(start_city, end_city, "driving")
        dur_mins = route_data.get("duration_minutes", 120)
        dist_meters = route_data.get("distance_meters", 100000.0)
        est_price = max(500, int((dist_meters / 1000.0) * 15.0))
        
        dep_dt = datetime.strptime("09:00", "%H:%M")
        arr_dt = dep_dt + timedelta(minutes=dur_mins)
        dep_str = "09:00"
        arr_str = arr_dt.strftime("%H:%M")
        
        return [
            TransitOption(
                id=f"road_{start_city.lower().replace(' ', '_')}_{end_city.lower().replace(' ', '_')}_0",
                origin=start_city,
                destination=end_city,
                departure_time=dep_str,
                arrival_time=arr_str,
                mode=TravelMode.DRIVING,
                duration_minutes=dur_mins,
                estimated_price=est_price,
                carrier="Self-Drive / Ride"
            )
        ]
    
    # Check if this segment requires a flight or driving
    def resolve_mode_and_log(start_city: str, end_city: str) -> bool:
        origin_code = get_airport_code(start_city)
        dest_code = get_airport_code(end_city)
        is_flight = origin_code != dest_code and not (origin_code == "DEL" and dest_code == "DEL")
        
        if is_flight:
            emit_event(config, {"type": "api_call", "tool": "Google Flights"})
            log_agent(config, f"🔍 Searching Google Flights for {start_city} to {end_city}...")
        else:
            emit_event(config, {"type": "api_call", "tool": "Google Maps"})
            log_agent(config, f"🔍 Finding road routes and driving times from {start_city} to {end_city}...")
        return is_flight

    if not planned_dests:
        destination = params.get("destination", "")
        is_flight = resolve_mode_and_log(origin, destination)
        
        import time
        if not is_flight:
            transit_options = get_road_transit(origin, destination)
            log_agent(config, f"🚗 Sourced driving route from {origin} ➔ {destination} ({transit_options[0].duration_minutes} mins)!")
        else:
            start_time = time.perf_counter()
            transit_options = search_transit(origin, destination, start_date)
            dur = time.perf_counter() - start_time
            log_dev(config, f"[Latency Metric] Travel Agent flight search ({origin} -> {destination}): {dur:.2f}s")
            if transit_options:
                for idx, opt in enumerate(transit_options):
                    opt.id = f"flight_{origin.lower().replace(' ', '_')}_{destination.lower().replace(' ', '_')}_{idx}"
                log_agent(config, f"✈️  Found flight connections for {origin} ➔ {destination}!")
            else:
                # Smart fallback for single destination
                road_route = get_road_transit(origin, destination)
                driving_dur = road_route[0].duration_minutes if road_route else 9999
                
                if driving_dur <= 360:
                    log_agent(config, f"🚗 Sourced direct driving route from {origin} ➔ {destination} ({driving_dur} mins) since it is nearby.")
                    transit_options = road_route
                else:
                    log_agent(config, f"🔍 No direct flights found for {origin} ➔ {destination} (distance too far for direct drive). Resolving nearest major commercial airport...")
                    try:
                        from src.tools.flights import resolve_nearest_airport
                        airport_info = resolve_nearest_airport(destination)
                        airport_city = airport_info.airport_city
                        airport_code = airport_info.iata_code
                        
                        log_agent(config, f"📍 Nearest major airport to {destination} resolved as {airport_city} ({airport_code}).")
                        
                        # Search flights to that airport
                        log_agent(config, f"🔍 Searching flights from {origin} to nearest airport {airport_city}...")
                        flight_options = search_transit(origin, airport_city, start_date)
                        
                        if flight_options:
                            for idx, opt in enumerate(flight_options):
                                opt.id = f"flight_{origin.lower().replace(' ', '_')}_{airport_city.lower().replace(' ', '_')}_{idx}"
                            
                            road_to_dest = get_road_transit(airport_city, destination)
                            log_agent(config, f"✈️🚗 Routing via {airport_city} ({airport_code}): flight to {airport_city} + drive to {destination} ({road_to_dest[0].duration_minutes} mins).")
                            transit_options = [flight_options[0]] + road_to_dest
                        else:
                            log_agent(config, f"⚠️ No flight connections found to the nearest airport {airport_city}. Falling back to driving the whole way...")
                            transit_options = road_route
                    except Exception as e:
                        log_dev(config, f"[Travel Agent] Error resolving nearest airport: {e}. Falling back to direct drive.")
                        transit_options = road_route

        if transit_options:
            segments = defaultdict(list)
            for opt in transit_options:
                segments[f"{opt.origin} ➔ {opt.destination}"].append(opt)
            
            card_lines = ["✈️ TRANSIT OPTIONS GATHERED", "━━━━━━━━━━━━━━━━━━━━━━━━"]
            for seg, opts in segments.items():
                card_lines.append(f"📍 {seg}")
                for opt in opts:
                    price_str = f"₹{int(opt.estimated_price):,}" if opt.estimated_price else "Price unavailable"
                    emoji = "✈️" if opt.mode == TravelMode.FLIGHT else "🚗"
                    card_lines.append(f"  • {emoji} {opt.carrier} ({opt.departure_time}) — {price_str}")
            card_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
            log_agent(config, "\n".join(card_lines))

        emit_event(config, {
            "type": "candidates_discovered",
            "category": "transit",
            "candidates": [opt.model_dump() for opt in transit_options]
        })
        emit_event(config, {"type": "node_end", "node": "travel"})
        return {"transit": transit_options}
        
    transit_options = []
    current_origin = origin
    current_date = start_date
    
    log_agent(config, "Finding travel options and routes...")
    log_dev(config, f"[Travel Agent] Building transit chain for destinations: {[d.destination for d in planned_dests]} starting on {start_date}...")
    
    # 1. Query transit for all forward hops in the route
    for i, alloc in enumerate(planned_dests):
        dest = alloc.destination
        days = alloc.duration_days
        
        log_dev(config, f"[Travel Agent] Hop: {current_origin} -> {dest} (Date: {current_date or 'default'})")
        
        # If it's an intermediate hop and the style suggests driving, force road mode
        has_road_style = any(s.lower() in ["motorcycle riding", "motorcycle", "riding", "road trip", "driving", "car", "roadtrip"] for s in styles)
        
        is_flight = True
        if i > 0 and has_road_style:
            emit_event(config, {"type": "api_call", "tool": "Google Maps"})
            log_agent(config, f"🔍 Finding road routes and driving times from {current_origin} to {dest}...")
            is_flight = False
        else:
            is_flight = resolve_mode_and_log(current_origin, dest)
        
        import time
        if not is_flight:
            options = get_road_transit(current_origin, dest)
            log_agent(config, f"🚗 Sourced driving route from {current_origin} ➔ {dest} ({options[0].duration_minutes} mins)!")
        else:
            start_time = time.perf_counter()
            options = search_transit(current_origin, dest, current_date)
            dur = time.perf_counter() - start_time
            log_dev(config, f"[Latency Metric] Travel Agent flight search ({current_origin} -> {dest}): {dur:.2f}s")
            if options:
                for idx, opt in enumerate(options):
                    opt.id = f"flight_{current_origin.lower().replace(' ', '_')}_{dest.lower().replace(' ', '_')}_{idx}"
                log_agent(config, f"✈️  Found flight connections for {current_origin} ➔ {dest}!")
            else:
                # Smart forward fallback
                road_route = get_road_transit(current_origin, dest)
                driving_dur = road_route[0].duration_minutes if road_route else 9999
                
                if driving_dur <= 360:
                    log_agent(config, f"🚗 Sourced direct driving route from {current_origin} ➔ {dest} ({driving_dur} mins) since it is nearby.")
                    options = road_route
                else:
                    log_agent(config, f"🔍 No direct flights found for {current_origin} ➔ {dest} (distance too far for direct drive). Resolving nearest major commercial airport...")
                    try:
                        from src.tools.flights import resolve_nearest_airport
                        airport_info = resolve_nearest_airport(dest)
                        airport_city = airport_info.airport_city
                        airport_code = airport_info.iata_code
                        
                        log_agent(config, f"📍 Nearest major airport to {dest} resolved as {airport_city} ({airport_code}).")
                        
                        # Search flights to that airport
                        log_agent(config, f"🔍 Searching flights from {current_origin} to nearest airport {airport_city}...")
                        flight_options = search_transit(current_origin, airport_city, current_date)
                        
                        if flight_options:
                            for idx, opt in enumerate(flight_options):
                                opt.id = f"flight_{current_origin.lower().replace(' ', '_')}_{airport_city.lower().replace(' ', '_')}_{idx}"
                            
                            road_to_dest = get_road_transit(airport_city, dest)
                            log_agent(config, f"✈️🚗 Routing via {airport_city} ({airport_code}): flight to {airport_city} + drive to {dest} ({road_to_dest[0].duration_minutes} mins).")
                            options = [flight_options[0]] + road_to_dest
                        else:
                            log_agent(config, f"⚠️ No flight connections found to the nearest airport {airport_city}. Falling back to driving the whole way...")
                            options = road_route
                    except Exception as e:
                        log_dev(config, f"[Travel Agent] Error resolving nearest airport: {e}. Falling back to direct drive.")
                        options = road_route
        
        if options:
            transit_options.extend(options)
            
        current_origin = dest
        current_date = get_next_date(current_date, days)
        
    # 2. Query return transit back to starting origin
    log_dev(config, f"[Travel Agent] Hop (Return): {current_origin} -> {origin} (Date: {current_date or 'default'})")
    is_flight = resolve_mode_and_log(current_origin, origin)
    
    import time
    if not is_flight:
        return_options = get_road_transit(current_origin, origin)
        log_agent(config, f"🚗 Sourced driving route from {current_origin} ➔ {origin} ({return_options[0].duration_minutes} mins)!")
    else:
        start_time = time.perf_counter()
        return_options = search_transit(current_origin, origin, current_date)
        dur = time.perf_counter() - start_time
        log_dev(config, f"[Latency Metric] Travel Agent flight search ({current_origin} -> {origin}): {dur:.2f}s")
        if return_options:
            for idx, opt in enumerate(return_options):
                opt.id = f"flight_{current_origin.lower().replace(' ', '_')}_{origin.lower().replace(' ', '_')}_{idx}"
            log_agent(config, f"✈️  Found flight connections for {current_origin} ➔ {origin}!")
        else:
            # Smart return fallback
            road_route = get_road_transit(current_origin, origin)
            driving_dur = road_route[0].duration_minutes if road_route else 9999
            
            if driving_dur <= 360:
                log_agent(config, f"🚗 Sourced direct driving route from {current_origin} ➔ {origin} ({driving_dur} mins) since it is nearby.")
                return_options = road_route
            else:
                log_agent(config, f"🔍 No direct flights found for {current_origin} ➔ {origin} (distance too far for direct drive). Resolving nearest major commercial airport...")
                try:
                    from src.tools.flights import resolve_nearest_airport
                    airport_info = resolve_nearest_airport(current_origin)
                    airport_city = airport_info.airport_city
                    airport_code = airport_info.iata_code
                    
                    log_agent(config, f"📍 Nearest major airport to starting point {current_origin} resolved as {airport_city} ({airport_code}).")
                    
                    # Drive from current destination to the nearest airport, then fly from there to origin
                    road_to_airport = get_road_transit(current_origin, airport_city)
                    
                    log_agent(config, f"🔍 Searching flights from {airport_city} to {origin}...")
                    flight_options = search_transit(airport_city, origin, current_date)
                    
                    if flight_options:
                        for idx, opt in enumerate(flight_options):
                            opt.id = f"flight_{airport_city.lower().replace(' ', '_')}_{origin.lower().replace(' ', '_')}_{idx}"
                        
                        log_agent(config, f"✈️🚗 Routing via {airport_city} ({airport_code}): drive to {airport_city} ({road_to_airport[0].duration_minutes} mins) + flight to {origin}.")
                        return_options = road_to_airport + [flight_options[0]]
                    else:
                        log_agent(config, f"⚠️ No flight connections found from the nearest airport {airport_city}. Falling back to driving the whole way...")
                        return_options = road_route
                except Exception as e:
                    log_dev(config, f"[Travel Agent] Error resolving nearest airport: {e}. Falling back to direct drive.")
                    return_options = road_route
    
    if return_options:
        transit_options.extend(return_options)
        
    if transit_options:
        segments = defaultdict(list)
        for opt in transit_options:
            segments[f"{opt.origin} ➔ {opt.destination}"].append(opt)
        
        card_lines = ["✈️ TRANSIT OPTIONS GATHERED", "━━━━━━━━━━━━━━━━━━━━━━━━"]
        for seg, opts in segments.items():
            card_lines.append(f"📍 {seg}")
            for opt in opts:
                price_str = f"₹{int(opt.estimated_price):,}" if opt.estimated_price else "Price unavailable"
                emoji = "✈️" if opt.mode == TravelMode.FLIGHT else "🚗"
                card_lines.append(f"  • {emoji} {opt.carrier} ({opt.departure_time}) — {price_str}")
            card_lines.append("")
        card_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        log_agent(config, "\n".join(card_lines))
            
    emit_event(config, {
        "type": "candidates_discovered",
        "category": "transit",
        "candidates": [opt.model_dump() for opt in transit_options]
    })
    emit_event(config, {"type": "node_end", "node": "travel"})
    return {
        "transit": transit_options
    }
