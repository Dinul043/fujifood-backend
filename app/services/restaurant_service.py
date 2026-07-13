"""
Restaurant Service — Business logic for restaurant profile management.

Handles:
  - Get restaurant by tenant (admin or storefront)
  - Update restaurant profile (admin)
  - Toggle online/published status
  - Get public restaurant info (storefront)
"""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.models.tenant import Tenant, TenantStatus
from app.schemas.restaurant import UpdateRestaurantRequest


class RestaurantService:
    """Restaurant profile management."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Get Restaurant by Tenant ID ──────────────────────────────

    def get_by_tenant_id(self, tenant_id: int) -> Optional[Restaurant]:
        """Get restaurant for a tenant (admin use)."""
        return (
            self.db.query(Restaurant)
            .filter(
                Restaurant.tenant_id == tenant_id,
                Restaurant.deleted_at.is_(None),
            )
            .first()
        )

    # ─── Get Public Restaurant by Slug ────────────────────────────

    def get_public_by_slug(self, slug: str) -> Optional[Restaurant]:
        """
        Get restaurant by tenant slug — public storefront use.
        Only returns if tenant is active and restaurant is published.
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

        restaurant = self.get_by_tenant_id(tenant.id)
        if not restaurant or not restaurant.is_published:
            return None

        return restaurant

    # ─── Update Restaurant ────────────────────────────────────────

    def update_restaurant(
        self, tenant_id: int, request: UpdateRestaurantRequest
    ) -> Tuple[Optional[Restaurant], Optional[str]]:
        """Update restaurant profile — partial update."""
        restaurant = self.get_by_tenant_id(tenant_id)
        if not restaurant:
            return None, "Restaurant not found"

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(restaurant, field, value)

        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant, None

    # ─── Toggle Online Status ─────────────────────────────────────

    def set_online_status(
        self, tenant_id: int, is_online: bool
    ) -> Tuple[Optional[Restaurant], Optional[str]]:
        """Toggle restaurant online/offline (accepting orders or not)."""
        restaurant = self.get_by_tenant_id(tenant_id)
        if not restaurant:
            return None, "Restaurant not found"

        restaurant.is_online = is_online
        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant, None

    # ─── Publish / Unpublish ──────────────────────────────────────

    def set_published_status(
        self, tenant_id: int, is_published: bool
    ) -> Tuple[Optional[Restaurant], Optional[str]]:
        """Publish or unpublish the restaurant storefront."""
        restaurant = self.get_by_tenant_id(tenant_id)
        if not restaurant:
            return None, "Restaurant not found"

        restaurant.is_published = is_published
        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant, None
