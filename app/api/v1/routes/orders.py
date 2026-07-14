"""
Order Routes — Customer ordering and restaurant order management.

Customer endpoints:
  POST   /orders/place                → Place a new order
  GET    /orders/my-orders            → List customer's orders
  GET    /orders/my-orders/{id}       → Get order details
  POST   /orders/my-orders/{id}/cancel → Cancel pending order

Restaurant Admin endpoints:
  GET    /orders/manage               → List all orders (with filters)
  GET    /orders/manage/{id}          → Get order details
  PATCH  /orders/manage/{id}/status   → Update order status
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.order import (
    PlaceOrderRequest,
    UpdateOrderStatusRequest,
    OrderResponse,
    OrderItemResponse,
    OrderListResponse,
)
from app.schemas.auth import ErrorResponse
from app.services.order_service import OrderService

router = APIRouter()


def _build_order_response(order) -> OrderResponse:
    """Helper to build OrderResponse from an Order model."""
    return OrderResponse(
        id=order.id,
        uuid=order.uuid,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        discount_amount=order.discount_amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        delivery_address=order.delivery_address,
        estimated_delivery_time=order.estimated_delivery_time,
        customer_notes=order.customer_notes,
        restaurant_notes=order.restaurant_notes,
        items=[
            OrderItemResponse(
                id=i.id,
                menu_item_id=i.menu_item_id,
                item_name=i.item_name,
                item_price=i.item_price,
                quantity=i.quantity,
                line_total=i.line_total,
                notes=i.notes,
            )
            for i in order.items
        ],
        created_at=str(order.created_at),
        accepted_at=order.accepted_at,
        delivered_at=order.delivered_at,
    )


# ═══════════════════════════════════════════════════
#  CUSTOMER — Place Order
# ═══════════════════════════════════════════════════

@router.post(
    "/place",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    summary="Place a new order",
    description="Customer places an order with items and delivery address.",
)
async def place_order(
    request: PlaceOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db, current_user.tenant_id)
    order, error = service.place_order(current_user.id, request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return _build_order_response(order)


# ═══════════════════════════════════════════════════
#  CUSTOMER — My Orders
# ═══════════════════════════════════════════════════

@router.get(
    "/my-orders",
    response_model=OrderListResponse,
    summary="List my orders",
    description="Returns the authenticated customer's order history.",
)
async def list_my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db, current_user.tenant_id)
    orders, total = service.list_customer_orders(
        current_user.id, page, page_size
    )
    return OrderListResponse(
        orders=[_build_order_response(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/my-orders/{order_id}/cancel",
    response_model=OrderResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Cancel my order",
    description="Cancel a pending order. Only works if order is still pending.",
)
async def cancel_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db, current_user.tenant_id)
    order, error = service.cancel_order(order_id, current_user.id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return _build_order_response(order)


# ═══════════════════════════════════════════════════
#  ADMIN — Order Management
# ═══════════════════════════════════════════════════

@router.get(
    "/manage",
    response_model=OrderListResponse,
    summary="List all restaurant orders",
    description="Restaurant admin views all orders with optional status filter.",
)
async def list_restaurant_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = OrderService(db, current_user.tenant_id)
    orders, total = service.list_restaurant_orders(
        page, page_size, status_filter
    )
    return OrderListResponse(
        orders=[_build_order_response(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/manage/{order_id}/status",
    response_model=OrderResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Update order status",
    description=(
        "Transition order status. Valid transitions: "
        "pending→confirmed/rejected, confirmed→preparing/cancelled, "
        "preparing→ready/cancelled, ready→delivered"
    ),
)
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = OrderService(db, current_user.tenant_id)
    order, error = service.update_order_status(order_id, request)
    if error:
        status_code = 404 if "not found" in error else 400
        raise HTTPException(status_code=status_code, detail=error)
    return _build_order_response(order)
