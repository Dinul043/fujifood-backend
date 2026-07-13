"""
Menu models — MenuCategory and MenuItem.

Structure:
  Restaurant
    └── MenuCategory  (e.g. "Starters", "Mains", "Beverages")
          └── MenuItem  (e.g. "Chicken Biryani", "Masala Dosa")
"""
import enum
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TenantBaseModel


class FoodType(str, enum.Enum):
    VEG      = "veg"       # Pure vegetarian
    NON_VEG  = "non_veg"   # Non-vegetarian
    EGG      = "egg"       # Contains egg


class MenuCategory(TenantBaseModel):
    """
    Groups menu items into sections.
    Example: Starters, Mains, Biryani, Desserts, Beverages
    """
    __tablename__ = "menu_categories"

    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    restaurant_id   = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)

    name            = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    image_url       = Column(String(500), nullable=True)
    sort_order      = Column(Integer, default=0, nullable=False)  # Display order
    is_active       = Column(Boolean, default=True, nullable=False)

    # Relationships
    items = relationship("MenuItem", back_populates="category", lazy="select")

    def __repr__(self):
        return f"<MenuCategory id={self.id} name={self.name}>"


class MenuItem(TenantBaseModel):
    """
    A single dish or product in the restaurant menu.
    """
    __tablename__ = "menu_items"

    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    restaurant_id   = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    category_id     = Column(Integer, ForeignKey("menu_categories.id"), nullable=False, index=True)

    # Basic info
    name            = Column(String(300), nullable=False)
    description     = Column(Text, nullable=True)
    image_url       = Column(String(500), nullable=True)

    # Pricing
    price           = Column(Float, nullable=False)
    discount_price  = Column(Float, nullable=True)   # Strike-through price if on offer

    # Classification
    food_type       = Column(
                        String(20),
                        nullable=False,
                        default=FoodType.VEG
                      )
    is_bestseller   = Column(Boolean, default=False, nullable=False)
    is_recommended  = Column(Boolean, default=False, nullable=False)
    is_spicy        = Column(Boolean, default=False, nullable=False)

    # Availability
    is_available    = Column(Boolean, default=True, nullable=False)
    sort_order      = Column(Integer, default=0, nullable=False)

    # Nutritional info (optional)
    calories        = Column(Integer, nullable=True)
    allergens       = Column(String(500), nullable=True)  # Comma-separated

    # SEO / Search tags
    tags            = Column(String(500), nullable=True)  # e.g. "biryani,rice,spicy"

    # Relationships
    category = relationship("MenuCategory", back_populates="items")

    def __repr__(self):
        return f"<MenuItem id={self.id} name={self.name} price={self.price}>"
