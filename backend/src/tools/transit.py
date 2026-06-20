from typing import List
from src.graph.state import TransitOption, TravelMode

def search_transit(destination: str, start_date: str) -> List[TransitOption]:
    """
    Mock search for flights/trains to the destination.
    """
    return [
        TransitOption(
            id="transit_flight_1",
            origin="San Francisco (SFO)",
            destination=destination,
            departure_time="08:00",
            arrival_time="16:00",
            mode=TravelMode.FLIGHT,
            duration_minutes=480,
            estimated_price=450.0,
            carrier="United Airlines"
        ),
        TransitOption(
            id="transit_flight_2",
            origin="San Francisco (SFO)",
            destination=destination,
            departure_time="14:00",
            arrival_time="22:00",
            mode=TravelMode.FLIGHT,
            duration_minutes=480,
            estimated_price=380.0,
            carrier="Delta Air Lines"
        )
    ]
