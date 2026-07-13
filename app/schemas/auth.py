"""
Auth Schemas — Request and Response DTOs for authentication.

Covers:
  - Restaurant admin login (phone + password)
  - Customer OTP flow (send OTP → verify OTP)
  - Token responses
  - Current user profile
"""
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════
#  Restaurant Admin — Login with phone + password
# ═══════════════════════════════════════════════════

class AdminLoginRequest(BaseModel):
    """Restaurant admin login — phone + password."""
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number with country code")
    password: str = Field(..., min_length=6, description="Account password")
    tenant_slug: str = Field(..., min_length=2, max_length=100, description="Restaurant tenant slug")


# ═══════════════════════════════════════════════════
#  Customer — OTP Flow
# ═══════════════════════════════════════════════════

class OTPSendRequest(BaseModel):
    """Request to send OTP to customer's phone."""
    phone: str = Field(..., min_length=10, max_length=15, description="Customer phone number")
    tenant_slug: str = Field(..., min_length=2, max_length=100, description="Restaurant tenant slug")


class OTPSendResponse(BaseModel):
    """Confirmation that OTP was sent."""
    success: bool = True
    message: str = "OTP sent successfully"
    phone: str
    expires_in_seconds: int = 300  # 5 minutes


class OTPVerifyRequest(BaseModel):
    """Verify OTP and authenticate customer."""
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=6, description="OTP code")
    tenant_slug: str = Field(..., min_length=2, max_length=100)


# ═══════════════════════════════════════════════════
#  Token Responses
# ═══════════════════════════════════════════════════

class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")
    user: "UserProfileResponse"


class RefreshTokenRequest(BaseModel):
    """Request to refresh an expired access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


# ═══════════════════════════════════════════════════
#  User Profile
# ═══════════════════════════════════════════════════

class UserProfileResponse(BaseModel):
    """Current authenticated user's profile."""
    id: int
    tenant_id: int
    name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    role: str  # "customer" | "restaurant_admin"
    status: str  # "active" | "suspended"

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════
#  Registration (Restaurant Admin — created by our team)
# ═══════════════════════════════════════════════════

class CreateRestaurantAdminRequest(BaseModel):
    """
    Internal API — used by our operations team to create a restaurant admin.
    NOT exposed publicly. Called after a restaurant is onboarded.
    """
    tenant_id: int = Field(..., description="Tenant this admin belongs to")
    name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)


# ═══════════════════════════════════════════════════
#  Generic Error Response
# ═══════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Standard error response structure."""
    success: bool = False
    message: str
    detail: Optional[str] = None


# Resolve forward references
TokenResponse.model_rebuild()
