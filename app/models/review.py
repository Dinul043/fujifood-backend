"""
Review model — Customer reviews for delivered orders.

One review per order. Only allowed after delivery.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from app.models.base import TenantBaseModel


class Review(TenantBaseModel):
    """Customer review for a delivered order."""
    __tablename__ = "reviews"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    order_id     = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    customer_id  = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    rating       = Column(Integer, nullable=False)  # 1-5 stars
    comment      = Column(Text, nullable=True)
    customer_name = Column(String(200), nullable=True)

    def __repr__(self):
        return f"<Review id={self.id} order_id={self.order_id} rating={self.rating}>"
