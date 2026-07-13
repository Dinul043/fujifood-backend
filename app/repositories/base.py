"""
Base Repository — generic CRUD operations with automatic tenant isolation.

Every repository inherits from one of:
  - BaseRepository      (for platform-level tables: tenants, admin_users)
  - TenantRepository    (for tenant-scoped tables: restaurants, menus, orders)

Tenant isolation is automatic — no query ever leaks across tenants.
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.models.base import BaseModel, TenantBaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
TenantModelType = TypeVar("TenantModelType", bound=TenantBaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for platform-level models (no tenant scoping).
    Example: tenants, admin_users, subscriptions
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return (
            self.db.query(self.model)
            .filter(self.model.id == id, self.model.deleted_at.is_(None))
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 50) -> List[ModelType]:
        return (
            self.db.query(self.model)
            .filter(self.model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def soft_delete(self, obj: ModelType) -> ModelType:
        from datetime import datetime
        obj.deleted_at = datetime.utcnow()
        self.db.commit()
        return obj

    def hard_delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()


class TenantRepository(Generic[TenantModelType]):
    """
    Generic repository for tenant-scoped models.
    ALL queries are automatically scoped to tenant_id.

    Example: restaurants, menu_categories, menu_items, orders, customers

    IMPORTANT: Never call this without a valid tenant_id.
    """

    def __init__(self, model: Type[TenantModelType], db: Session, tenant_id: int):
        self.model = model
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """All queries start here — tenant_id + soft delete filter applied."""
        return (
            self.db.query(self.model)
            .filter(
                self.model.tenant_id == self.tenant_id,
                self.model.deleted_at.is_(None),
            )
        )

    def get_by_id(self, id: int) -> Optional[TenantModelType]:
        return self._base_query().filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[TenantModelType]:
        return self._base_query().offset(skip).limit(limit).all()

    def create(self, obj: TenantModelType) -> TenantModelType:
        obj.tenant_id = self.tenant_id
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: TenantModelType) -> TenantModelType:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def soft_delete(self, obj: TenantModelType) -> TenantModelType:
        from datetime import datetime
        obj.deleted_at = datetime.utcnow()
        self.db.commit()
        return obj
