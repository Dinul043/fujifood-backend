"""
Theme Service — Business logic for the Theme Configuration Engine.

Handles:
  - Get theme for a tenant (used by storefront to render CSS variables)
  - Update theme configuration (used by restaurant admin)
  - Apply theme presets (pre-defined configurations)

The theme drives ALL visual aspects of the storefront:
  - Colors, fonts, layout, card styles, hero configuration
  - Changes take effect immediately — no redeployment needed
"""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.theme import Theme
from app.schemas.theme import UpdateThemeRequest


# ═══════════════════════════════════════════════════
#  Theme Presets — Professional configurations
# ═══════════════════════════════════════════════════

THEME_PRESETS = {
    "luxury": {
        "font_heading": "Playfair Display",
        "font_body": "Lora",
        "color_primary": "#B8860B",
        "color_secondary": "#0A0A0A",
        "color_accent": "#D4AF37",
        "color_bg": "#0D0D0D",
        "color_surface": "#1A1A1A",
        "color_text": "#F5F5F5",
        "hero_layout": "full",
        "header_style": "transparent",
        "card_style": "elevated",
    },
    "traditional": {
        "font_heading": "Merriweather",
        "font_body": "Source Sans Pro",
        "color_primary": "#8B4513",
        "color_secondary": "#2C1810",
        "color_accent": "#DAA520",
        "color_bg": "#FFF8F0",
        "color_surface": "#FFFFFF",
        "color_text": "#2C1810",
        "hero_layout": "split",
        "header_style": "solid",
        "card_style": "rounded",
    },
    "cafe": {
        "font_heading": "Poppins",
        "font_body": "Nunito",
        "color_primary": "#6B4E37",
        "color_secondary": "#3C2415",
        "color_accent": "#E8A87C",
        "color_bg": "#F9F5F0",
        "color_surface": "#FFFFFF",
        "color_text": "#3C2415",
        "hero_layout": "centered",
        "header_style": "glass",
        "card_style": "rounded",
    },
    "modern": {
        "font_heading": "Plus Jakarta Sans",
        "font_body": "Inter",
        "color_primary": "#E85D8E",
        "color_secondary": "#18181B",
        "color_accent": "#F59E0B",
        "color_bg": "#FAFAFA",
        "color_surface": "#FFFFFF",
        "color_text": "#18181B",
        "hero_layout": "split",
        "header_style": "glass",
        "card_style": "rounded",
    },
    "minimal": {
        "font_heading": "DM Sans",
        "font_body": "DM Sans",
        "color_primary": "#111111",
        "color_secondary": "#333333",
        "color_accent": "#FF4500",
        "color_bg": "#FFFFFF",
        "color_surface": "#F8F8F8",
        "color_text": "#111111",
        "hero_layout": "minimal",
        "header_style": "minimal",
        "card_style": "flat",
    },
}


class ThemeService:
    """Theme configuration business logic."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Get Theme ─────────────────────────────────────────────────

    def get_theme_by_tenant_id(self, tenant_id: int) -> Optional[Theme]:
        """Get theme configuration for a tenant."""
        return (
            self.db.query(Theme)
            .filter(
                Theme.tenant_id == tenant_id,
                Theme.deleted_at.is_(None),
            )
            .first()
        )

    def get_theme_by_slug(self, slug: str) -> Optional[Theme]:
        """
        Get theme by tenant slug — used by storefront.
        Resolves tenant from slug, then returns their theme.
        """
        from app.models.tenant import Tenant, TenantStatus

        tenant = (
            self.db.query(Tenant)
            .filter(
                Tenant.slug == slug,
                Tenant.status == "active",
                Tenant.deleted_at.is_(None),
            )
            .first()
        )

        if not tenant:
            return None

        return self.get_theme_by_tenant_id(tenant.id)

    # ─── Update Theme ──────────────────────────────────────────────

    def update_theme(
        self, tenant_id: int, request: UpdateThemeRequest
    ) -> Tuple[Optional[Theme], Optional[str]]:
        """
        Update theme configuration for a tenant.
        Only provided fields are updated (partial update).
        """
        theme = self.get_theme_by_tenant_id(tenant_id)
        if not theme:
            return None, "Theme not found for this tenant"

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(theme, field, value)

        self.db.commit()
        self.db.refresh(theme)
        return theme, None

    # ─── Apply Preset ──────────────────────────────────────────────

    def apply_preset(
        self, tenant_id: int, preset_name: str
    ) -> Tuple[Optional[Theme], Optional[str]]:
        """
        Apply a pre-defined theme preset to a tenant.
        Overwrites all theme fields with the preset values.
        """
        if preset_name not in THEME_PRESETS:
            return None, f"Unknown preset: {preset_name}"

        theme = self.get_theme_by_tenant_id(tenant_id)
        if not theme:
            return None, "Theme not found for this tenant"

        preset = THEME_PRESETS[preset_name]
        for field, value in preset.items():
            setattr(theme, field, value)

        self.db.commit()
        self.db.refresh(theme)
        return theme, None

    # ─── List Available Presets ────────────────────────────────────

    @staticmethod
    def list_presets() -> dict:
        """Return all available theme presets with their configurations."""
        return THEME_PRESETS
