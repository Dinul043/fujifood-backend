"""
Order models — Order (header) + OrderItem (line items).

Structure:
  Order
    └── OrderItem (one per menu item ordered)

Each order belongs to one tenant and one customer.
"""
import enum
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import TenantBaseModel


class OrderStatus(str, enum.Enum):
    PENDING    = "pending"     # Order placed, awaiting restaurant confirmation
    CONFIRMED  = "confirmed"   # Restaurant accepted the order
    PREPARING  = "preparing"   # Kitchen is preparing
    READY      = "ready"       # Ready for pickup / out for delivery
    DELIVERED  = "delivered"   # Successfully delivered
    CANCELLED  = "cancelled"   # Cancelled (customer or restaurant)
    REJECTED   = "rejected"    # Restaurant rejected


class PaymentMethod(str, enum.Enum):
    ONLINE = "online"   # Razorpay, UPI, card
    COD    = "cod"      # Cash on delivery


class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    PAID      = "paid"
    FAILED    = "failed"
    REFUNDED  = "refunded"


class Order(TenantBaseModel):
    """
    Order header — one record per customer order.
    """
    __tablename__ = "orders"

    tenant_id       = Column(Integer, ForeignKey("tenants.id"),    nullable=False, index=True)
    restaurant_id   = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    customer_id     = Column(Integer, ForeignKey("users.id"),   nullable=False, index=True)

    # Human-readable order number shown to customer and restaurant
    order_number    = Column(String(50), nullable=False, unique=True, index=True)
    # Example: ORD-2026-000001

    # Status
    status          = Column(
                        String(20),
                        nullable=False,
                        default=OrderStatus.PENDING,
                        index=True
                      )

    # Amounts
    subtotal        = Column(Float, nullable=False)           # Sum of item prices
    delivery_fee    = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    tax_amount      = Column(Float, default=0.0, nullable=False)
    total_amount    = Column(Float, nullable=False)           # Final amount charged

    # Payment
    payment_method  = Column(String(20), nullable=False, default=PaymentMethod.COD)
    payment_status  = Column(String(20), nullable=False, default=PaymentStatus.PENDING)
    payment_ref     = Column(String(200), nullable=True)  # Razorpay order/payment ID

    # Delivery address (snapshot at time of order — customer may change address later)
    delivery_address = Column(JSON, nullable=False)
    # Structure: {line1, line2, city, state, pincode, latitude, longitude}

    # Timing
    estimated_delivery_time = Column(Integer, nullable=True)  # minutes
    accepted_at   = Column(String(50), nullable=True)
    prepared_at   = Column(String(50), nullable=True)
    delivered_at  = Column(String(50), nullable=True)

    # Notes
    customer_notes    = Column(Text, nullable=True)   # Customer's special instructions
    restaurant_notes  = Column(Text, nullable=True)   # Restaurant's internal notes

    # Relationships
    items    = relationship("OrderItem", back_populates="order", lazy="select")
    customer = relationship("User",  backref="orders", foreign_keys=[customer_id])

    def __repr__(self):
        return f"<Order id={self.id} number={self.order_number} status={self.status}>"


class OrderItem(TenantBaseModel):
    """
    Line item — one record per menu item in the order.
    Stores a price snapshot so historical orders are not affected by price changes.
    """
    __tablename__ = "order_items"

    tenant_id       = Column(Integer, ForeignKey("tenants.id"),  nullable=False, index=True)
    order_id        = Column(Integer, ForeignKey("orders.id"),   nullable=False, index=True)
    menu_item_id    = Column(Integer, ForeignKey("menu_items.id"), nullable=False)

    # Snapshot — DO NOT use live menu_item price, use these stored values
    item_name       = Column(String(300), nullable=False)
    item_price      = Column(Float, nullable=False)   # Price at time of order
    quantity        = Column(Integer, nullable=False, default=1)
    line_total      = Column(Float, nullable=False)   # item_price × quantity

    # Customisation notes (e.g. "no onions")
    notes           = Column(Text, nullable=True)

    # Relationships
    order     = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", backref="order_items", foreign_keys=[menu_item_id])

    def __repr__(self):
        return f"<OrderItem id={self.id} name={self.item_name} qty={self.quantity}>"
