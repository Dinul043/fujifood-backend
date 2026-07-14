"""
Geolocation utilities — distance calculation using Haversine formula.
No external API needed. Pure math.
"""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers.
    Uses the Haversine formula (accurate for small distances).

    Args:
        lat1, lon1: First point (e.g., restaurant)
        lat2, lon2: Second point (e.g., customer)

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_radius(
    restaurant_lat: float,
    restaurant_lng: float,
    customer_lat: float,
    customer_lng: float,
    radius_km: float,
) -> tuple[bool, float]:
    """
    Check if customer is within restaurant's delivery radius.

    Returns:
        (is_within, distance_km)
    """
    distance = haversine_distance(restaurant_lat, restaurant_lng, customer_lat, customer_lng)
    return distance <= radius_km, round(distance, 1)
