"""
Cart model — Database-backed shopping cart per user.

Each user has cart items that persist across sessions/devices.
Cart is cleared after successful order placement.
"""
from sqlalchemy import Column, Integer, ForeignKey, Index
from app.models.base import TenantBaseModel


class CartItem(TenantBaseModel):
    """One item in a customer's cart."""
    __tablename__ = "cart_items"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity     = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("idx_cart_user_item", "tenant_id", "user_id", "menu_item_id", unique=True),
    )

    def __repr__(self):
        return f"<CartItem user_id={self.user_id} menu_item_id={self.menu_item_id} qty={self.quantity}>"
