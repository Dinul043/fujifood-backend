"""
Restaurant Schemas — Request and Response DTOs for restaurant management.

Used by restaurant_admin to manage their own restaurant profile:
  - Update business info, delivery settings, branding, SEO
  - Toggle online/published status
"""
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════
#  Restaurant Update (Admin manages own restaurant)
# ═══════════════════════════════════════════════════

class UpdateRestaurantRequest(BaseModel):
    """Partial update of restaurant profile by restaurant admin."""

    # Business info
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    cuisine_type: Optional[str] = Field(None, max_length=200)
    gstin: Optional[str] = Field(None, max_length=20)
    fssai_number: Optional[str] = Field(None, max_length=20)

    # Location
    address_line1: Optional[str] = Field(None, max_length=300)
    address_line2: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)

    # Branding
    logo_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)

    # Delivery settings
    delivery_radius_km: Optional[float] = Field(None, ge=0, le=50)
    min_order_amount: Optional[float] = Field(None, ge=0)
    delivery_fee: Optional[float] = Field(None, ge=0)
    free_delivery_above: Optional[float] = Field(None, ge=0)
    avg_delivery_time_mins: Optional[int] = Field(None, ge=5, le=180)

    # Operational
    is_online: Optional[bool] = None
    is_published: Optional[bool] = None

    # SEO
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = Field(None, max_length=500)
    seo_keywords: Optional[str] = Field(None, max_length=500)


# ═══════════════════════════════════════════════════
#  Restaurant Response
# ═══════════════════════════════════════════════════

class RestaurantResponse(BaseModel):
    """Full restaurant profile response."""
    id: int
    uuid: str
    tenant_id: int
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    gstin: Optional[str] = None
    fssai_number: Optional[str] = None

    # Location
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Contact
    phone: str
    email: str
    website: Optional[str] = None

    # Branding
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    favicon_url: Optional[str] = None

    # Delivery
    delivery_radius_km: float
    min_order_amount: float
    delivery_fee: float
    free_delivery_above: Optional[float] = None
    avg_delivery_time_mins: int

    # Operational
    is_online: bool
    is_published: bool

    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None

    class Config:
        from_attributes = True


class RestaurantPublicResponse(BaseModel):
    """Public restaurant info for storefront (no internal fields)."""
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    city: str
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    delivery_radius_km: float
    min_order_amount: float
    delivery_fee: float
    free_delivery_above: Optional[float] = None
    avg_delivery_time_mins: int
    is_online: bool

    class Config:
        from_attributes = True
