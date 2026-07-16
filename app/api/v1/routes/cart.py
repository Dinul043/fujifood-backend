"""
Cart Routes — Database-backed cart for customers.

Endpoints:
  GET    /cart/              → Get cart items with menu details
  POST   /cart/add          → Add item to cart (or increment qty)
  PATCH  /cart/update       → Update item quantity
  DELETE /cart/remove/{id}  → Remove item from cart
  DELETE /cart/clear        → Clear entire cart
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.cart import CartItem
from app.models.menu import MenuItem

router = APIRouter()


class AddToCartRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1)


class UpdateCartRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., ge=0)  # 0 = remove


class CartItemResponse(BaseModel):
    id: int
    menu_item_id: int
    name: str
    price: float
    image_url: str | None
    quantity: int


# ─── Get Cart ─────────────────────────────────────────────────────

@router.get("/", response_model=list[CartItemResponse], summary="Get cart")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(CartItem, MenuItem)
        .join(MenuItem, CartItem.menu_item_id == MenuItem.id)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.tenant_id == current_user.tenant_id,
            CartItem.deleted_at.is_(None),
        )
        .all()
    )
    return [
        CartItemResponse(
            id=ci.id,
            menu_item_id=ci.menu_item_id,
            name=mi.name,
            price=mi.price,
            image_url=mi.image_url,
            quantity=ci.quantity,
        )
        for ci, mi in items
    ]


# ─── Add to Cart ─────────────────────────────────────────────────

@router.post("/add", response_model=CartItemResponse, summary="Add item to cart")
async def add_to_cart(
    request: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify menu item exists
    menu_item = db.query(MenuItem).filter(MenuItem.id == request.menu_item_id, MenuItem.deleted_at.is_(None)).first()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Check if already in cart
    existing = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.tenant_id == current_user.tenant_id,
            CartItem.menu_item_id == request.menu_item_id,
            CartItem.deleted_at.is_(None),
        )
        .first()
    )

    if existing:
        existing.quantity += request.quantity
        db.commit()
        db.refresh(existing)
        cart_item = existing
    else:
        cart_item = CartItem(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            menu_item_id=request.menu_item_id,
            quantity=request.quantity,
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        menu_item_id=cart_item.menu_item_id,
        name=menu_item.name,
        price=menu_item.price,
        image_url=menu_item.image_url,
        quantity=cart_item.quantity,
    )


# ─── Update Quantity ──────────────────────────────────────────────

@router.patch("/update", summary="Update item quantity")
async def update_cart_item(
    request: UpdateCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.tenant_id == current_user.tenant_id,
            CartItem.menu_item_id == request.menu_item_id,
            CartItem.deleted_at.is_(None),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    if request.quantity == 0:
        db.delete(item)
        db.commit()
        return {"success": True, "message": "Item removed"}

    item.quantity = request.quantity
    db.commit()
    return {"success": True, "quantity": request.quantity}


# ─── Remove Item ──────────────────────────────────────────────────

@router.delete("/remove/{menu_item_id}", summary="Remove item from cart")
async def remove_from_cart(
    menu_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.tenant_id == current_user.tenant_id,
            CartItem.menu_item_id == menu_item_id,
            CartItem.deleted_at.is_(None),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    db.delete(item)
    db.commit()
    return {"success": True}


# ─── Clear Cart ───────────────────────────────────────────────────

@router.delete("/clear", summary="Clear entire cart")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.tenant_id == current_user.tenant_id,
        CartItem.deleted_at.is_(None),
    ).delete()
    db.commit()
    return {"success": True}
