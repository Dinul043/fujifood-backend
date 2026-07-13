"""
Restaurant Routes — Restaurant profile management.

Two access patterns:
  1. Public (storefront):  GET /restaurants/storefront/{slug}
  2. Admin (restaurant):   GET/PATCH /restaurants/manage

Endpoints:
  GET    /restaurants/storefront/{slug}    → Public restaurant info
  GET    /restaurants/manage               → Admin get own restaurant
  PATCH  /restaurants/manage               → Admin update restaurant
  POST   /restaurants/manage/go-online     → Start accepting orders
  POST   /restaurants/manage/go-offline    → Stop accepting orders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import require_role
from app.models.user import User
from app.schemas.restaurant import (
    UpdateRestaurantRequest,
    RestaurantResponse,
    RestaurantPublicResponse,
)
from app.schemas.auth import ErrorResponse
from app.services.restaurant_service import RestaurantService

router = APIRouter()


# ─── Public: Storefront ────────────────────────────────────────────

@router.get(
    "/storefront/{slug}",
    response_model=RestaurantPublicResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get public restaurant info",
    description="Returns public restaurant details for the storefront.",
)
async def get_public_restaurant(slug: str, db: Session = Depends(get_db)):
    service = RestaurantService(db)
    restaurant = service.get_public_by_slug(slug)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantPublicResponse.model_validate(restaurant)


# ─── Admin: Get Own Restaurant ─────────────────────────────────────

@router.get(
    "/manage",
    response_model=RestaurantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get own restaurant profile",
    description="Returns the full restaurant profile for the authenticated admin.",
)
async def get_own_restaurant(
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = RestaurantService(db)
    restaurant = service.get_by_tenant_id(current_user.tenant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantResponse.model_validate(restaurant)


# ─── Admin: Update Restaurant ──────────────────────────────────────

@router.patch(
    "/manage",
    response_model=RestaurantResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Update restaurant profile",
    description="Partial update — only provided fields are changed.",
)
async def update_restaurant(
    request: UpdateRestaurantRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = RestaurantService(db)
    restaurant, error = service.update_restaurant(
        current_user.tenant_id, request
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return RestaurantResponse.model_validate(restaurant)


# ─── Admin: Go Online / Offline ────────────────────────────────────

@router.post(
    "/manage/go-online",
    response_model=RestaurantResponse,
    summary="Start accepting orders",
    description="Sets the restaurant to online — customers can place orders.",
)
async def go_online(
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = RestaurantService(db)
    restaurant, error = service.set_online_status(current_user.tenant_id, True)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return RestaurantResponse.model_validate(restaurant)


@router.post(
    "/manage/go-offline",
    response_model=RestaurantResponse,
    summary="Stop accepting orders",
    description="Sets the restaurant to offline — ordering is disabled.",
)
async def go_offline(
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = RestaurantService(db)
    restaurant, error = service.set_online_status(current_user.tenant_id, False)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return RestaurantResponse.model_validate(restaurant)
