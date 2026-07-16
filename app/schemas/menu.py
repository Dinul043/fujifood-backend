"""
Menu Schemas — Request and Response DTOs for menu management.

Covers:
  - Menu categories (CRUD)
  - Menu items (CRUD)
  - Public menu browsing (storefront)
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════
#  Menu Category
# ═══════════════════════════════════════════════════

class CreateCategoryRequest(BaseModel):
    """Create a new menu category."""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class UpdateCategoryRequest(BaseModel):
    """Update an existing menu category."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Menu category response."""
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class CategoryWithItemsResponse(BaseModel):
    """Category with nested menu items — used for storefront."""
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int
    items: List["MenuItemResponse"] = []

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════
#  Menu Item
# ═══════════════════════════════════════════════════

class CreateMenuItemRequest(BaseModel):
    """Create a new menu item."""
    category_id: int = Field(..., description="ID of the category this item belongs to")
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = Field(None, ge=0)
    food_type: str = Field(default="veg")
    is_bestseller: bool = False
    is_recommended: bool = False
    is_spicy: bool = False
    is_available: bool = True
    sort_order: int = Field(default=0, ge=0)
    calories: Optional[int] = Field(None, ge=0)
    allergens: Optional[str] = Field(None, max_length=500)
    tags: Optional[str] = Field(None, max_length=500)

    @field_validator("food_type")
    @classmethod
    def validate_food_type(cls, v: str) -> str:
        valid = {"veg", "non_veg", "egg"}
        if v not in valid:
            raise ValueError(f"food_type must be one of: {', '.join(valid)}")
        return v

    @field_validator("discount_price")
    @classmethod
    def validate_discount(cls, v, info):
        if v is not None and "price" in info.data and v >= info.data["price"]:
            raise ValueError("discount_price must be less than price")
        return v


class UpdateMenuItemRequest(BaseModel):
    """Update an existing menu item."""
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    discount_price: Optional[float] = Field(None, ge=0)
    food_type: Optional[str] = None
    is_bestseller: Optional[bool] = None
    is_recommended: Optional[bool] = None
    is_spicy: Optional[bool] = None
    is_available: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    calories: Optional[int] = Field(None, ge=0)
    allergens: Optional[str] = Field(None, max_length=500)
    tags: Optional[str] = Field(None, max_length=500)

    @field_validator("food_type")
    @classmethod
    def validate_food_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"veg", "non_veg", "egg"}
        if v not in valid:
            raise ValueError(f"food_type must be one of: {', '.join(valid)}")
        return v


class MenuItemResponse(BaseModel):
    """Menu item response."""
    id: int
    uuid: str
    category_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    food_type: str
    is_bestseller: bool
    is_recommended: bool
    is_spicy: bool
    is_available: bool
    sort_order: int
    avg_rating: float = 0.0
    rating_count: int = 0
    calories: Optional[int] = None
    allergens: Optional[str] = None
    tags: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════
#  Full Menu Response (Storefront)
# ═══════════════════════════════════════════════════

class FullMenuResponse(BaseModel):
    """Complete menu — categories with nested items for storefront."""
    restaurant_name: str
    categories: List[CategoryWithItemsResponse]
    total_items: int


# Rebuild forward refs
CategoryWithItemsResponse.model_rebuild()
