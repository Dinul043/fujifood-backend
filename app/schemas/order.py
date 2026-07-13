"""
Order Schemas — Request and Response DTOs for the ordering flow.

Covers:
  - Customer: Place order, view orders, cancel order
  - Restaurant Admin: View orders, update status
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════
#  Place Order (Customer)
# ═══════════════════════════════════════════════════

class OrderItemRequest(BaseModel):
    """Single item in an order."""
    menu_item_id: int
    quantity: int = Field(..., ge=1, le=50)
    notes: Optional[str] = Field(None, max_length=500)


class DeliveryAddress(BaseModel):
    """Delivery address for an order."""
    line1: str = Field(..., min_length=5, max_length=300)
    line2: Optional[str] = Field(None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=5, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PlaceOrderRequest(BaseModel):
    """Customer places an order."""
    items: List[OrderItemRequest] = Field(..., min_length=1)
    delivery_address: DeliveryAddress
    payment_method: str = Field(default="cod")
    customer_notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        valid = {"online", "cod"}
        if v not in valid:
            raise ValueError(f"payment_method must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Update Order Status (Restaurant Admin)
# ═══════════════════════════════════════════════════

class UpdateOrderStatusRequest(BaseModel):
    """Restaurant admin updates order status."""
    status: str
    restaurant_notes: Optional[str] = Field(None, max_length=1000)
    estimated_delivery_time: Optional[int] = Field(None, ge=5, le=180)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"confirmed", "preparing", "ready", "delivered", "cancelled", "rejected"}
        if v not in valid:
            raise ValueError(f"status must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Response DTOs
# ═══════════════════════════════════════════════════

class OrderItemResponse(BaseModel):
    """Order line item response."""
    id: int
    menu_item_id: int
    item_name: str
    item_price: float
    quantity: int
    line_total: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Full order response."""
    id: int
    uuid: str
    order_number: str
    status: str
    subtotal: float
    delivery_fee: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    delivery_address: Dict[str, Any]
    estimated_delivery_time: Optional[int] = None
    customer_notes: Optional[str] = None
    restaurant_notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: str
    accepted_at: Optional[str] = None
    delivered_at: Optional[str] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Paginated list of orders."""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
