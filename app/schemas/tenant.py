"""
Tenant Schemas — Request and Response DTOs for internal tenant provisioning.

This is NOT a public registration system.
These APIs are used exclusively by the FujiFood operations team
to provision new restaurant tenants after agreement and payment.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


# ═══════════════════════════════════════════════════
#  Tenant Provisioning — Full Onboarding Request
# ═══════════════════════════════════════════════════

class ProvisionTenantRequest(BaseModel):
    """
    Complete tenant provisioning request.
    Creates: Tenant + Restaurant + Theme + Restaurant Admin User
    in a single atomic operation.
    """

    # Tenant identity
    name: str = Field(..., min_length=2, max_length=200,
                      description="Restaurant business name")
    slug: str = Field(..., min_length=2, max_length=100,
                      description="URL slug (e.g. 'a2b' → a2b.fujifood.com)")
    custom_domain: Optional[str] = Field(None, max_length=255,
                                         description="Custom domain if applicable")
    plan: str = Field(default="trial",
                      description="Subscription plan: trial|starter|professional|enterprise")

    # Owner contact
    owner_name: str = Field(..., min_length=2, max_length=200)
    owner_email: str = Field(..., max_length=255)
    owner_phone: Optional[str] = Field(None, max_length=20)

    # Restaurant details
    restaurant_name: str = Field(..., min_length=2, max_length=200)
    restaurant_phone: str = Field(..., min_length=10, max_length=20)
    restaurant_email: str = Field(..., max_length=255)
    cuisine_type: Optional[str] = Field(None, max_length=200)
    address_line1: str = Field(..., min_length=5, max_length=300)
    address_line2: Optional[str] = Field(None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="India", max_length=50)

    # Restaurant admin credentials
    admin_name: str = Field(..., min_length=2, max_length=200,
                            description="Name of the restaurant admin user")
    admin_phone: str = Field(..., min_length=10, max_length=20,
                             description="Admin login phone number")
    admin_email: Optional[str] = Field(None, max_length=255)
    admin_password: str = Field(..., min_length=8, max_length=100,
                                description="Initial admin password")

    # Onboarding notes (internal)
    onboarding_notes: Optional[str] = Field(None,
                                            description="Internal notes about this onboarding")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "cannot start/end with hyphen"
            )
        return v

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        valid = {"trial", "starter", "professional", "enterprise"}
        if v not in valid:
            raise ValueError(f"Plan must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Tenant Update
# ═══════════════════════════════════════════════════

class UpdateTenantRequest(BaseModel):
    """Update tenant details — used by operations team."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    custom_domain: Optional[str] = Field(None, max_length=255)
    plan: Optional[str] = None
    status: Optional[str] = None
    owner_name: Optional[str] = Field(None, min_length=2, max_length=200)
    owner_email: Optional[str] = Field(None, max_length=255)
    owner_phone: Optional[str] = Field(None, max_length=20)
    onboarding_notes: Optional[str] = None

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"trial", "starter", "professional", "enterprise"}
        if v not in valid:
            raise ValueError(f"Plan must be one of: {', '.join(valid)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"pending", "approved", "active", "suspended", "cancelled"}
        if v not in valid:
            raise ValueError(f"Status must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Response DTOs
# ═══════════════════════════════════════════════════

class TenantResponse(BaseModel):
    """Tenant details returned to operations team."""
    id: int
    uuid: str
    name: str
    slug: str
    custom_domain: Optional[str] = None
    status: str
    plan: str
    owner_name: str
    owner_email: str
    owner_phone: Optional[str] = None
    is_verified: bool
    onboarding_notes: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RestaurantSummaryResponse(BaseModel):
    """Restaurant summary within tenant provisioning response."""
    id: int
    uuid: str
    name: str
    city: str
    is_online: bool
    is_published: bool

    class Config:
        from_attributes = True


class ProvisionTenantResponse(BaseModel):
    """Response after successful tenant provisioning."""
    success: bool = True
    message: str = "Tenant provisioned successfully"
    tenant: TenantResponse
    restaurant: RestaurantSummaryResponse
    admin_user_id: int
    admin_phone: str
    storefront_url: str


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    tenants: List[TenantResponse]
    total: int
    page: int
    page_size: int
