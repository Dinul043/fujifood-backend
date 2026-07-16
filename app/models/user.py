"""
User model — single unified users table.

Supports two roles in Phase 1:
  - customer          : OTP login, places orders
  - restaurant_admin  : Phone + password, manages restaurant

Future roles (architecture-ready, not implemented in Phase 1):
  - restaurant_staff  : Limited management access
  - platform_admin    : FujiFood internal team

All users belong to a tenant.
Customers are scoped to ONE tenant — a customer of A2B cannot order from Geetham.
"""
import enum
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import TenantBaseModel


class UserRole(str, enum.Enum):
    CUSTOMER          = "customer"
    RESTAURANT_ADMIN  = "restaurant_admin"
    # Future — do not implement in Phase 1:
    # RESTAURANT_STAFF = "restaurant_staff"
    # PLATFORM_ADMIN   = "platform_admin"


class UserStatus(str, enum.Enum):
    ACTIVE    = "active"
    SUSPENDED = "suspended"


class User(TenantBaseModel):
    """
    Single users table for all user types.
    Role determines access level and login method.
    """
    __tablename__ = "users"

    tenant_id     = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Identity
    name          = Column(String(200), nullable=True)   # Can be set after OTP login
    phone         = Column(String(20),  nullable=False)  # Primary identifier for all users
    email         = Column(String(255), nullable=True)   # Optional

    # Auth
    # password_hash is NULL for customers (OTP-only login)
    # password_hash is SET for restaurant_admin
    password_hash = Column(String(255), nullable=True)

    # Role and status
    role          = Column(String(30), nullable=False, default=UserRole.CUSTOMER, index=True)
    status        = Column(String(20), nullable=False, default=UserStatus.ACTIVE)

    # Flags
    phone_verified = Column(Boolean, default=False, nullable=False)
    is_active      = Column(Boolean, default=True, nullable=False)
    is_owner       = Column(Boolean, default=False, nullable=False)  # Owner vs staff admin

    # Relationships
    tenant = relationship("Tenant", backref="users", foreign_keys=[tenant_id])

    # Composite index: phone lookups per tenant (not unique — family can share phone)
    __table_args__ = (
        Index("idx_users_tenant_phone", "tenant_id", "phone", unique=False),
        Index("idx_users_tenant_role", "tenant_id", "role"),
    )

    def __repr__(self):
        return f"<User id={self.id} phone={self.phone} role={self.role} tenant={self.tenant_id}>"
