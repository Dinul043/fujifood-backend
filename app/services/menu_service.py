"""
Menu Service — Business logic for menu management.

Handles:
  - Category CRUD (restaurant admin)
  - Menu item CRUD (restaurant admin)
  - Full menu retrieval (storefront — public)

All queries are tenant-scoped via tenant_id.
"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models.menu import MenuCategory, MenuItem
from app.models.restaurant import Restaurant
from app.models.tenant import Tenant, TenantStatus
from app.schemas.menu import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CreateMenuItemRequest,
    UpdateMenuItemRequest,
)


class MenuService:
    """Menu management business logic."""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    # ─── Helpers ───────────────────────────────────────────────────

    def _get_restaurant(self) -> Optional[Restaurant]:
        return (
            self.db.query(Restaurant)
            .filter(
                Restaurant.tenant_id == self.tenant_id,
                Restaurant.deleted_at.is_(None),
            )
            .first()
        )

    # ═══════════════════════════════════════════════════
    #  CATEGORIES
    # ═══════════════════════════════════════════════════

    def list_categories(self, include_inactive: bool = False) -> List[MenuCategory]:
        """List all categories for this tenant."""
        query = (
            self.db.query(MenuCategory)
            .filter(
                MenuCategory.tenant_id == self.tenant_id,
                MenuCategory.deleted_at.is_(None),
            )
        )
        if not include_inactive:
            query = query.filter(MenuCategory.is_active == True)

        return query.order_by(MenuCategory.sort_order.asc()).all()

    def get_category(self, category_id: int) -> Optional[MenuCategory]:
        """Get a single category by ID."""
        return (
            self.db.query(MenuCategory)
            .filter(
                MenuCategory.id == category_id,
                MenuCategory.tenant_id == self.tenant_id,
                MenuCategory.deleted_at.is_(None),
            )
            .first()
        )

    def create_category(
        self, request: CreateCategoryRequest
    ) -> Tuple[Optional[MenuCategory], Optional[str]]:
        """Create a new menu category."""
        restaurant = self._get_restaurant()
        if not restaurant:
            return None, "Restaurant not found"

        category = MenuCategory(
            tenant_id=self.tenant_id,
            restaurant_id=restaurant.id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            sort_order=request.sort_order,
            is_active=request.is_active,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category, None

    def update_category(
        self, category_id: int, request: UpdateCategoryRequest
    ) -> Tuple[Optional[MenuCategory], Optional[str]]:
        """Update an existing menu category."""
        category = self.get_category(category_id)
        if not category:
            return None, "Category not found"

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category, None

    def delete_category(self, category_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a category and all its items."""
        from datetime import datetime

        category = self.get_category(category_id)
        if not category:
            return False, "Category not found"

        now = datetime.utcnow()
        category.deleted_at = now

        # Also soft-delete all items in this category
        items = (
            self.db.query(MenuItem)
            .filter(
                MenuItem.category_id == category_id,
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.deleted_at.is_(None),
            )
            .all()
        )
        for item in items:
            item.deleted_at = now

        self.db.commit()
        return True, None

    # ═══════════════════════════════════════════════════
    #  MENU ITEMS
    # ═══════════════════════════════════════════════════

    def list_items(
        self,
        category_id: Optional[int] = None,
        available_only: bool = False,
    ) -> List[MenuItem]:
        """List menu items, optionally filtered by category."""
        query = (
            self.db.query(MenuItem)
            .filter(
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.deleted_at.is_(None),
            )
        )
        if category_id:
            query = query.filter(MenuItem.category_id == category_id)
        if available_only:
            query = query.filter(MenuItem.is_available == True)

        return query.order_by(MenuItem.sort_order.asc()).all()

    def get_item(self, item_id: int) -> Optional[MenuItem]:
        """Get a single menu item by ID."""
        return (
            self.db.query(MenuItem)
            .filter(
                MenuItem.id == item_id,
                MenuItem.tenant_id == self.tenant_id,
                MenuItem.deleted_at.is_(None),
            )
            .first()
        )

    def create_item(
        self, request: CreateMenuItemRequest
    ) -> Tuple[Optional[MenuItem], Optional[str]]:
        """Create a new menu item."""
        restaurant = self._get_restaurant()
        if not restaurant:
            return None, "Restaurant not found"

        # Verify category exists and belongs to this tenant
        category = self.get_category(request.category_id)
        if not category:
            return None, "Category not found"

        item = MenuItem(
            tenant_id=self.tenant_id,
            restaurant_id=restaurant.id,
            category_id=request.category_id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            price=request.price,
            discount_price=request.discount_price,
            food_type=request.food_type,
            is_bestseller=request.is_bestseller,
            is_recommended=request.is_recommended,
            is_spicy=request.is_spicy,
            is_available=request.is_available,
            sort_order=request.sort_order,
            calories=request.calories,
            allergens=request.allergens,
            tags=request.tags,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item, None

    def update_item(
        self, item_id: int, request: UpdateMenuItemRequest
    ) -> Tuple[Optional[MenuItem], Optional[str]]:
        """Update an existing menu item."""
        item = self.get_item(item_id)
        if not item:
            return None, "Menu item not found"

        # If category_id is being changed, verify new category exists
        if request.category_id is not None:
            category = self.get_category(request.category_id)
            if not category:
                return None, "Target category not found"

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(item, field, value)

        self.db.commit()
        self.db.refresh(item)
        return item, None

    def delete_item(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a menu item."""
        from datetime import datetime

        item = self.get_item(item_id)
        if not item:
            return False, "Menu item not found"

        item.deleted_at = datetime.utcnow()
        self.db.commit()
        return True, None

    def toggle_availability(
        self, item_id: int, is_available: bool
    ) -> Tuple[Optional[MenuItem], Optional[str]]:
        """Quick toggle item availability (e.g. sold out)."""
        item = self.get_item(item_id)
        if not item:
            return None, "Menu item not found"

        item.is_available = is_available
        self.db.commit()
        self.db.refresh(item)
        return item, None


# ═══════════════════════════════════════════════════
#  Public Menu Service (Storefront)
# ═══════════════════════════════════════════════════

class PublicMenuService:
    """Public menu retrieval for storefront — read-only."""

    def __init__(self, db: Session):
        self.db = db

    def get_full_menu(self, slug: str) -> Optional[dict]:
        """
        Get complete menu for a restaurant by slug.
        Returns categories with nested available items.
        """
        tenant = (
            self.db.query(Tenant)
            .filter(
                Tenant.slug == slug,
                Tenant.status == "active",
                Tenant.deleted_at.is_(None),
            )
            .first()
        )
        if not tenant:
            return None

        restaurant = (
            self.db.query(Restaurant)
            .filter(
                Restaurant.tenant_id == tenant.id,
                Restaurant.deleted_at.is_(None),
            )
            .first()
        )
        if not restaurant:
            return None

        categories = (
            self.db.query(MenuCategory)
            .filter(
                MenuCategory.tenant_id == tenant.id,
                MenuCategory.is_active == True,
                MenuCategory.deleted_at.is_(None),
            )
            .order_by(MenuCategory.sort_order.asc())
            .all()
        )

        total_items = 0
        cat_data = []
        for cat in categories:
            items = (
                self.db.query(MenuItem)
                .filter(
                    MenuItem.category_id == cat.id,
                    MenuItem.tenant_id == tenant.id,
                    MenuItem.is_available == True,
                    MenuItem.deleted_at.is_(None),
                )
                .order_by(MenuItem.sort_order.asc())
                .all()
            )
            total_items += len(items)
            cat_data.append({"category": cat, "items": items})

        return {
            "restaurant_name": restaurant.name,
            "categories": cat_data,
            "total_items": total_items,
        }
