"""
Theme Routes — Theme Configuration Engine API.

Two access patterns:
  1. Public (storefront):  GET /themes/storefront/{slug}
     → Returns theme config for a restaurant's frontend to render
  2. Admin (restaurant):   GET/PATCH /themes/manage
     → Restaurant admin updates their own theme

Endpoints:
  GET    /themes/storefront/{slug}   → Public theme for storefront rendering
  GET    /themes/manage              → Get current tenant's theme (auth required)
  PATCH  /themes/manage              → Update theme (auth required)
  POST   /themes/manage/preset       → Apply a preset (auth required)
  GET    /themes/presets             → List available presets
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.theme import (
    UpdateThemeRequest,
    ApplyThemePresetRequest,
    ThemeResponse,
)
from app.schemas.auth import ErrorResponse
from app.services.theme_service import ThemeService, THEME_PRESETS

router = APIRouter()


# ─── Public: Storefront Theme ──────────────────────────────────────

@router.get(
    "/storefront/{slug}",
    response_model=ThemeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get storefront theme by restaurant slug",
    description=(
        "Public endpoint — returns the theme configuration for a restaurant's "
        "storefront. Used by the frontend to inject CSS variables at runtime."
    ),
)
async def get_storefront_theme(slug: str, db: Session = Depends(get_db)):
    service = ThemeService(db)
    theme = service.get_theme_by_slug(slug)

    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found or inactive",
        )

    return ThemeResponse.model_validate(theme)


# ─── Admin: Get Own Theme ──────────────────────────────────────────

@router.get(
    "/manage",
    response_model=ThemeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get current restaurant theme",
    description="Returns the theme configuration for the authenticated admin's restaurant.",
)
async def get_own_theme(
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = ThemeService(db)
    theme = service.get_theme_by_tenant_id(current_user.tenant_id)

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not configured")

    return ThemeResponse.model_validate(theme)


# ─── Admin: Update Theme ───────────────────────────────────────────

@router.patch(
    "/manage",
    response_model=ThemeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update restaurant theme",
    description=(
        "Partial update — only provided fields are changed. "
        "Changes take effect immediately on the storefront."
    ),
)
async def update_theme(
    request: UpdateThemeRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = ThemeService(db)
    theme, error = service.update_theme(current_user.tenant_id, request)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return ThemeResponse.model_validate(theme)


# ─── Admin: Apply Preset ───────────────────────────────────────────

@router.post(
    "/manage/preset",
    response_model=ThemeResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Apply a theme preset",
    description="Applies a pre-defined theme configuration. Overwrites current theme.",
)
async def apply_preset(
    request: ApplyThemePresetRequest,
    current_user: User = Depends(require_role("restaurant_admin")),
    db: Session = Depends(get_db),
):
    service = ThemeService(db)
    theme, error = service.apply_preset(current_user.tenant_id, request.preset_name)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return ThemeResponse.model_validate(theme)


# ─── Public: List Presets ──────────────────────────────────────────

@router.get(
    "/presets",
    summary="List available theme presets",
    description="Returns all pre-defined theme presets with their configurations.",
)
async def list_presets():
    return {
        "presets": [
            {"name": name, "config": config}
            for name, config in THEME_PRESETS.items()
        ]
    }
