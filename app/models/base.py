"""
Base models — Enterprise-grade foundation for all database tables.

Every table gets:
  id            — Auto-increment internal PK
  uuid          — Public-facing unique identifier (never expose sequential IDs)
  created_at    — Record creation timestamp (IST)
  updated_at    — Last modification timestamp (IST)
  deleted_at    — Soft delete (NULL = active)
  created_by    — Who created this record (user ID)
  updated_by    — Who last modified (user ID)

Tenant-scoped tables additionally get:
  tenant_id     — Multi-tenancy row-level isolation
"""
import uuid as uuid_lib
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import CHAR
from app.core.database import Base

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid_lib.uuid4())


def now_ist() -> datetime:
    """Get current time in IST."""
    return datetime.now(IST).replace(tzinfo=None)  # Store without tz info for MySQL


class TimestampMixin:
    """Audit timestamps on every record (IST)."""
    created_at = Column(DateTime, default=now_ist, nullable=False)
    updated_at = Column(DateTime, default=now_ist, onupdate=now_ist, nullable=False)


class SoftDeleteMixin:
    """Soft delete — deleted_at=NULL means active."""
    deleted_at = Column(DateTime, nullable=True, default=None, index=True)


class AuditMixin:
    """Track who created/modified records."""
    created_by = Column(Integer, nullable=True)  # user.id who created
    updated_by = Column(Integer, nullable=True)  # user.id who last modified


class TenantMixin:
    """Row-level tenant isolation."""
    tenant_id = Column(Integer, nullable=False, index=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Abstract base for platform-level tables (not tenant-scoped).
    Example: tenants, platform_settings
    """
    __abstract__ = True

    id   = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(CHAR(36), default=generate_uuid, unique=True, nullable=False, index=True)


class TenantBaseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin, TenantMixin):
    """
    Abstract base for tenant-scoped tables.
    Example: restaurants, menus, orders, customers

    All queries MUST filter by tenant_id.
    """
    __abstract__ = True

    id   = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(CHAR(36), default=generate_uuid, unique=True, nullable=False, index=True)
