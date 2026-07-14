"""
Order Service — Business logic for the ordering flow.

Handles:
  - Customer: Place order, list own orders, cancel order
  - Restaurant Admin: List orders, update status, reject

Order Number Format: ORD-{YYYYMMDD}-{sequence}
Example: ORD-20260713-000042
"""
from typing import Optional, Tuple, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order, OrderItem, OrderStatus
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.schemas.order import PlaceOrderRequest, UpdateOrderStatusRequest


class OrderService:
    """Order management business logic."""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    # ─── Generate Order Number ─────────────────────────────────────

    def _generate_order_number(self) -> str:
        """Generate sequential order number: ORD-YYYYMMDD-XXXXXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"ORD-{today}-"

        # Find the last order number for today
        last_order = (
            self.db.query(Order)
            .filter(
                Order.tenant_id == self.tenant_id,
                Order.order_number.like(f"{prefix}%"),
            )
            .order_by(Order.id.desc())
            .first()
        )

        if last_order:
            last_seq = int(last_order.order_number.split("-")[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:06d}"

    # ─── Place Order (Customer) ────────────────────────────────────

    def place_order(
        self, customer_id: int, request: PlaceOrderRequest
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Customer places a new order.

        Steps:
          1. Validate all items exist and are available
          2. Calculate totals using current prices
          3. Create Order + OrderItems
          4. Return created order
        """
        restaurant = (
            self.db.query(Restaurant)
            .filter(
                Restaurant.tenant_id == self.tenant_id,
                Restaurant.deleted_at.is_(None),
            )
            .first()
        )
        if not restaurant:
            return None, "Restaurant not found"

        if not restaurant.is_online:
            return None, "Restaurant is currently not accepting orders"

        # Validate items and calculate totals
        subtotal = 0.0
        order_items_data = []

        for item_req in request.items:
            menu_item = (
                self.db.query(MenuItem)
                .filter(
                    MenuItem.id == item_req.menu_item_id,
                    MenuItem.tenant_id == self.tenant_id,
                    MenuItem.is_available == True,
                    MenuItem.deleted_at.is_(None),
                )
                .first()
            )
            if not menu_item:
                return None, f"Menu item ID {item_req.menu_item_id} not found or unavailable"

            # Use discount price if available
            effective_price = menu_item.discount_price or menu_item.price
            line_total = effective_price * item_req.quantity
            subtotal += line_total

            order_items_data.append({
                "menu_item": menu_item,
                "quantity": item_req.quantity,
                "price": effective_price,
                "line_total": line_total,
                "notes": item_req.notes,
            })

        # Check minimum order amount
        if subtotal < restaurant.min_order_amount:
            return None, (
                f"Minimum order amount is {restaurant.min_order_amount}. "
                f"Current total: {subtotal}"
            )

        # Calculate delivery fee
        delivery_fee = restaurant.delivery_fee
        if restaurant.free_delivery_above and subtotal >= restaurant.free_delivery_above:
            delivery_fee = 0.0

        total_amount = subtotal + delivery_fee

        # Create order
        order = Order(
            tenant_id=self.tenant_id,
            restaurant_id=restaurant.id,
            customer_id=customer_id,
            order_number=self._generate_order_number(),
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount_amount=0.0,
            tax_amount=0.0,
            total_amount=total_amount,
            payment_method=request.payment_method,
            payment_status="pending",
            delivery_address=request.delivery_address.model_dump(),
            estimated_delivery_time=restaurant.avg_delivery_time_mins,
            customer_notes=request.customer_notes,
        )
        self.db.add(order)
        self.db.flush()

        # Create order items (price snapshot)
        for item_data in order_items_data:
            order_item = OrderItem(
                tenant_id=self.tenant_id,
                order_id=order.id,
                menu_item_id=item_data["menu_item"].id,
                item_name=item_data["menu_item"].name,
                item_price=item_data["price"],
                quantity=item_data["quantity"],
                line_total=item_data["line_total"],
                notes=item_data["notes"],
            )
            self.db.add(order_item)

        self.db.commit()
        self.db.refresh(order)
        return order, None

    # ─── Customer: List Own Orders ─────────────────────────────────

    def list_customer_orders(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Order], int]:
        """List orders for a specific customer."""
        query = (
            self.db.query(Order)
            .filter(
                Order.tenant_id == self.tenant_id,
                Order.customer_id == customer_id,
                Order.deleted_at.is_(None),
            )
        )
        total = query.count()
        orders = (
            query
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return orders, total

    # ─── Customer: Cancel Order ────────────────────────────────────

    def cancel_order(
        self, order_id: int, customer_id: int
    ) -> Tuple[Optional[Order], Optional[str]]:
        """Customer cancels their own order. Auto-refund if paid online."""
        order = (
            self.db.query(Order)
            .filter(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id,
                Order.customer_id == customer_id,
                Order.deleted_at.is_(None),
            )
            .first()
        )
        if not order:
            return None, "Order not found"

        # Can only cancel pending or confirmed orders
        if order.status not in [OrderStatus.PENDING, "confirmed"]:
            return None, "Only pending or confirmed orders can be cancelled"

        # If paid online, process refund
        if order.payment_method == "online" and order.payment_status == "paid":
            from app.services.payment_service import PaymentService
            payment_svc = PaymentService(self.db)
            success, err = payment_svc.refund_payment(order_id, self.tenant_id)
            if not success:
                return None, f"Cancellation failed: {err}"

        order.status = OrderStatus.CANCELLED
        self.db.commit()
        self.db.refresh(order)
        return order, None

    # ─── Admin: List All Orders ────────────────────────────────────

    def list_restaurant_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """List all orders for the restaurant (admin view)."""
        query = (
            self.db.query(Order)
            .filter(
                Order.tenant_id == self.tenant_id,
                Order.deleted_at.is_(None),
            )
        )
        if status_filter:
            query = query.filter(Order.status == status_filter)

        total = query.count()
        orders = (
            query
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return orders, total

    # ─── Admin: Update Order Status ────────────────────────────────

    def update_order_status(
        self, order_id: int, request: UpdateOrderStatusRequest
    ) -> Tuple[Optional[Order], Optional[str]]:
        """Restaurant admin updates order status."""
        order = (
            self.db.query(Order)
            .filter(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id,
                Order.deleted_at.is_(None),
            )
            .first()
        )
        if not order:
            return None, "Order not found"

        # Validate status transition
        valid_transitions = {
            "pending": ["confirmed", "rejected"],
            "confirmed": ["preparing", "cancelled"],
            "preparing": ["ready", "cancelled"],
            "ready": ["delivered"],
        }

        current = order.status
        allowed = valid_transitions.get(current, [])
        if request.status not in allowed:
            return None, (
                f"Cannot transition from '{current}' to '{request.status}'. "
                f"Allowed: {', '.join(allowed)}"
            )

        now = datetime.utcnow().isoformat()
        order.status = request.status

        if request.status == "confirmed":
            order.accepted_at = now
        elif request.status == "delivered":
            order.delivered_at = now

        if request.restaurant_notes:
            order.restaurant_notes = request.restaurant_notes
        if request.estimated_delivery_time:
            order.estimated_delivery_time = request.estimated_delivery_time

        self.db.commit()
        self.db.refresh(order)
        return order, None
