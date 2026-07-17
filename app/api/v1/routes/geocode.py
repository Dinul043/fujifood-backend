"""
Geocode Routes — Delivery radius check.

Endpoints:
  POST /geo/check-delivery  → Check if coordinates are within delivery radius
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.models.tenant import Tenant
from app.utils.geo import is_within_radius

router = APIRouter()


class DeliveryCheckRequest(BaseModel):
    latitude: float
    longitude: float
    tenant_slug: str = "a2b"


class AddressCheckRequest(BaseModel):
    address: str
    city: str
    pincode: str = ""
    tenant_slug: str = "a2b"


@router.post("/check-delivery-address", summary="Check delivery by address text")
async def check_delivery_by_address(request: AddressCheckRequest, db: Session = Depends(get_db)):
    """
    Geocode an address and check if it's within delivery radius.
    Uses OpenStreetMap Nominatim (free).
    """
    import httpx

    tenant = db.query(Tenant).filter(Tenant.slug == request.tenant_slug, Tenant.deleted_at.is_(None)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = db.query(Restaurant).filter(Restaurant.tenant_id == tenant.id, Restaurant.deleted_at.is_(None)).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # If restaurant doesn't have coordinates, allow
    if not restaurant.latitude or not restaurant.longitude:
        return {"deliverable": True, "message": "Delivery available"}

    # Geocode the address
    query = f"{request.address}, {request.city} {request.pincode}".strip()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "FujiFood/1.0"},
                timeout=10,
            )
            results = resp.json()
    except:
        return {"deliverable": True, "message": "Could not verify address, allowing order"}

    if not results:
        return {"deliverable": True, "message": "Address could not be geocoded, allowing order"}

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])

    within, distance = is_within_radius(
        restaurant.latitude, restaurant.longitude, lat, lon, restaurant.delivery_radius_km
    )

    if within:
        return {"deliverable": True, "distance_km": distance, "message": f"Delivery available ({distance} km away)"}
    else:
        return {"deliverable": False, "distance_km": distance, "message": f"Sorry, this address is {distance} km away. We deliver within {restaurant.delivery_radius_km} km only."}


@router.post("/check-delivery", summary="Check if location is within delivery radius")
async def check_delivery(request: DeliveryCheckRequest, db: Session = Depends(get_db)):
    """
    Check if the given coordinates are within the restaurant's delivery radius.
    Returns: deliverable (bool), distance (km), radius (km)
    """
    tenant = db.query(Tenant).filter(Tenant.slug == request.tenant_slug, Tenant.deleted_at.is_(None)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = db.query(Restaurant).filter(Restaurant.tenant_id == tenant.id, Restaurant.deleted_at.is_(None)).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # If restaurant doesn't have coordinates set, allow all orders
    if not restaurant.latitude or not restaurant.longitude:
        return {"deliverable": True, "distance_km": 0, "radius_km": restaurant.delivery_radius_km, "message": "Delivery available"}

    within, distance = is_within_radius(
        restaurant.latitude,
        restaurant.longitude,
        request.latitude,
        request.longitude,
        restaurant.delivery_radius_km,
    )

    if within:
        return {
            "deliverable": True,
            "distance_km": distance,
            "radius_km": restaurant.delivery_radius_km,
            "message": f"Delivery available ({distance} km away)",
        }
    else:
        return {
            "deliverable": False,
            "distance_km": distance,
            "radius_km": restaurant.delivery_radius_km,
            "message": f"Sorry, you're {distance} km away. We deliver within {restaurant.delivery_radius_km} km only.",
        }
