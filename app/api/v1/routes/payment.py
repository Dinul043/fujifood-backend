"""
Payment Routes — Razorpay integration.

Endpoints:
  POST /payment/create-order    → Create Razorpay order (before opening modal)
  POST /payment/verify          → Verify payment after success
  POST /payment/refund/{id}     → Refund a paid order (admin)
  GET  /payment/status/{id}     → Get payment status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter()


class CreateOrderRequest(BaseModel):
    order_id: int


class VerifyPaymentRequest(BaseModel):
    order_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order", summary="Create Razorpay order for payment")
async def create_razorpay_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    result, error = service.create_razorpay_order(request.order_id, current_user.tenant_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@router.post("/verify", summary="Verify Razorpay payment signature")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    result, error = service.verify_payment(
        order_id=request.order_id,
        tenant_id=current_user.tenant_id,
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@router.post("/refund/{order_id}", summary="Refund a paid online order")
async def refund_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    success, error = service.refund_payment(order_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Refund processed"}
