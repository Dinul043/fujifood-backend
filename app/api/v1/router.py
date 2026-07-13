from fastapi import APIRouter
# Routes will be added here as each module is built

api_router = APIRouter()

# Phase 1: Auth + Tenant foundation
# from app.api.v1.routes import auth, tenants, admin
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])

# Placeholder health
@api_router.get("/ping")
async def ping():
    return {"message": "FujiFood API v1 — Online"}
