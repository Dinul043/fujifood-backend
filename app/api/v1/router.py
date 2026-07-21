"""
API v1 Router — aggregates all route modules.
"""
from fastapi import APIRouter
from app.api.v1.routes import auth, tenants, themes, restaurants, menu, orders
from app.api.v1.routes import payment, geocode, staff, reviews, cart, addresses

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Tenant provisioning (internal)
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants (Internal)"])

# Theme engine
api_router.include_router(themes.router, prefix="/themes", tags=["Theme Engine"])

# Restaurant management
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])

# Menu management
api_router.include_router(menu.router, prefix="/menu", tags=["Menu"])

# Order management
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])

# Payment (Razorpay)
api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])

# Geolocation
api_router.include_router(geocode.router, prefix="/geo", tags=["Geolocation"])

# Staff management (owner only)
api_router.include_router(staff.router, prefix="/staff", tags=["Staff Management"])

# Reviews
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

# Cart
api_router.include_router(cart.router, prefix="/cart", tags=["Cart"])

# Addresses
api_router.include_router(addresses.router, prefix="/addresses", tags=["Addresses"])


@api_router.get("/ping", tags=["Health"])
async def ping():
    return {"message": "FujiFood API v1 — Online"}
