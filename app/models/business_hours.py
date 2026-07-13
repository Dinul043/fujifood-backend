"""
Business Hours model — restaurant operating hours per day of week.

Each restaurant has 7 records (one per day).
Supports multiple time slots per day (e.g., lunch + dinner).
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from app.models.base import TenantBaseModel


class BusinessHours(TenantBaseModel):
    """
    Operating hours for each day of the week.
    """
    __tablename__ = "business_hours"

    tenant_id      = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    restaurant_id  = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)

    day_of_week    = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    is_open        = Column(Boolean, default=True, nullable=False)

    # Time slots (24h format, e.g., "10:00", "22:00")
    open_time      = Column(String(5), nullable=True)   # "10:00"
    close_time     = Column(String(5), nullable=True)   # "22:00"

    # Optional second slot (e.g., closed 3-5pm)
    open_time_2    = Column(String(5), nullable=True)
    close_time_2   = Column(String(5), nullable=True)

    __table_args__ = (
        Index("idx_business_hours_restaurant_day", "restaurant_id", "day_of_week", unique=True),
    )

    def __repr__(self):
        return f"<BusinessHours day={self.day_of_week} open={self.is_open}>"
