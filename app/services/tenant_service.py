"""
Tenant Provisioning Service — Internal operations workflow.

This service handles the complete tenant onboarding lifecycle:
  1. Create Tenant record
  2. Create Restaurant profile
  3. Create default Theme
  4. Create Restaurant Admin user
  5. Activate tenant

All operations are atomic — if any step fails, the entire
provisioning is rolled back.

This is NOT a public-facing service.
Only our internal operations team uses these APIs.
"""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus, TenantPlan
from app.models.restaurant import Restaurant
from app.models.theme import Theme
from app.models.user import User, UserRole, UserStatus
from app.schemas.tenant import (
    ProvisionTenantRequest,
    UpdateTenantRequest,
)


class TenantService:
    """Internal tenant provisioning and management."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Full Provisioning (Atomic) ───────────────────────────────

    def provision_tenant(
        self, request: ProvisionTenantRequest
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Provision a complete tenant setup in one atomic transaction.

        Creates:
          1. Tenant record (status = active)
          2. Restaurant profile
          3. Default theme configuration
          4. Restaurant admin user account

        Returns:
            (result_dict, None) on success
            (None, error_message) on failure
        """
        try:
            # Step 1: Create Tenant
            tenant = Tenant(
                name=request.name,
                slug=request.slug,
                custom_domain=request.custom_domain,
                status="active",
                plan=request.plan,
                owner_name=request.owner_name,
                owner_email=request.owner_email,
                owner_phone=request.owner_phone,
                is_verified=True,
                email_verified=True,
                onboarding_notes=request.onboarding_notes,
            )

            # Set trial period if applicable
            if request.plan == "trial":
                trial_end = datetime.utcnow() + timedelta(days=14)
                tenant.trial_ends_at = trial_end.isoformat()

            self.db.add(tenant)
            self.db.flush()  # Get tenant.id without committing

            # Step 2: Create Restaurant
            restaurant = Restaurant(
                tenant_id=tenant.id,
                name=request.restaurant_name,
                phone=request.restaurant_phone,
                email=request.restaurant_email,
                cuisine_type=request.cuisine_type,
                address_line1=request.address_line1,
                address_line2=request.address_line2,
                city=request.city,
                state=request.state,
                pincode=request.pincode,
                country=request.country,
                is_online=False,
                is_published=False,
            )
            self.db.add(restaurant)
            self.db.flush()

            # Step 3: Create Default Theme
            theme = Theme(
                tenant_id=tenant.id,
                font_heading="Plus Jakarta Sans",
                font_body="Inter",
                color_primary="#E85D8E",
                color_secondary="#18181B",
                color_accent="#F59E0B",
                color_bg="#FAFAFA",
                color_surface="#FFFFFF",
                color_text="#18181B",
                hero_layout="split",
                header_style="glass",
                card_style="rounded",
                is_published=True,
            )
            self.db.add(theme)

            # Step 4: Create Restaurant Admin User
            admin_user = User(
                tenant_id=tenant.id,
                name=request.admin_name,
                phone=request.admin_phone,
                email=request.admin_email,
                password_hash=hash_password(request.admin_password),
                role=UserRole.RESTAURANT_ADMIN,
                status=UserStatus.ACTIVE,
                phone_verified=True,
                is_active=True,
            )
            self.db.add(admin_user)

            # Commit all together — atomic
            self.db.commit()
            self.db.refresh(tenant)
            self.db.refresh(restaurant)
            self.db.refresh(admin_user)

            # Build storefront URL
            if tenant.custom_domain:
                storefront_url = f"https://{tenant.custom_domain}"
            else:
                storefront_url = f"https://{tenant.slug}.fujifood.com"

            return {
                "tenant": tenant,
                "restaurant": restaurant,
                "admin_user": admin_user,
                "storefront_url": storefront_url,
            }, None

        except IntegrityError as e:
            self.db.rollback()
            error_msg = str(e.orig) if e.orig else str(e)
            if "slug" in error_msg or "uq_tenants_slug" in error_msg:
                return None, f"Slug '{request.slug}' is already taken"
            if "owner_email" in error_msg:
                return None, f"Owner email '{request.owner_email}' already exists"
            if "tenant_phone" in error_msg or "idx_users_tenant_phone" in error_msg:
                return None, f"Phone '{request.admin_phone}' already registered"
            return None, f"Provisioning failed: {error_msg}"

        except Exception as e:
            self.db.rollback()
            return None, f"Unexpected error during provisioning: {str(e)}"

    # ─── Get Tenant ────────────────────────────────────────────────

    def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID (excludes soft-deleted)."""
        return (
            self.db.query(Tenant)
            .filter(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
            .first()
        )

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug (excludes soft-deleted)."""
        return (
            self.db.query(Tenant)
            .filter(Tenant.slug == slug, Tenant.deleted_at.is_(None))
            .first()
        )

    # ─── List Tenants ──────────────────────────────────────────────

    def list_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Tenant], int]:
        """
        List all tenants with optional status filter.
        Returns (tenants_list, total_count).
        """
        query = self.db.query(Tenant).filter(Tenant.deleted_at.is_(None))

        if status_filter:
            query = query.filter(Tenant.status == status_filter)

        total = query.count()
        tenants = (
            query
            .order_by(Tenant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return tenants, total

    # ─── Update Tenant ─────────────────────────────────────────────

    def update_tenant(
        self, tenant_id: int, request: UpdateTenantRequest
    ) -> Tuple[Optional[Tenant], Optional[str]]:
        """Update tenant details."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None, "Tenant not found"

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(tenant, field, value)

        try:
            self.db.commit()
            self.db.refresh(tenant)
            return tenant, None
        except IntegrityError as e:
            self.db.rollback()
            return None, f"Update failed: {str(e.orig)}"

    # ─── Activate / Suspend / Cancel ───────────────────────────────

    def activate_tenant(self, tenant_id: int) -> Tuple[Optional[Tenant], Optional[str]]:
        """Activate a tenant — makes their website live."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None, "Tenant not found"

        tenant.status = "active"
        self.db.commit()
        self.db.refresh(tenant)
        return tenant, None

    def suspend_tenant(self, tenant_id: int) -> Tuple[Optional[Tenant], Optional[str]]:
        """Suspend a tenant — disables their website."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None, "Tenant not found"

        tenant.status = "suspended"
        self.db.commit()
        self.db.refresh(tenant)
        return tenant, None

    def cancel_tenant(self, tenant_id: int) -> Tuple[Optional[Tenant], Optional[str]]:
        """Cancel a tenant subscription — soft deletes after cancellation."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None, "Tenant not found"

        tenant.status = "cancelled"
        self.db.commit()
        self.db.refresh(tenant)
        return tenant, None

    # ─── Delete Tenant (Soft) ──────────────────────────────────────

    def delete_tenant(self, tenant_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a tenant and all associated data."""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        now = datetime.utcnow()
        tenant.deleted_at = now

        # Also soft-delete associated restaurant
        restaurant = (
            self.db.query(Restaurant)
            .filter(Restaurant.tenant_id == tenant_id, Restaurant.deleted_at.is_(None))
            .first()
        )
        if restaurant:
            restaurant.deleted_at = now

        self.db.commit()
        return True, None
