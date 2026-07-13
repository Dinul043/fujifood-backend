"""
Theme Schemas — Request and Response DTOs for the Theme Engine.

The theme engine allows each restaurant to fully customize their
storefront appearance without any code changes or redeployment.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
import re


# ═══════════════════════════════════════════════════
#  Theme Configuration Request
# ═══════════════════════════════════════════════════

class UpdateThemeRequest(BaseModel):
    """Update theme configuration for a tenant."""

    # Typography
    font_heading: Optional[str] = Field(None, max_length=100)
    font_body: Optional[str] = Field(None, max_length=100)

    # Colors
    color_primary: Optional[str] = Field(None, max_length=20)
    color_secondary: Optional[str] = Field(None, max_length=20)
    color_accent: Optional[str] = Field(None, max_length=20)
    color_bg: Optional[str] = Field(None, max_length=20)
    color_surface: Optional[str] = Field(None, max_length=20)
    color_text: Optional[str] = Field(None, max_length=20)

    # Layout
    hero_layout: Optional[str] = Field(None, max_length=50)
    header_style: Optional[str] = Field(None, max_length=50)
    card_style: Optional[str] = Field(None, max_length=50)

    # Media
    hero_image_url: Optional[str] = Field(None, max_length=500)
    hero_video_url: Optional[str] = Field(None, max_length=500)

    # Custom
    custom_css: Optional[str] = None
    advanced_config: Optional[Dict[str, Any]] = None
    is_published: Optional[bool] = None

    @field_validator(
        "color_primary", "color_secondary", "color_accent",
        "color_bg", "color_surface", "color_text",
    )
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$", v):
            raise ValueError("Must be a valid hex color (e.g. #FF5733 or #fff)")
        return v.upper()

    @field_validator("hero_layout")
    @classmethod
    def validate_hero_layout(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"split", "full", "centered", "minimal", "video"}
        if v not in valid:
            raise ValueError(f"hero_layout must be one of: {', '.join(valid)}")
        return v

    @field_validator("header_style")
    @classmethod
    def validate_header_style(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"glass", "solid", "minimal", "transparent"}
        if v not in valid:
            raise ValueError(f"header_style must be one of: {', '.join(valid)}")
        return v

    @field_validator("card_style")
    @classmethod
    def validate_card_style(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {"rounded", "flat", "elevated", "bordered"}
        if v not in valid:
            raise ValueError(f"card_style must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Apply Theme Preset
# ═══════════════════════════════════════════════════

class ApplyThemePresetRequest(BaseModel):
    """Apply a pre-defined theme preset to a tenant."""
    preset_name: str = Field(..., description="Preset name: luxury|traditional|cafe|modern|minimal")

    @field_validator("preset_name")
    @classmethod
    def validate_preset(cls, v: str) -> str:
        valid = {"luxury", "traditional", "cafe", "modern", "minimal"}
        if v not in valid:
            raise ValueError(f"Preset must be one of: {', '.join(valid)}")
        return v


# ═══════════════════════════════════════════════════
#  Theme Response
# ═══════════════════════════════════════════════════

class ThemeResponse(BaseModel):
    """Full theme configuration returned to frontend."""
    id: int
    tenant_id: int
    font_heading: str
    font_body: str
    color_primary: str
    color_secondary: str
    color_accent: str
    color_bg: str
    color_surface: str
    color_text: str
    hero_layout: str
    header_style: str
    card_style: str
    hero_image_url: Optional[str] = None
    hero_video_url: Optional[str] = None
    custom_css: Optional[str] = None
    advanced_config: Optional[Dict[str, Any]] = None
    is_published: bool

    class Config:
        from_attributes = True
