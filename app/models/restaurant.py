"""
Restaurant model — the restaurant business details for a tenant.

Each tenant has exactly one restaurant profile (future: multiple branches).
"""
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TenantBaseModel


class Restaurant(TenantBaseModel):
    """
    Restaurant profile — business details, location, settings.
    """
    __tablename__ = "restaurants"

    # Foreign key to tenant
    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Business info
    name            = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    cuisine_type    = Column(String(200), nullable=True)   # "Indian, Chinese, Fast Food"
    gstin           = Column(String(20), nullable=True)    # Tax registration
    fssai_number    = Column(String(20), nullable=True)    # Food license

    # Location
    address_line1   = Column(String(300), nullable=True)
    address_line2   = Column(String(300), nullable=True)
    city            = Column(String(100), nullable=True)
    state           = Column(String(100), nullable=True)
    pincode         = Column(String(10), nullable=True)
    country         = Column(String(50), default="India", nullable=True)
    latitude        = Column(Float, nullable=True)
    longitude       = Column(Float, nullable=True)

    # Contact
    phone           = Column(String(20), nullable=True)
    email           = Column(String(255), nullable=True)
    website         = Column(String(255), nullable=True)

    # Branding
    logo_url        = Column(String(500), nullable=True)
    banner_url      = Column(String(500), nullable=True)
    favicon_url     = Column(String(500), nullable=True)

    # Delivery settings
    delivery_radius_km      = Column(Float, default=5.0, nullable=False)
    min_order_amount        = Column(Float, default=0.0, nullable=False)
    delivery_fee            = Column(Float, default=0.0, nullable=False)
    free_delivery_above     = Column(Float, nullable=True)  # Free delivery above this amount
    avg_delivery_time_mins  = Column(Integer, default=30, nullable=False)

    # Operational
    is_online               = Column(Boolean, default=False, nullable=False)  # Currently accepting orders
    is_published            = Column(Boolean, default=False, nullable=False)  # Website is live

    # SEO
    seo_title               = Column(String(200), nullable=True)
    seo_description         = Column(String(500), nullable=True)
    seo_keywords            = Column(String(500), nullable=True)

    # Relationships
    tenant = relationship("Tenant", backref="restaurant", foreign_keys=[tenant_id])

    def __repr__(self):
        return f"<Restaurant id={self.id} name={self.name} tenant_id={self.tenant_id}>"
