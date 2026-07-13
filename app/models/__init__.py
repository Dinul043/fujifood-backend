"""
FujiFood Models — Central model registry.

All models are imported here so Alembic and the application
can discover them from a single import point.
"""
from app.models.base import Base, BaseModel, TenantBaseModel
from app.models.tenant import Tenant, TenantStatus, TenantPlan
from app.models.user import User, UserRole, UserStatus
from app.models.restaurant import Restaurant
from app.models.menu import MenuCategory, MenuItem, FoodType
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.models.theme import Theme

__all__ = [
    "Base",
    "BaseModel",
    "TenantBaseModel",
    "Tenant",
    "TenantStatus",
    "TenantPlan",
    "User",
    "UserRole",
    "UserStatus",
    "Restaurant",
    "MenuCategory",
    "MenuItem",
    "FoodType",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentMethod",
    "PaymentStatus",
    "Theme",
]
