"""
Tenant model — represents one restaurant SaaS account on FujiFood.

One tenant = one restaurant business.
A tenant can have one or more branches (future).
"""
import enum
from sqlalchemy import Column, String, Enum, Boolean, Text
from app.models.base import BaseModel


class TenantStatus(str, enum.Enum):
    PENDING   = "pending"    # Application submitted, awaiting admin review
    APPROVED  = "approved"   # Approved but subscription not yet active
    ACTIVE    = "active"     # Subscription active — restaurant is live
    SUSPENDED = "suspended"  # Payment failed or manually suspended
    CANCELLED = "cancelled"  # Subscription cancelled


class TenantPlan(str, enum.Enum):
    TRIAL        = "trial"
    STARTER      = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE   = "enterprise"


class Tenant(BaseModel):
    """
    Core SaaS account table. Created when admin approves a restaurant application.
    """
    __tablename__ = "tenants"

    # Identity
    name             = Column(String(200), nullable=False)               # "A2B Restaurant"
    slug             = Column(String(100), nullable=False, unique=True)  # "a2b" → a2b.fujifood.com
    custom_domain    = Column(String(255), nullable=True, unique=True)   # "order.a2b.com"

    # Status
    status           = Column(Enum(TenantStatus), default=TenantStatus.PENDING, nullable=False, index=True)

    # Subscription
    plan             = Column(Enum(TenantPlan), default=TenantPlan.TRIAL, nullable=False)
    trial_ends_at    = Column(String(50), nullable=True)   # ISO datetime string
    subscription_ends_at = Column(String(50), nullable=True)

    # Owner contact (for admin reference)
    owner_name       = Column(String(200), nullable=False)
    owner_email      = Column(String(255), nullable=False, unique=True, index=True)
    owner_phone      = Column(String(20), nullable=True)

    # Flags
    is_verified      = Column(Boolean, default=False, nullable=False)
    email_verified   = Column(Boolean, default=False, nullable=False)

    # Metadata
    onboarding_notes = Column(Text, nullable=True)  # Admin notes during review

    def __repr__(self):
        return f"<Tenant id={self.id} slug={self.slug} status={self.status}>"
