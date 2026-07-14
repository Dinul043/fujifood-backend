"""
Payment Service — Razorpay integration for online payments.

Handles:
  - Create Razorpay order (before checkout)
  - Verify payment signature (after customer pays)
  - Process refund (on cancellation)
  - Payment status tracking

All amounts in INR. Razorpay expects paise (multiply by 100).
"""
import razorpay
import hmac
import hashlib
from typing import Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order, OrderStatus
from app.models.base import now_ist


# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    # ─── Create Razorpay Order ─────────────────────────────────────

    def create_razorpay_order(self, order_id: int, tenant_id: int) -> Tuple[Optional[dict], Optional[str]]:
        """
        Create a Razorpay order for an existing order.
        Returns razorpay_order_id + key for frontend to open checkout modal.
        """
        order = (
            self.db.query(Order)
            .filter(Order.id == order_id, Order.tenant_id == tenant_id, Order.deleted_at.is_(None))
            .first()
        )
        if not order:
            return None, "Order not found"

        if order.payment_method != "online":
            return None, "This order uses COD, not online payment"

        if order.payment_status == "paid":
            return None, "Order is already paid"

        # Create Razorpay order
        amount_paise = int(order.total_amount * 100)
        try:
            rz_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"order_{order.id}",
                "payment_capture": 1,  # Auto-capture
            })
        except Exception as e:
            return None, f"Razorpay error: {str(e)}"

        # Save razorpay_order_id to our order
        order.payment_ref = rz_order["id"]
        self.db.commit()

        return {
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": rz_order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "order_id": order.id,
            "order_number": order.order_number,
        }, None

    # ─── Verify Payment ────────────────────────────────────────────

    def verify_payment(
        self,
        order_id: int,
        tenant_id: int,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Verify Razorpay payment signature and mark order as paid.
        Called by frontend after successful payment in Razorpay modal.
        """
        order = (
            self.db.query(Order)
            .filter(Order.id == order_id, Order.tenant_id == tenant_id, Order.deleted_at.is_(None))
            .first()
        )
        if not order:
            return None, "Order not found"

        # Verify signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, razorpay_signature):
            return None, "Invalid payment signature"

        # Mark as paid
        order.payment_status = "paid"
        order.payment_ref = razorpay_payment_id
        order.status = OrderStatus.CONFIRMED
        order.accepted_at = now_ist().isoformat()
        self.db.commit()

        return {
            "success": True,
            "order_id": order.id,
            "order_number": order.order_number,
            "payment_status": "paid",
            "order_status": "confirmed",
        }, None

    # ─── Refund Payment ────────────────────────────────────────────

    def refund_payment(self, order_id: int, tenant_id: int) -> Tuple[bool, Optional[str]]:
        """
        Refund a paid online order (called on cancellation).
        Full refund — amount goes back to customer.
        """
        order = (
            self.db.query(Order)
            .filter(Order.id == order_id, Order.tenant_id == tenant_id, Order.deleted_at.is_(None))
            .first()
        )
        if not order:
            return False, "Order not found"

        if order.payment_method != "online":
            return True, None  # COD — no refund needed

        if order.payment_status != "paid":
            return True, None  # Not paid — no refund needed

        if not order.payment_ref:
            return False, "No payment reference found"

        # Process refund via Razorpay
        try:
            client.payment.refund(order.payment_ref, {
                "amount": int(order.total_amount * 100),
            })
        except Exception as e:
            return False, f"Refund failed: {str(e)}"

        # Mark as refunded
        order.payment_status = "refunded"
        self.db.commit()

        return True, None
