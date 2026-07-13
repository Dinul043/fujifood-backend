"""
Base model for all FujiFood database tables.

Every table gets:
  id          - Auto-increment primary key
  tenant_id   - Multi-tenancy isolation (NULL for platform-level tables)
  created_at  - Record creation timestamp
  updated_at  - Last modification timestamp
  deleted_at  - Soft delete timestamp (NULL = active)
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declared_attr
from app.core.database import Base


class TimestampMixin:
    """Adds created_at and updated_at to any model."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Adds soft delete support. deleted_at=NULL means active."""
    deleted_at = Column(DateTime, nullable=True, default=None)


class TenantMixin:
    """Adds tenant_id for multi-tenancy row-level isolation."""
    tenant_id = Column(Integer, nullable=True, index=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base for all platform-level tables (not tenant-scoped).
    Example: tenants, subscriptions, admin_users
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)


class TenantBaseModel(Base, TimestampMixin, SoftDeleteMixin, TenantMixin):
    """
    Abstract base for all tenant-scoped tables.
    Example: restaurants, menus, orders, customers

    All queries MUST filter by tenant_id.
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
