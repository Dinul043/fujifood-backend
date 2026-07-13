"""
Menu Routes — Menu management and public browsing.

Admin endpoints (restaurant_admin):
  Categories:
    GET    /menu/manage/categories           → List categories
    POST   /menu/manage/categories           → Create category
    PATCH  /menu/manage/categories/{id}      → Update category
    DELETE /menu/manage/categories/{id}      → Delete category

  Items:
    GET    /menu/manage/items                → List items
    POST   /menu/manage/items                → Create item
    PATCH  /menu/manage/items/{id}           → Update item
    DELETE /menu/manage/items/{id}           → Delete item
    POST   /menu/manage/items/{id}/toggle    → Toggle availability

Public endpoints (storefront):
    GET    /menu/storefront/{slug}           → Full menu for customers
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import require_role
from app.models.user import User
from app.schemas.menu import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CategoryResponse,
    CreateMenuItemRequest,
    UpdateMenuItemRequest,
    MenuItemResponse,
    FullMenuResponse,
    CategoryWithItemsResponse,
)
from app.schemas.auth import ErrorResponse
from app.services.menu_service import MenuService, PublicMenuService

router = APIRouter()


# ═══════════════════════════════════════════════════
#  PUBLIC — Storefront Menu
# ═══════════════════════════════════════════════════

@router.get(
    "/storefront/{slug}",
    response_model=FullMenuResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get full restaurant menu (public)",
    description="Returns the complete menu with categories and available items.",
)
async def get_public_menu(slug: str, db: Session = Depends(get_db)):
    service = PublicMenuService(db)
    result = service.get_full_menu(slug)

    if not result:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return FullMenuResponse(
        restaurant_name=result["restaurant_name"],
        categories=[
            CategoryWithItemsResponse(
                id=c["category"].id,
                uuid=c["category"].uuid,
                name=c["category"].name,
                description=c["category"].description,
                image_url=c["category"].image_url,
                sort_order=c["category"].sort_order,
                items=[MenuItemResponse.model_validate(i) for i in c["items"]],
            )
            for c in result["categories"]
        ],
        total_items=result["total_items"],
    )


# ═══════════════════════════════════════════════════
#  ADMIN — Categories
# ═══════════════════════════════════════════════════

@router.get(
    "/manage/categories",
    response_model=list[CategoryResponse],
    summary="List menu categories",
)
async def list_categories(
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    categories = service.list_categories(include_inactive=include_inactive)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post(
    "/manage/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create menu category",
)
async def create_category(
    request: CreateCategoryRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    category, error = service.create_category(request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return CategoryResponse.model_validate(category)


@router.patch(
    "/manage/categories/{category_id}",
    response_model=CategoryResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update menu category",
)
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    category, error = service.update_category(category_id, request)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/manage/categories/{category_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}},
    summary="Delete menu category",
    description="Soft deletes the category and all items within it.",
)
async def delete_category(
    category_id: int,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    success, error = service.delete_category(category_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"success": True, "message": "Category deleted"}


# ═══════════════════════════════════════════════════
#  ADMIN — Menu Items
# ═══════════════════════════════════════════════════

@router.get(
    "/manage/items",
    response_model=list[MenuItemResponse],
    summary="List menu items",
)
async def list_items(
    category_id: Optional[int] = Query(default=None),
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    items = service.list_items(category_id=category_id)
    return [MenuItemResponse.model_validate(i) for i in items]


@router.post(
    "/manage/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create menu item",
)
async def create_item(
    request: CreateMenuItemRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    item, error = service.create_item(request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return MenuItemResponse.model_validate(item)


@router.patch(
    "/manage/items/{item_id}",
    response_model=MenuItemResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update menu item",
)
async def update_item(
    item_id: int,
    request: UpdateMenuItemRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    item, error = service.update_item(item_id, request)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return MenuItemResponse.model_validate(item)


@router.delete(
    "/manage/items/{item_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}},
    summary="Delete menu item",
)
async def delete_item(
    item_id: int,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    success, error = service.delete_item(item_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"success": True, "message": "Item deleted"}


@router.post(
    "/manage/items/{item_id}/toggle",
    response_model=MenuItemResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Toggle item availability",
    description="Quick toggle — mark item as available or sold out.",
)
async def toggle_item_availability(
    item_id: int,
    is_available: bool = Query(...),
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = MenuService(db, current_user.tenant_id)
    item, error = service.toggle_availability(item_id, is_available)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return MenuItemResponse.model_validate(item)
