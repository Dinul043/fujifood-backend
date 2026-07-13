"""
User Address model — saved delivery addresses for customers.

Each customer can save multiple addresses (Home, Work, Other).
One address per customer can be marked as default.
Scoped to tenant (customer's addresses are per-restaurant).
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, Index
from app.models.base import TenantBaseModel


class UserAddress(TenantBaseModel):
    """
    Saved delivery addresses for a customer.
    """
    __tablename__ = "user_addresses"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Address details
    label        = Column(String(50), nullable=False, default="Home")  # Home, Work, Other
    address_line1 = Column(String(300), nullable=False)
    address_line2 = Column(String(300), nullable=True)
    city         = Column(String(100), nullable=False)
    state        = Column(String(100), nullable=False)
    pincode      = Column(String(10), nullable=False)
    landmark     = Column(String(200), nullable=True)

    # Coordinates (for delivery radius check)
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)

    # Flags
    is_default   = Column(Boolean, default=False, nullable=False)

    # Composite index: one default address per user per tenant
    __table_args__ = (
        Index("idx_user_addresses_user", "tenant_id", "user_id"),
    )

    def __repr__(self):
        return f"<UserAddress id={self.id} label={self.label} user_id={self.user_id}>"
