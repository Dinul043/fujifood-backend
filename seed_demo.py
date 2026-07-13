"""
Seed demo tenant for development.
Run: py seed_demo.py
"""
import sys
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.services.tenant_service import TenantService
from app.schemas.tenant import ProvisionTenantRequest
from app.services.menu_service import MenuService
from app.schemas.menu import CreateCategoryRequest, CreateMenuItemRequest

db = SessionLocal()

# ─── Provision Tenant ──────────────────────────────────────────────
service = TenantService(db)

request = ProvisionTenantRequest(
    name="A2B Veg Restaurant",
    slug="a2b",
    plan="professional",
    owner_name="Rajesh Kumar",
    owner_email="rajesh@a2b.com",
    owner_phone="+919876543210",
    restaurant_name="A2B Veg Restaurant",
    restaurant_phone="+919876543210",
    restaurant_email="hello@a2b.com",
    cuisine_type="South Indian, North Indian, Chinese",
    address_line1="123, Marina Beach Road",
    address_line2="Anna Nagar",
    city="Chennai",
    state="Tamil Nadu",
    pincode="600001",
    country="India",
    admin_name="Rajesh Kumar",
    admin_phone="9876543210",
    admin_email="rajesh@a2b.com",
    admin_password="Admin@123",
    onboarding_notes="Demo tenant for development",
)

result, error = service.provision_tenant(request)
if error:
    print(f"Error: {error}")
    db.close()
    sys.exit(1)

tenant = result["tenant"]
print(f"Tenant provisioned: {tenant.name} (ID: {tenant.id})")
print(f"Admin login: phone=9876543210, password=Admin@123")

# ─── Seed Menu Categories ──────────────────────────────────────────
menu_service = MenuService(db, tenant.id)

categories_data = [
    ("South Indian", "Authentic dosas, idlis, and more", 1),
    ("North Indian", "Rich curries and breads", 2),
    ("Chinese", "Indo-Chinese favorites", 3),
    ("Beverages", "Fresh juices and hot drinks", 4),
    ("Sweets", "Traditional Indian desserts", 5),
]

categories = {}
for name, desc, order in categories_data:
    cat, err = menu_service.create_category(
        CreateCategoryRequest(name=name, description=desc, sort_order=order)
    )
    if cat:
        categories[name] = cat
        print(f"  Category: {name} (ID: {cat.id})")

# ─── Seed Menu Items ──────────────────────────────────────────────
items_data = [
    # South Indian
    ("Ghee Roast Dosa", categories["South Indian"].id, 120, "veg", True, True, False),
    ("Masala Dosa", categories["South Indian"].id, 110, "veg", False, True, False),
    ("Mini Tiffin Combo", categories["South Indian"].id, 99, "veg", True, False, False),
    ("Idli Sambar (4 pcs)", categories["South Indian"].id, 70, "veg", False, False, False),
    ("Rava Dosa", categories["South Indian"].id, 100, "veg", False, False, False),
    ("Pongal", categories["South Indian"].id, 80, "veg", False, True, False),
    # North Indian
    ("Paneer Butter Masala", categories["North Indian"].id, 160, "veg", True, True, True),
    ("Dal Makhani", categories["North Indian"].id, 140, "veg", False, True, False),
    ("Butter Naan", categories["North Indian"].id, 40, "veg", False, False, False),
    ("Veg Biryani", categories["North Indian"].id, 150, "veg", True, False, True),
    ("Chole Bhature", categories["North Indian"].id, 130, "veg", False, False, False),
    # Chinese
    ("Veg Fried Rice", categories["Chinese"].id, 120, "veg", False, True, False),
    ("Gobi Manchurian", categories["Chinese"].id, 130, "veg", True, False, True),
    ("Veg Noodles", categories["Chinese"].id, 110, "veg", False, False, False),
    ("Spring Rolls (4 pcs)", categories["Chinese"].id, 90, "veg", False, False, False),
    # Beverages
    ("Filter Coffee", categories["Beverages"].id, 50, "veg", False, True, False),
    ("Mango Lassi", categories["Beverages"].id, 70, "veg", False, False, False),
    ("Fresh Lime Soda", categories["Beverages"].id, 45, "veg", False, False, False),
    # Sweets
    ("Rava Kesari", categories["Sweets"].id, 80, "veg", True, True, False),
    ("Gulab Jamun (2 pcs)", categories["Sweets"].id, 60, "veg", False, False, False),
]

for name, cat_id, price, food_type, bestseller, recommended, spicy in items_data:
    item, err = menu_service.create_item(
        CreateMenuItemRequest(
            category_id=cat_id,
            name=name,
            price=price,
            food_type=food_type,
            is_bestseller=bestseller,
            is_recommended=recommended,
            is_spicy=spicy,
        )
    )
    if item:
        print(f"    Item: {name} - Rs.{price}")

# ─── Update restaurant to online + published ──────────────────────
from app.models.restaurant import Restaurant
restaurant = db.query(Restaurant).filter(Restaurant.tenant_id == tenant.id).first()
restaurant.is_online = True
restaurant.is_published = True
restaurant.delivery_radius_km = 8.0
restaurant.delivery_fee = 30.0
restaurant.min_order_amount = 99.0
restaurant.free_delivery_above = 299.0
restaurant.avg_delivery_time_mins = 35
db.commit()

print("\nDone! Restaurant is live.")
print(f"Storefront: https://a2b.fujifood.com (dev: http://localhost:3001)")
print(f"Admin login: phone=9876543210, password=Admin@123")
db.close()
