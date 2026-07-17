"""
Review Routes — Customer reviews and admin management.

Customer:
  POST   /reviews/              → Submit review for a delivered order
  GET    /reviews/my-reviews    → List my reviews

Public:
  GET    /reviews/storefront/{slug} → Public reviews for the restaurant

Admin:
  GET    /reviews/manage        → List all reviews
  DELETE /reviews/manage/{id}   → Delete a review
"""
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user, require_role
from app.models.user import User
from app.models.order import Order
from app.models.review import Review
from app.models.tenant import Tenant

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────

class CreateReviewRequest(BaseModel):
    order_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    item_ratings: Optional[list[Any]] = None  # [{menu_item_id: int, rating: int}]


class ReviewResponse(BaseModel):
    id: int
    order_id: int
    rating: int
    comment: Optional[str]
    customer_name: Optional[str]
    created_at: Optional[str]
    order_items: Optional[str] = None  # Comma-separated item names

    class Config:
        from_attributes = True


# ─── Customer: Submit Review ──────────────────────────────────────

@router.post("/", response_model=ReviewResponse, status_code=201, summary="Submit review")
async def create_review(
    request: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify order exists, belongs to customer, and is delivered
    order = (
        db.query(Order)
        .filter(
            Order.id == request.order_id,
            Order.customer_id == current_user.id,
            Order.tenant_id == current_user.tenant_id,
            Order.deleted_at.is_(None),
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Can only review delivered orders")

    # Check if already reviewed
    existing = db.query(Review).filter(Review.order_id == request.order_id, Review.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this order")

    review = Review(
        tenant_id=current_user.tenant_id,
        order_id=request.order_id,
        customer_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
        customer_name=current_user.name,
    )
    db.add(review)

    # Update per-item ratings if provided
    from app.models.menu import MenuItem
    if request.item_ratings:
        for ir in request.item_ratings:
            item_id = ir.get('menu_item_id') if isinstance(ir, dict) else None
            item_rating = ir.get('rating') if isinstance(ir, dict) else None
            if item_id and item_rating and 1 <= item_rating <= 5:
                menu_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
                if menu_item:
                    # Running average: new_avg = (old_avg * count + new_rating) / (count + 1)
                    total = menu_item.avg_rating * menu_item.rating_count + item_rating
                    menu_item.rating_count += 1
                    menu_item.avg_rating = round(total / menu_item.rating_count, 1)
    else:
        # If no per-item ratings, apply overall rating to all items in the order
        from app.models.order import OrderItem as OI
        order_items = db.query(OI).filter(OI.order_id == request.order_id).all()
        for oi in order_items:
            menu_item = db.query(MenuItem).filter(MenuItem.id == oi.menu_item_id).first()
            if menu_item:
                total = menu_item.avg_rating * menu_item.rating_count + request.rating
                menu_item.rating_count += 1
                menu_item.avg_rating = round(total / menu_item.rating_count, 1)

    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        order_id=review.order_id,
        rating=review.rating,
        comment=review.comment,
        customer_name=review.customer_name,
        created_at=str(review.created_at),
    )


# ─── Customer: My Reviews ────────────────────────────────────────

@router.get("/my-reviews", response_model=list[ReviewResponse], summary="My reviews")
async def my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .filter(
            Review.customer_id == current_user.id,
            Review.tenant_id == current_user.tenant_id,
            Review.deleted_at.is_(None),
        )
        .order_by(Review.created_at.desc())
        .all()
    )
    return [
        ReviewResponse(
            id=r.id, order_id=r.order_id, rating=r.rating,
            comment=r.comment, customer_name=r.customer_name,
            created_at=str(r.created_at),
        )
        for r in reviews
    ]


# ─── Public: Storefront Reviews ──────────────────────────────────

@router.get("/storefront/{slug}", response_model=list[ReviewResponse], summary="Public reviews")
async def public_reviews(slug: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.slug == slug, Tenant.deleted_at.is_(None)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    reviews = (
        db.query(Review)
        .filter(
            Review.tenant_id == tenant.id,
            Review.deleted_at.is_(None),
        )
        .order_by(Review.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        ReviewResponse(
            id=r.id, order_id=r.order_id, rating=r.rating,
            comment=r.comment, customer_name=r.customer_name,
            created_at=str(r.created_at),
        )
        for r in reviews
    ]


# ─── Admin: List Reviews ─────────────────────────────────────────

@router.get("/manage", response_model=list[ReviewResponse], summary="Admin: list reviews")
async def admin_list_reviews(
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    from app.models.order import OrderItem as OI

    reviews = (
        db.query(Review)
        .filter(
            Review.tenant_id == current_user.tenant_id,
            Review.deleted_at.is_(None),
        )
        .order_by(Review.created_at.desc())
        .all()
    )

    result = []
    for r in reviews:
        # Get order items for this review
        items = db.query(OI).filter(OI.order_id == r.order_id).all()
        item_names = ", ".join([i.item_name for i in items]) if items else None
        result.append(ReviewResponse(
            id=r.id, order_id=r.order_id, rating=r.rating,
            comment=r.comment, customer_name=r.customer_name,
            created_at=str(r.created_at),
            order_items=item_names,
        ))
    return result


# ─── Admin: Delete Review ────────────────────────────────────────

@router.delete("/manage/{review_id}", summary="Admin: delete review")
async def admin_delete_review(
    review_id: int,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    review = (
        db.query(Review)
        .filter(
            Review.id == review_id,
            Review.tenant_id == current_user.tenant_id,
            Review.deleted_at.is_(None),
        )
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.deleted_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "Review deleted"}
