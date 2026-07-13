"""
Theme model — per-tenant storefront configuration.

Every restaurant controls their branding without any redeployment.
Changes take effect immediately on the storefront.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import TenantBaseModel


class Theme(TenantBaseModel):
    """
    Storefront theme configuration for a tenant.
    One record per tenant. Read by the storefront at request time.
    """
    __tablename__ = "themes"

    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)

    # Typography
    font_heading    = Column(String(100), default="Plus Jakarta Sans", nullable=False)
    font_body       = Column(String(100), default="Inter",             nullable=False)

    # Colors
    color_primary   = Column(String(20),  default="#E85D8E", nullable=False)  # Brand primary
    color_secondary = Column(String(20),  default="#18181B", nullable=False)  # Dark
    color_accent    = Column(String(20),  default="#F59E0B", nullable=False)  # Accent/gold
    color_bg        = Column(String(20),  default="#FAFAFA", nullable=False)  # Page background
    color_surface   = Column(String(20),  default="#FFFFFF", nullable=False)  # Card background
    color_text      = Column(String(20),  default="#18181B", nullable=False)  # Body text

    # Layout
    hero_layout         = Column(String(50),  default="split",    nullable=False)  # split | full | centered
    header_style        = Column(String(50),  default="glass",    nullable=False)  # glass | solid | minimal
    card_style          = Column(String(50),  default="rounded",  nullable=False)  # rounded | flat | elevated

    # Media
    hero_image_url      = Column(String(500), nullable=True)
    hero_video_url      = Column(String(500), nullable=True)

    # Custom CSS (Enterprise plan only)
    custom_css          = Column(Text, nullable=True)

    # JSON blob for future extensibility (layout blocks, component config)
    advanced_config     = Column(JSON, nullable=True)

    is_published        = Column(Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", backref="theme", foreign_keys=[tenant_id])

    def __repr__(self):
        return f"<Theme tenant_id={self.tenant_id} primary={self.color_primary}>"
